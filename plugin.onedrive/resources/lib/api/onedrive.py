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

class OneDrive:
    _login_url = 'https://login.live.com/oauth20_token.srf'
    _redirect_uri = 'https://login.live.com/oauth20_desktop.srf'
    _api_url = 'https://api.onedrive.com/v1.0'
    _signin_url = 'http://onedrive.daro.mx/service.jsp'
    exporting_count = 0
    exporting_target = 0
    exporting_percent = 0
    def __init__(self, client_id):
        self.retry_times = 0
        self.client_id = client_id
        self.access_token = self.refresh_token = ''
        self.event_listener = None
    def begin_signin(self):
        response = urllib2.urlopen(self._signin_url).read()
        jsonResponse = json.loads(response)
        return jsonResponse['pin']
    def finish_signin(self, pin):
        url = self._signin_url + '?' + urllib.urlencode({'action': 'code', 'pin': pin})
        response = urllib2.urlopen(url).read()
        jsonResponse = json.loads(response)
        return jsonResponse
    def login(self, code=None):
        if code is None:
            data = self._get_login_request_data('refresh_token')
            if data['refresh_token'] == '' :
                raise Exception('login', 'No authorization code or refresh token provided.')
        else:
            data = self._get_login_request_data('authorization_code', code)
        response = urllib2.urlopen(self._login_url, urllib.urlencode(data)).read()
        jsonResponse = json.loads(response)
        if 'error' in jsonResponse:
            raise Exception('login', utils.Utils.str(jsonResponse['error']), utils.Utils.str(jsonResponse['error_description']))
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
    
    def _check_response_pass(self, response):
        if 'error' in response:
            error = response['error']
            if error['code'] == 'request_token_expired' or error['code'] == 'unauthenticated':
                return False
            else:
                raise Exception('request', 'Unknow error: "' + error['code'] + '": ' + error['message'] + ', retry times: '+self.retry_times);
        return True
    
    def _make_path(self, path):
        if not (re.search("^\/", path)):
            path = "/" + path
        return path
    
    def get_url_params(self, params=None):
        access_token = self.access_token
        if access_token is None:
            raise Exception('request', 'Not logged in.')
        if params is None:
            params = {}
        params['access_token'] = access_token
        return urllib.urlencode(params)
    
    def get_url(self, method, path, params=None):
        url = self._api_url+self._make_path(path)
        if method == 'get':
            url = url + '?' + params
        return url
    
    def request(self, method, path, params=None, raw_url=False):
        try:
            url_params = self.get_url_params(params)
            url = self.get_url(method, path, url_params) if not raw_url else path
            if method == 'get':
                response = urllib2.urlopen(url).read()
            else:
                response = urllib2.urlopen(url, url_params).read()
            jsonResponse = json.loads(response)
            self.retry_times = 0
            return jsonResponse
        except urllib2.URLError, e:
            print e
            print url
            if self.retry_times < 1:
                if e.code == 401 or e.code == 404:
                    self.login()
                self.retry_times += 1
                return self.request(method, path, params, raw_url)
            else:
                raise e

    def get(self, path, **kwargs):
        return self.request('get', path, **kwargs)
    
    def post(self, path, **kwargs):
        return self.request('post', path, **kwargs)
