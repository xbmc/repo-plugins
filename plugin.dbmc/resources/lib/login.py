#/*
# *      Copyright (C) 2013 Joost Kop
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import xbmcaddon
import xbmcgui

import uuid
import urllib, urllib2
import json

from utils import *

from dropbox import client, rest

APP_KEY= 'QF9EBAwGS10NWBJFDRcCHxhfUR5bDhIcQhAeV0YTGBcACgg='
SUCCES = 'Succes'

def getAccessToken():
    tokenRecieved = False
    #Get the session_id (uuid). Create one if there is none yet.
    sessionId = ADDON.getSetting('session_id').decode("utf-8")
    if sessionId == '':
         sessionId = str(uuid.uuid1())
         ADDON.setSetting('session_id', sessionId)
    #Try to get a access_code
    key, secret = decode_key(APP_KEY).split('|')
    flow = client.DropboxOAuth2FlowNoRedirect(key, secret)
    authorize_url = flow.start()
    oauth = DbmcOauth2()
    result, accesscode, pin = oauth.getAccessCode(sessionId, authorize_url)
    if result != SUCCES:
        log_error('Failed to get the PIN/accesscode: %s'%result)
        dialog = xbmcgui.Dialog()
        dialog.ok(ADDON_NAME, LANGUAGE_STRING(30200), '%s'%result)
    elif accesscode == '':
        #No accesscode yet, so direct to web=page with PIN
        log('No accesscode, goto web-page with PIN: %s'%pin)
        dialog = xbmcgui.Dialog()
        dialog.ok(ADDON_NAME, LANGUAGE_STRING(30002), LANGUAGE_STRING(30003), LANGUAGE_STRING(30001) + pin )
    else:
        #Accesscode present, so try to get the access token now
        log_debug('Accesscode recieved: %s. Getting access token...'%accesscode)
        #start the flow process (getting the auth-code
        try:
            access_token, user_id = flow.finish(accesscode)
            #save the token in settings
            ADDON.setSetting('access_token', access_token)
            log('Access token stored')
            tokenRecieved = True
        except rest.ErrorResponse, e:
            log_error('Failed getting the access token: %s'%str(e))
            dialog = xbmcgui.Dialog()
            dialog.ok(ADDON_NAME, LANGUAGE_STRING(30201), str(e), LANGUAGE_STRING(30202))
        finally:
            #always remove the session (failed or not)
            result = oauth.removeAccessCode(sessionId, tokenRecieved)
            if result != SUCCES:
                log_error('Failed removing the access code: %s'%result)
    return tokenRecieved

    
class DbmcOauth2(object):
    #HOST = 'http://localhost/xbmc-dropbox'
    HOST = 'http://xbmc-dropbox.sourceforge.net'
    PAGE = '/dbmc-accesscode/access-code.php'

    def getAccessCode(self, sessionId, oauthUrl=None):
        accesscode = ''
        pin = ''
        params = {'session': sessionId, 'action': 'get'}
        if oauthUrl:
            params['oauth_url'] = oauthUrl
        result, data = self.getData(params)
        if result == SUCCES:
            try:
                response = json.loads(data)
                result = response['result']
                accesscode = response['accesscode']
                pin = response['PIN']
            except Exception as e:
                if not result:
                    result = 'Failed to Decode response data: %s'%(repr(e))
        return result, accesscode, pin
 
    def removeAccessCode(self, sessionId, tokenRecieved):
        params = {'session': sessionId, 'action': 'remove', 'auth_succes': tokenRecieved}
        result, data = self.getData(params)
        if result == SUCCES:
            try:
                response = json.loads(data)
                result = response['result']
            except Exception as e:
                if not result:
                    result = 'Failed to Decode response data: %s'%(repr(e))
        return result

    def getData(self, params):
        paramsEnc = urllib.urlencode(params)
        result = SUCCES
        data = None
        url = '%s%s'%(self.HOST, self.PAGE)
        req = urllib2.Request(url, data=paramsEnc)
        #f = urllib.urlopen('%s%s'%(self.HOST, self.PAGE), params )
        #response = f.read()
        try: 
            response = urllib2.urlopen(req)
            data = response.read()
            log_debug('Received url data: %s'%repr(data))
        except urllib2.URLError as e:
            result = repr(e)
        return result, data
