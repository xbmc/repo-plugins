import requests
from resources.lib.utils import Util
from resources.lib.globals import *
from kodi_six import xbmc, xbmcaddon, xbmcgui
import time, uuid
import random
import string

if sys.version_info[0] > 2:
    from urllib.parse import quote
else:
    from urllib import quote


class Account:
    addon = xbmcaddon.Addon()
    username = ''
    password = ''    
    icon = addon.getAddonInfo('icon')
    verify = False

    def __init__(self):
        self.username = self.addon.getSetting('username')
        self.password = self.addon.getSetting('password')
        self.util = Util()
        self.media_url = 'https://media-gateway.mlb.com/graphql'

    def login(self):
        # Check if username and password are provided
        if self.username == '':
            dialog = xbmcgui.Dialog()
            self.username = dialog.input(LOCAL_STRING(30140), type=xbmcgui.INPUT_ALPHANUM)
            self.addon.setSetting(id='username', value=self.username)

        if self.password == '':
            dialog = xbmcgui.Dialog()
            self.password = dialog.input(LOCAL_STRING(30150), type=xbmcgui.INPUT_ALPHANUM,
                                    option=xbmcgui.ALPHANUM_HIDE_INPUT)
            self.addon.setSetting(id='password', value=self.password)

        if self.username == '' or self.password == '':
            sys.exit()
        else:
            url = 'https://ids.mlb.com/oauth2/aus1m088yK07noBfh356/v1/token'
            headers = {'User-Agent': UA_ANDROID,
                       'Content-Type': 'application/x-www-form-urlencoded'
                       }
            payload = ('grant_type=password&username=%s&password=%s&scope=openid offline_access'
                       '&client_id=0oa3e1nutA1HLzAKG356') % (quote(self.username),
                                                             quote(self.password))

            r = requests.post(url, headers=headers, data=payload, verify=self.verify)
            if r.ok:
                login_token = r.json()['access_token']
                login_token_expiry = datetime.now() + timedelta(seconds=int(r.json()['expires_in']))
                self.addon.setSetting('login_token', login_token)
                self.addon.setSetting('login_token_expiry', str(login_token_expiry))
                self.get_device_session_id()
            else:
                dialog = xbmcgui.Dialog()
                msg = LOCAL_STRING(30263)
                if 'error_description' in r.json():
                    msg = r.json()['error_description']
                dialog.notification(LOCAL_STRING(30262), msg, ICON, 5000, False)
                self.addon.setSetting('login_token', '')
                self.addon.setSetting('login_token_expiry', '')
                self.addon.setSetting('device_id', '')
                self.addon.setSetting('session_key', '')
                self.addon.setSetting('entitlements', '')
                sys.exit()


    def logout(self):
        self.util.delete_cookies()
        self.addon.setSetting('login_token', '')
        self.addon.setSetting('login_token_expiry', '')
        self.addon.setSetting('device_id', '')
        self.addon.setSetting('session_key', '')
        self.addon.setSetting('entitlements', '')
        self.addon.setSetting('username', '')
        self.addon.setSetting('password', '')

    # need to login to access featured videos like Big Inning and MiLB games
    def login_token(self):
        if self.addon.getSetting('login_token_expiry') == '' or \
                parse(self.addon.getSetting('login_token_expiry')) < datetime.now():
            self.login()

        return self.addon.getSetting('login_token')


    def access_token(self):
        return self.login_token()

    def get_stream(self, content_id):
        if self.addon.getSetting('device_id') == '' or self.addon.getSetting('session_key') == '':
            self.get_device_session_id()
        headers = {
            'User-Agent': UA_PC,
            'Authorization': 'Bearer ' + self.login_token(),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        data = {
            "operationName": "initPlaybackSession",
            "query": '''mutation initPlaybackSession(
                $adCapabilities: [AdExperienceType]
                $mediaId: String!
                $deviceId: String!
                $sessionId: String!
                $quality: PlaybackQuality
            ) {
                initPlaybackSession(
                    adCapabilities: $adCapabilities
                    mediaId: $mediaId
                    deviceId: $deviceId
                    sessionId: $sessionId
                    quality: $quality
                ) {
                    playbackSessionId
                    playback {
                        url
                        token
                        expiration
                        cdn
                    }
                    adScenarios {
                        adParamsObj
                        adScenarioType
                        adExperienceType
                    }
                    adExperience {
                        adExperienceTypes
                        adEngineIdentifiers {
                            name
                            value
                        }
                        adsEnabled
                    }
                    heartbeatInfo {
                        url
                        interval
                    }
                    trackingObj
                }
            }''',
            "variables": {
                "adCapabilities": ["GOOGLE_STANDALONE_AD_PODS"],                
                "mediaId": content_id,
                "quality": "PLACEHOLDER",
                "deviceId": self.addon.getSetting('device_id'),
                "sessionId": self.addon.getSetting('session_key')
            }
        }
        xbmc.log(str(data))
        r = requests.post(self.media_url, headers=headers, json=data, verify=VERIFY)
        xbmc.log(r.text)
        #r = requests.get(url, headers=headers, cookies=self.util.load_cookies(), verify=self.verify)
        if not r.ok:
            dialog = xbmcgui.Dialog()
            msg = ""
            for item in r.json()['errors']:
                msg += item['code'] + '\n'
            dialog.notification(LOCAL_STRING(30270), msg, self.icon, 5000, False)
            sys.exit()

        stream_url = r.json()['data']['initPlaybackSession']['playback']['url']
        xbmc.log(f'Stream URL: {stream_url}')
        headers = 'User-Agent=' + UA_PC
        return stream_url, headers
    
    def get_device_session_id(self):
        headers = {
            'User-Agent': UA_PC,
            'Authorization': 'Bearer ' + self.login_token(),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        data = {
            "operationName": "initSession",
            "query": '''mutation initSession($device: InitSessionInput!, $clientType: ClientType!, $experience: ExperienceTypeInput) {
                initSession(device: $device, clientType: $clientType, experience: $experience) {
                    deviceId
                    sessionId
                    entitlements {
                        code
                    }
                    location {
                        countryCode
                        regionName
                        zipCode
                        latitude
                        longitude
                    }
                    clientExperience
                    features
                }
            }''',
            "variables": {
                "device": {
                    "appVersion": "7.8.2",
                    "deviceFamily": "desktop",
                    "knownDeviceId": "",
                    "languagePreference": "ENGLISH",
                    "manufacturer": "Google Inc.",
                    "model": "",
                    "os": "windows",
                    "osVersion": "10"
                },
                "clientType": "WEB"
            }
        }

        r = requests.post(self.media_url, headers=headers, json=data)
        device_id = r.json()['data']['initSession']['deviceId']
        session_id = r.json()['data']['initSession']['sessionId']
        entitlements = []
        for entitlement in r.json()['data']['initSession']['entitlements']:
            entitlements.append(entitlement['code'])
        
        self.addon.setSetting('device_id', device_id)
        self.addon.setSetting('session_key', session_id)
        self.addon.setSetting('entitlements', json.dumps(entitlements))

    def get_entitlements(self):
        if self.addon.getSetting('entitlements') == '':
            self.get_device_session_id()
        return self.addon.getSetting('entitlements')
        
    def get_broadcast_start_time(self, stream_url):
        try:
            variant_url = stream_url.replace('.m3u8', '_5600K.m3u8')
            r = requests.get(variant_url, headers={'User-Agent': UA_PC}, verify=self.verify)
            content = r.text
        
            line_array = content.splitlines()
            for line in line_array:
                if line.startswith('#EXT-X-PROGRAM-DATE-TIME:'):
                    return parse(line[25:])
        except Exception as e:
            xbmc.log('error getting get_broadcast_start_time ' + str(e))
        return None