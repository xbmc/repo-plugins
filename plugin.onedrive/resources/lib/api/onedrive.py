'''
    OneDrive for Kodi
    Copyright (C) 2015 - Carlos Guzman

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

    Created on Mar 1, 2015
    @author: Carlos Guzman (cguZZman) carlosguzmang@hotmail.com
'''

import urllib
import urllib2
import json
import re
from resources.lib.api import utils
import xbmc
import xbmcgui
import xbmcaddon
import time
import ssl
import traceback

try:
    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context
except:
    None

class OneDrive:
    _login_url = 'https://login.live.com/oauth20_token.srf'
    _redirect_uri = 'https://login.live.com/oauth20_desktop.srf'
    _api_url = 'https://api.onedrive.com/v1.0'
    _signin_url = 'http://onedrive.daro.mx/service.jsp'
    exporting_count = 0
    exporting_target = 0
    exporting_percent = 0
    retry_target = 2
    
    def __init__(self, client_id):
        self.retry_times = 0
        self.client_id = client_id
        self.access_token = self.refresh_token = ''
        self.event_listener = None
        self.monitor = xbmc.Monitor()
        self.addon = xbmcaddon.Addon()
        self.addonname = self.addon.getAddonInfo('name')
        self.progress_dialog_bg = xbmcgui.DialogProgressBG()
        self.pg_bg_created = False
        self.do_not_clean_counter = False
        
    def cancelOperation(self):
        return self.monitor.abortRequested()
    def begin_signin(self):
        return self.get(self._signin_url, raw_url=True)['pin']
    def finish_signin(self, pin):
        url = self._signin_url + '?' + urllib.urlencode({'action': 'code', 'pin': pin})
        return self.get(url, raw_url=True)
    def login(self, code=None):
        if code is None:
            data = self._get_login_request_data('refresh_token')
            if data['refresh_token'] == '' :
                raise OneDriveException(Exception('login', 'No authorization code or refresh token provided.'), None, 'login method', str(data))
        else:
            data = self._get_login_request_data('authorization_code', code)
        jsonResponse = self.post(self._login_url, params=data, raw_url=True)
        if not self.cancelOperation():
            if 'error' in jsonResponse:
                raise OneDriveException(Exception('login', utils.Utils.str(jsonResponse['error']), utils.Utils.str(jsonResponse['error_description'])), None, 'response of login', str(jsonResponse))
            else:
                self.access_token = jsonResponse['access_token']
                self.refresh_token = jsonResponse['refresh_token']
                if not self.event_listener is None:
                    self.event_listener(self, 'login_success', jsonResponse)
    
    def _get_login_request_data(self, grant_type, code=None):
        data = {
            'client_id': self.client_id,
            'redirect_uri': self._redirect_uri,
            'grant_type': grant_type
        }
        if grant_type == 'authorization_code':
            data['code'] = code
        elif grant_type == 'refresh_token':
            data['refresh_token'] = self.refresh_token
        return data
    
    def _make_path(self, path):
        if not (re.search("^\/", path)):
            path = "/" + path
        return path
    
    def get_url_params(self, params=None, raw_url=False):
        access_token = self.access_token
        if access_token is None:
            raise Exception('request', 'Not logged in.')
        if params is None:
            params = {}
        if not raw_url:
            params['access_token'] = access_token
        return urllib.urlencode(params)
    
    def get_url(self, method, path, params=None):
        url = self._api_url+self._make_path(path)
        if method == 'get':
            url = url + '?' + params
        return url
    
    def request(self, method, path, params=None, raw_url=False, retry=True):
        url_params = self.get_url_params(params, raw_url)
        url = self.get_url(method, path, url_params) if not raw_url else path
        try:
            if not self.cancelOperation():
                if method == 'get':
                    response = urllib2.urlopen(url).read()
                else:
                    response = urllib2.urlopen(url, url_params).read()
            if not self.do_not_clean_counter:
                self.retry_times = 0
            if not self.cancelOperation():
                return json.loads(response)
            return {}
        except Exception as e:
            if self.retry_times < self.retry_target and retry:
                self.retry_times += 1
                if isinstance(e, urllib2.HTTPError) and (e.code == 401 or e.code == 404):
                    self.do_not_clean_counter = True
                    self.login()
                    self.do_not_clean_counter = False
                else:
                    again = ' again'
                    attempt = self.addon.getLocalizedString(30045) % (str(self.retry_times), str(self.retry_target))
                    seconds = self.retry_times*5
                    if self.retry_times == 1:
                        again = ''
                        attempt = None
                    self.progress_dialog_bg.create(self.addonname)
                    self.pg_bg_created = True
                    current_time = time.time()
                    max_waiting_time = current_time + seconds
                    while not self.cancelOperation() and max_waiting_time > current_time:
                        remaining = round(max_waiting_time-current_time)
                        p = int(remaining/seconds*100) if remaining > 0 else 0
                        p = 100 if p > 100 else p
                        self.progress_dialog_bg.update(p, self.addon.getLocalizedString(30043) % again + ' ' + self.addon.getLocalizedString(30044) % str(int(remaining)), attempt)
                        if self.monitor.waitForAbort(1):
                            break
                        current_time = time.time()
                    self.progress_dialog_bg.close()
                return self.request(method, path, params, raw_url, retry)
            else:
                tb = traceback.format_exc()
                if self.pg_bg_created:
                    self.progress_dialog_bg.close()
                self.retry_times = 0
                response = None
                if isinstance(e, urllib2.HTTPError):
                    origin = OneDriveHttpException(e)
                    try:
                        response = e.read()
                    except:
                        response = 'Error reading the body response!\n' + traceback.format_exc()
                else:
                    origin = e
                url_params += '\n--service response: --\n' + utils.Utils.str(response)
                raise OneDriveException(origin, tb, url, url_params)
        
    def get(self, path, **kwargs):
        return self.request('get', path, **kwargs)
    
    def post(self, path, **kwargs):
        return self.request('post', path, **kwargs)

class OneDriveException(Exception):
    origin = None
    tb = None
    url = None
    body = None
    def __init__(self, origin, tb, url, body):
        self.origin = origin
        self.tb = tb
        self.url = url
        self.body = body

class OneDriveHttpException(urllib2.HTTPError):
    def __init__(self, origin):
        self.code = origin.code
        