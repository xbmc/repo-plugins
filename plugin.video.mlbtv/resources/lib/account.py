import requests
from resources.lib.utils import Util
from resources.lib.globals import *
from kodi_six import xbmc, xbmcaddon, xbmcgui
import time, uuid
import random
import string
import base64

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
                self.addon.setSetting('okta_id', '')
                sys.exit()


    def logout(self):
        self.util.delete_cookies()
        self.addon.setSetting('login_token', '')
        self.addon.setSetting('login_token_expiry', '')
        self.addon.setSetting('device_id', '')
        self.addon.setSetting('session_key', '')
        self.addon.setSetting('entitlements', '')
        self.addon.setSetting('okta_id', '')
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

    def get_playback(self, content_id):
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
        token = r.json()['data']['initPlaybackSession']['playback']['token']
        xbmc.log(f'Token: {token}')
        return stream_url, headers, token

    def get_stream(self, content_id):
        stream_url, headers, token = self.get_playback(content_id)
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

    def okta_id(self):
        if self.addon.getSetting('okta_id') == '':
            self.get_okta_id()
        return self.addon.getSetting('okta_id')
        
    def get_okta_id(self):
        try:
            # get a new playback token for a past free game
            url, headers, token = self.get_playback('b7f0fff7-266f-4171-aa2d-af7988dc9302')
            if token:
                encoded_okta_id = token.split('_')[1]
                okta_id = base64.b64decode(encoded_okta_id.encode('ascii') + b'==').decode('ascii')
                self.addon.setSetting('okta_id', okta_id)
        except Exception as e:
            xbmc.log('error getting okta_id ' + str(e))
            sys.exit(0)

    def get_event_stream(self, url):
        xbmc.log('fetching event video stream from url')

        headers = {
            'User-Agent': UA_PC,
            'Authorization': 'Bearer ' + self.login_token(),
            'Accept': '*/*',
            'Origin': 'https://www.mlb.com',
            'Referer': 'https://www.mlb.com'
        }
        r = requests.get(url, headers=headers, verify=VERIFY)

        text_source = r.text
        #xbmc.log(text_source)

        # sometimes the returned content is already a stream playlist
        if text_source.startswith('#EXTM3U'):
            xbmc.log('video url is already a stream playlist')
            video_stream_url = url
        # otherwise it is JSON containing the stream URL
        else:
            json_source = r.json()
            if 'data' in json_source and len(json_source['data']) > 0 and 'value' in json_source['data'][0]:
                video_stream_url = json_source['data'][0]['value']
                xbmc.log('found video stream url : ' + video_stream_url)
        return video_stream_url
        

    def get_linear_stream(self, network):
        if self.addon.getSetting('device_id') == '' or self.addon.getSetting('session_key') == '':
            self.get_device_session_id()
        url = 'https://media-gateway.mlb.com/graphql'
        headers = {
            'User-Agent': UA_PC,
            'Authorization': 'Bearer ' + self.login_token(),
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.5',
            'connection': 'keep-alive',
            'content-type': 'application/json',
            'x-client-name': 'WEB',
            'x-client-version': '7.8.1',
            'cache-control': 'no-cache',
            'origin': 'https://www.mlb.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://www.mlb.com/',
            'sec-ch-ua': '"Chromium";v="133", "Google Chrome";v="133", "Not-A.Brand";v="8"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site'
        }
        data = {
            "operationName": "contentCollections",
            "query": '''query contentCollections(
                    $categories: [ContentGroupCategory!]
                    $includeRestricted: Boolean = false
                    $includeSpoilers: Boolean = false
                    $limit: Int = 10,
                    $skip: Int = 0\n    ) {
                    contentCollections(
                        categories: $categories
                        includeRestricted: $includeRestricted
                        includeSpoilers: $includeSpoilers
                        limit: $limit
                        skip: $skip
                    ) {
                        title
                        category
                        contents {
                            assetTrackingKey
                            contentDate
                            contentId
                            contentRestrictions
                            description
                            duration
                            language
                            mediaId
                            officialDate
                            title
                            mediaState {
                                state
                                mediaType
                            }
                            thumbnails {
                                thumbnailType
                                templateUrl
                                thumbnailUrl
                            }
                        }
                    }
                }''',
            "variables": {
                "categories": network,                
                "limit": "25"
            }
        }
        xbmc.log(str(data))
        r = requests.post(url, headers=headers, json=data, verify=VERIFY)
        xbmc.log(r.text)
        if not r.ok:
            dialog = xbmcgui.Dialog()
            msg = ""
            for item in r.json()['errors']:
                msg += item['code'] + '\n'
            dialog.notification(LOCAL_STRING(30270), msg, self.icon, 5000, False)
            sys.exit()

        availableStreams  = r.json()['data']['contentCollections'][0]['contents']
        for stream in availableStreams:
            try:
                stream_url, headers = self.get_stream(stream['mediaId'])
                xbmc.log(f'Stream URL: {stream_url}')
                return stream_url
            except:
                pass
