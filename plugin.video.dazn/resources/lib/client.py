# -*- coding: utf-8 -*-

import simple_requests as requests

class Client:

    def __init__(self, plugin):
        self.plugin = plugin

        self.DEVICE_ID = self.plugin.get_setting('device_id')
        self.TOKEN = self.plugin.get_setting('token')
        self.MPX = self.plugin.get_setting('mpx')
        self.COUNTRY = self.plugin.get_setting('country')
        self.LANGUAGE = self.plugin.get_setting('language')
        self.PORTABILITY = self.plugin.get_setting('portability')
        self.POST_DATA = {}
        self.ERRORS = 0

        self.HEADERS = {
            'Content-Type': 'application/json',
            'Referer': self.plugin.api_base
        }

        self.PARAMS = {
            '$format': 'json'
        }

        self.STARTUP = self.plugin.api_base + 'v4/Startup'
        self.RAIL = self.plugin.api_base + 'v2/Rail'
        self.RAILS = self.plugin.api_base + 'v4/Rails'
        self.EPG = self.plugin.api_base + 'v1/Epg'
        self.EVENT = self.plugin.api_base + 'v2/Event'
        self.PLAYBACK = self.plugin.api_base + 'v2/Playback'
        self.SIGNIN = self.plugin.api_base + 'v4/SignIn'
        self.SIGNOUT = self.plugin.api_base + 'v1/SignOut'
        self.REFRESH = self.plugin.api_base + 'v4/RefreshAccessToken'
        self.PROFILE = self.plugin.api_base + 'v1/UserProfile'

    def content_data(self, url):
        data = self.request(url)
        if data.get('odata.error', None):
            self.errorHandler(data)
        return data

    def rails(self, id_, params=''):
        self.PARAMS['groupId'] = id_
        self.PARAMS['params'] = params
        return self.content_data(self.RAILS)

    def rail(self, id_, params=''):
        self.PARAMS['id'] = id_
        self.PARAMS['params'] = params
        return self.content_data(self.RAIL)

    def epg(self, params):
        self.PARAMS['date'] = params
        return self.content_data(self.EPG)

    def event(self, id_):
        self.PARAMS['Id'] = id_
        return self.content_data(self.EVENT)

    def playback_data(self, id_):
        params = {
            'AssetId': id_,
            'Format': 'MPEG-DASH',
            'PlayerId': 'DAZN-' + self.DEVICE_ID,
            'Secure': 'true',
            'PlayReadyInitiator': 'false',
            'LanguageCode': self.LANGUAGE
        }
        self.PARAMS.update(params)
        return self.request(self.PLAYBACK)

    def playback(self, id_):
        data = self.playback_data(id_)
        if data.get('odata.error', None):
            self.errorHandler(data)
            if self.TOKEN:
                data = self.playback_data(id_)
        return data
            
    def userProfile(self):
        data = self.request(self.PROFILE)
        if data.get('odata.error', None):
            self.errorHandler(data)
        else:
            if 'PortabilityAvailable' in self.PORTABILITY:
                self.COUNTRY = self.plugin.portability_country(self.COUNTRY, data['UserCountryCode'])
                self.plugin.set_setting('country', self.COUNTRY)
            self.plugin.set_setting('viewer_id', data['ViewerId'])

    def setToken(self, auth, result):
        self.plugin.log('[{0}] signin: {1}'.format(self.plugin.addon_id, result))
        if auth and result == 'SignedIn':
            self.TOKEN = auth['Token']
            self.MPX = self.plugin.get_mpx(self.TOKEN)
        else:
            if result == 'HardOffer':
                self.plugin.dialog_ok(30161)
            self.signOut()
        self.plugin.set_setting('token', self.TOKEN)
        self.plugin.set_setting('mpx', self.MPX)

    def signIn(self):
        credentials = self.plugin.get_credentials()
        if credentials:
            self.POST_DATA = {
                'Email': credentials['email'],
                'Password': credentials['password'],
                'DeviceId': self.DEVICE_ID,
                'Platform': 'web'
            }
            data = self.request(self.SIGNIN)
            if data.get('odata.error', None):
                self.errorHandler(data)
            else:
                self.setToken(data['AuthToken'], data.get('Result', 'SignInError'))
        else:
            self.plugin.dialog_ok(30004)

    def signOut(self):
        self.POST_DATA = {
            'DeviceId': self.DEVICE_ID
        }
        r = self.request(self.SIGNOUT)
        self.TOKEN = ''
        self.plugin.set_setting('token', self.TOKEN)

    def refreshToken(self):
        self.POST_DATA = {
            'DeviceId': self.DEVICE_ID
        }
        data = self.request(self.REFRESH)
        if data.get('odata.error', None):
            self.signOut()
            self.errorHandler(data)
        else:
            self.setToken(data['AuthToken'], data.get('Result', 'RefreshAccessTokenError'))

    def startUp(self):
        kodi_language = self.plugin.get_language()
        self.POST_DATA = {
            'LandingPageKey': 'generic',
            'Languages': '{0}, {1}'.format(kodi_language, self.LANGUAGE),
            'Platform': 'web',
            'Manufacturer': '',
            'PromoCode': ''
        }
        data = self.request(self.STARTUP)
        region = data.get('Region', {})
        if region.get('isAllowed', False):
            self.PORTABILITY = region['CountryPortabilityStatus']
            self.COUNTRY = region['Country']
            self.LANGUAGE = region['Language']
            languages = data['SupportedLanguages']
            for i in languages:
                if i == kodi_language:
                    self.LANGUAGE = i
                    break
            self.plugin.set_setting('language', self.LANGUAGE)
            self.plugin.set_setting('country', self.COUNTRY)
            self.plugin.set_setting('portability', self.PORTABILITY)
            if self.TOKEN:
                self.refreshToken()
            else:
                self.signIn()
        else:
            self.TOKEN = ''
            self.plugin.log('[{0}] version: {1} region: {2}'.format(self.plugin.addon_id, self.plugin.addon_version, str(region)))
            self.plugin.dialog_ok(30101)

    def request(self, url):
        self.HEADERS['Authorization'] = 'Bearer ' + self.TOKEN
        self.PARAMS['LanguageCode'] = self.LANGUAGE
        self.PARAMS['Country'] = self.COUNTRY

        if self.POST_DATA:
            r = requests.post(url, headers=self.HEADERS, data=self.POST_DATA, params=self.PARAMS)
            self.POST_DATA  = {}
        else:
            r = requests.get(url, headers=self.HEADERS, params=self.PARAMS)

        if r.headers.get('content-type', '').startswith('application/json'):
            return r.json()
        else:
            if not r.status_code == 204:
                self.plugin.log('[{0}] error: {1} ({2}, {3})'.format(self.plugin.addon_id, url, str(r.status_code), r.headers.get('content-type', '')))
            return {}

    def errorHandler(self, data):
        self.ERRORS += 1
        msg  = data['odata.error']['message']['value']
        code = str(data['odata.error']['code'])
        self.plugin.log('[{0}] version: {1} country: {2} language: {3} portability: {4}'.format(self.plugin.addon_id, self.plugin.addon_version, self.COUNTRY, self.LANGUAGE, self.PORTABILITY))
        self.plugin.log('[{0}] error: {1} ({2})'.format(self.plugin.addon_id, msg, code))
        if code == '10000' and self.ERRORS < 3:
            self.refreshToken()
        elif (code == '401' or code == '10033') and self.ERRORS < 3:
            self.signIn()
        elif code == '7':
            self.plugin.dialog_ok(30107)
        elif code == '3001':
            self.startUp()
        elif code == '10006':
            self.plugin.dialog_ok(30101)
        elif code == '10008':
            self.plugin.dialog_ok(30108)
        elif code == '10049':
            self.plugin.dialog_ok(30151)
