#   Copyright (C) 2018 Lunatixz, eracknaphobia, d21spike
#
#
# This file is part of Sling.TV.
#
# Sling.TV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sling.TV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sling.TV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, _strptime, datetime, re, traceback, pytz, calendar, random
import urlparse, urllib, urllib2, socket, json, requests, base64, inputstreamhelper
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
from itertools import cycle


from requests_oauthlib import OAuth1
from resources.lib.globals import *

class UserClient(object):

    HASH                = 'RB4DDQNZWhIqKB0IGxYIURgELTMcIRANAwNFMgEhVwVNBg0EXjE6LlwhGwYgBFw5OzENV3k6JS5d\n                                            E0cBAzo/DAJfQUYeIzUjfydaXCUyEhcxQFlL'
    OTL_URL             = '%s/v5/sessions?client_application=ottweb&format=json&locale=en' % BASE_API
    OTK_URL              = '%s/v5/users/access_from_jwt'%BASE_API
    ACCESS_TOKEN        = ''
    ACCESS              = REAL_SETTINGS.getSetting('access')
    OCK                 = ''
    OCS                 = ''
    OTL                 = ''
    OTK                 = ''
    OTS                 = ''

    def __init__(self):
        self.deviceID()
        if self.ACCESS == '':
            self.ACCESS_TOKEN = ''
            REAL_SETTINGS.setSetting('access_token', self.ACCESS_TOKEN)
            self.ACCESS = self.HASH
        self.getAccess()

            
    def deviceID(self):
        global DEVICE_ID
        if DEVICE_ID != '': return
        randomID = ""
        randomBag = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        for x in range(0, 32):
            randomID += randomBag[random.randint(0, 61)]
            if x == 7 or x == 11 or x == 15 or x == 19:
                randomID += '-'
        REAL_SETTINGS.setSetting('device_id', randomID)
        DEVICE_ID = randomID

        
    def loggedIn(self):
        if ACCESS_TOKEN == '': return False, 'ACCESS_TOKEN is blank, not logged in.'
        token_array = ACCESS_TOKEN.split('.')
        if len(token_array) == 0: return False, 'ACCESS_TOKEN is corrupt, not logged in.'

        user_token = loadJSON(base64.b64decode(token_array[1] + '=='))
        if 'email' in user_token:
            if user_token['email'] == USER_EMAIL: return True, 'ACCESS_TOKEN email matches USER_EMAIL, logged in.'
            else:
                REAL_SETTINGS.setSetting('access_token', '')
                REAL_SETTINGS.setSetting('user_email', '')
                REAL_SETTINGS.setSetting('password', '')
                return False, 'ACCESS_TOKEN email does not match USER_EMAIL, not logged in.'
        else:
            REAL_SETTINGS.setSetting('access_token', '')
            return False, 'ACCESS_TOKEN corrupt, not logged in.'
            
            
    def getRegionInfo(self):
        global USER_DMA, USER_OFFSET, USER_ZIP
        if not self.loggedIn(): return False, 'Must be logged in to retrieve region info.'
        log('getRegionInfo, Subscriber ID = ' + SUBSCRIBER_ID + ' | Device ID = ' + DEVICE_ID)
        if SUBSCRIBER_ID == '': return False, 'SUBSCRIBER_ID and DEVICE_ID required ' + \
                                                                            'for getRegionInfo'
        if DEVICE_ID == '':
            self.deviceID()
        regionUrl = BASE_GEO.format(SUBSCRIBER_ID, DEVICE_ID)
        log('getRegionInfo, URL = ' + regionUrl)
        headers = {
            "Host" : "p-geo.movetv.com",
            "Connection" : "keep-alive",
            "Origin" : "https://watch.sling.com",
            "User-Agent" : USER_AGENT,
            "Accept" : "*/*",
            "Referer" : "https://watch.sling.com/",
            "Accept-Encoding" : "gzip, deflate, br",
            "Accept-Language" : "en-US,en;q=0.9"
        }
        response = requests.get(regionUrl, headers=headers, verify=VERIFY)
        log("getRegionInfo Response = > " + str(response.json()))
        if response.status_code == 200:
            response = response.json()
            USER_DMA = str(response.get('dma',{}) or '')
            USER_OFFSET = (response.get('time_zone_offset',{}) or '')
            USER_ZIP = str(response.get('zip_code', {}) or '')
            REAL_SETTINGS.setSetting('user_dma', USER_DMA)
            REAL_SETTINGS.setSetting('user_offset', USER_OFFSET)
            REAL_SETTINGS.setSetting('user_zip', USER_ZIP)
            return True, { "USER_DMA" : USER_DMA, "USER_OFFSET" : USER_OFFSET }
        else:
            return False, 'Failed to retrieve user region info.'
            
            
    def getUserSubscriptions(self, subURL):
        global SUBSCRIBER_ID
        log("getUserSubscriptions =>URL: " + subURL)
        if not self.loggedIn(): return False, 'Must be logged in to retrieve subscriptions.'
        auth = OAuth1(self.OCK, self.OCS, self.OTK, self.OTS)
        response = requests.get(subURL, headers=HEADERS, auth=auth, verify=VERIFY)
        log("getUserSubscriptions Response = > " + str(response.json()))
        if response.status_code == 200:
            if SUBSCRIBER_ID == '':
                SUBSCRIBER_ID =response.json()['guid']
                REAL_SETTINGS.setSetting('subscriber_id', SUBSCRIBER_ID)

            subscriptions = response.json()['subscriptionpacks']
            sub_packs = ''
            legacy_subs = ''
            for subscription in subscriptions:
                if sub_packs != '':
                    sub_packs += "+"
                sub_packs += subscription['guid']
                if legacy_subs != '':
                    legacy_subs += "+"
                legacy_subs += str(subscription['id'])

            REAL_SETTINGS.setSetting('user_subs', sub_packs)
            REAL_SETTINGS.setSetting('legacy_subs', legacy_subs)
            return True, sub_packs


    def getAuth(self):
        return OAuth1(self.OCK, self.OCS, self.OTK, self.OTS)
        
        
    def getOTK(self):
        if not self.loggedIn(): return False, 'Must be logged in to retrieve OTK.'
        self.deviceID();
        self.getAccess()

        if self.OTL == '':
            otl_payload = {
                "email": USER_EMAIL,
                "password": USER_PASSWORD
            }
            log("getOTK => Login Payload: " + str(otl_payload))
            response = requests.post(self.OTL_URL, headers=HEADERS, data=json.dumps(otl_payload), \
                                    verify = VERIFY)
            log("getOTK Login Response => " + str(response) + "" + str(response.json()))
            if response.status_code == 200 and 'token' in response.json():
                self.OTL = response.json()['token']
                self.setAccess()
        if self.OTL != '':
            otk_payload = {
                "token": self.OTL,
                "device_guid": DEVICE_ID,
                "client_application": "Browser"
            }
            log("getOTK => Payload: " + str(otk_payload))
            auth = OAuth1(self.OCK, self.OCS)
            headers = {
                "Host": "ums.p.sling.com",
                "Connection": "keep-alive",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Origin": "https://watch.sling.com",
                "User-Agent": USER_AGENT,
                "Content-Type": "application/json; charset=UTF-8",
                "Accept": "*/*",
                "Referer": "https://watch.sling.com/",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9"
            }
            response = requests.post(self.OTK_URL, headers=headers, data=json.dumps(otk_payload), auth=auth, verify=VERIFY)
            log("getOTK Auth = > " + str(response) + str(response.json()))

            if response.status_code == 200 and 'access_token' in response.json():
                json_data = response.json()['access_token']
                self.OTK = json_data['token']
                self.OTS = json_data['secret']
                self.setAccess()
                return True, 'Successfully retrieved OTK.'
            else:
                return False, 'Failed to retrieve OTK.'
        else:
            return False, 'OTL required to retrieve signing token.'


    def getUserID(self):
        user_info = ACCESS_TOKEN[ACCESS_TOKEN.find('.')+1: ACCESS_TOKEN.rfind('.')]
        json_string = json.loads(base64.b64decode(user_info + "==="))
        return json_string

        
    def logIn(self, loginURL, email=USER_EMAIL, password=USER_PASSWORD):
        global ACCESS_TOKEN, USER_EMAIL, USER_PASSWORD
        log("logIn =>URL: " + loginURL + "email: " + email)
        status, message = self.loggedIn()
        if status: return status, 'Already logged in.'

        if email == '' or password == '':
            # firstrun wizard
            if yesnoDialog(LANGUAGE(30010), no=LANGUAGE(30008), yes=LANGUAGE(30009)):
                email = inputDialog(LANGUAGE(30006))
                password = inputDialog(LANGUAGE(30007), opt=xbmcgui.ALPHANUM_HIDE_INPUT)
                REAL_SETTINGS.setSetting('User_Email', email)
                REAL_SETTINGS.setSetting('User_Password', password)
                USER_EMAIL = email
                USER_PASSWORD = password
            else:
                return False, 'Login Aborted'

        payload = '{"username":"' + email + '","password":"' + password + '"}'
        response = requests.post(loginURL, headers=HEADERS, data=payload, verify=VERIFY)
        if response.status_code == 200 and 'access_token' in response.json():
            REAL_SETTINGS.setSetting('access_token', response.json()['access_token'])
            ACCESS_TOKEN = response.json()['access_token']
            if self.OTK == '':
                if self.getOTK(): return True, 'Successfully logged in.'
                else: return False, "Failed to log in, no otk"
            else: return True, 'Successfully logged in.'
        else: return False, 'Failed to log in, status code ' + str(response.status_code)

        
    def logOut(self):
        REAL_SETTINGS.setSetting('access_token', '')
        REAL_SETTINGS.setSetting('User_Email', '')
        REAL_SETTINGS.setSetting('User_Password', '')
        REAL_SETTINGS.setSetting('subscriber_id', '')
        REAL_SETTINGS.setSetting('user_dma', '')
        REAL_SETTINGS.setSetting('user_subs', '')
        REAL_SETTINGS.setSetting('legacy_subs', '')


    def xor(self, data, key='INSECURE', encode=False):
        if not encode:
            data = base64.decodestring(data)
        xored = ''.join(chr(ord(x) ^ ord(y)) for (x, y) in zip(data, cycle(key)))
        if encode:
            return base64.encodestring(xored).strip()
        return xored


    def getAccess(self):
        global DEVICE_ID, ADDON_ID
        if self.ACCESS == self.HASH: key = ADDON_ID
        else: key = DEVICE_ID
        decoded_access = self.xor(self.ACCESS, key, False)
        access_array = decoded_access.split(',')
        self.OCK = access_array[0]
        self.OCS = access_array[1]
        self.OTL = access_array[2]
        self.OTK = access_array[3]
        self.OTS = access_array[4]
        self.getRegionInfo()


    def setAccess(self):
        global DEVICE_ID, ADDON_ID
        if self.ACCESS == self.HASH: key = ADDON_ID
        else: key = DEVICE_ID

        payload = ('%s,%s,%s,%s,%s') % (self.OCK, self.OCS, self.OTL, self.OTK, self.OTS)
        new_access = self.xor(payload, key, True)
        REAL_SETTINGS.setSetting('access', new_access)
        self.ACCESS = new_access
