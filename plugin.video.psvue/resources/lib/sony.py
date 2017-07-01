import sys, os, xbmc, xbmcaddon, xbmcgui
import cookielib, requests, urllib
from datetime import datetime


class SONY():
    addon = xbmcaddon.Addon()
    api_url = 'https://auth.api.sonyentertainmentnetwork.com/2.0'
    device_id = ''
    localized = addon.getLocalizedString
    login_client_id = '71a7beb8-f21a-47d9-a604-2e71bee24fe0'
    npsso = ''
    password = ''
    req_client_id = 'dee6a88d-c3be-4e17-aec5-1018514cee40'
    ua_android = 'Mozilla/5.0 (Linux; Android 6.0.1; Build/MOB31H; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/44.0.2403.119 Safari/537.36'
    ua_sony = 'com.sony.snei.np.android.sso.share.oauth.versa.USER_AGENT'
    username = ''
    verify = False


    def __init__(self):
        self.device_id = self.addon.getSetting('deviceId')
        self.npsso = self.addon.getSetting('npsso')
        self.password = self.addon.getSetting('password')
        self.username = self.addon.getSetting('username')


    def check_auth(self):
        self.check_login()
        self.authorize_device()


    def check_login(self):
        expired_cookies = True
        addon_profile_path = xbmc.translatePath(self.addon.getAddonInfo('profile'))
        try:
            cj = cookielib.LWPCookieJar()
            cj.load(os.path.join(addon_profile_path, 'cookies.lwp'), ignore_discard=True)
            if self.npsso != '':
                for cookie in cj:
                    if cookie.name == 'npsso':
                        expired_cookies = cookie.is_expired()
                        break
        except:
            pass

        if expired_cookies:
            self.login()


    def login(self):
        if self.username == '':
            dialog = xbmcgui.Dialog()
            self.username = dialog.input(self.localized(30202), type=xbmcgui.INPUT_ALPHANUM)
            if self.username != '':
                self.addon.setSetting(id='username', value=self.username)
            else:
                sys.exit()

        if self.password == '':
            dialog = xbmcgui.Dialog()
            self.password = dialog.input(self.localized(30203), type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
            if self.password != '':
                self.addon.setSetting(id='password', value=self.password)
            else:
                sys.exit()

        if self.username != '' and self.password != '':
            url = self.api_url + '/ssocookie'
            headers = {"Accept": "*/*",
                       "Content-type": "application/x-www-form-urlencoded",
                       "Origin": "https://id.sonyentertainmentnetwork.com",
                       "Accept-Language": "en-US,en;q=0.8",
                       "Accept-Encoding": "deflate",
                       "User-Agent": self.ua_android,
                       "Connection": "Keep-Alive"
                       }

            payload = 'authentication_type=password&username='+urllib.quote_plus(self.username)+'&password='+urllib.quote_plus(self.password)+'&client_id='+self.login_client_id
            r = requests.post(url, headers=headers, cookies=self.load_cookies(), data=payload, verify=self.verify)
            json_source = r.json()
            self.save_cookies(r.cookies)

            if 'npsso' in json_source:
                npsso = json_source['npsso']
                self.addon.setSetting(id='npsso', value=npsso)
            elif 'authentication_type' in json_source:
                if json_source['authentication_type'] == 'two_step':
                    ticket_uuid = json_source['ticket_uuid']
                    self.two_step_verification(ticket_uuid)
            elif 'error_description' in json_source:
                msg = json_source['error_description']
                self.notification_msg(self.localized(30200), msg)
                sys.exit()
            else:
                # Something went wrong during login
                self.notification_msg(self.localized(30200), self.localized(30201))
                sys.exit()


    def two_step_verification(self, ticket_uuid):
        dialog = xbmcgui.Dialog()
        code = dialog.input(self.localized(30204), type=xbmcgui.INPUT_ALPHANUM)
        if code == '': sys.exit()

        url = self.api_url + '/ssocookie'
        headers = {
            "Accept": "*/*",
            "Content-type": "application/x-www-form-urlencoded",
            "Origin": "https://id.sonyentertainmentnetwork.com",
            "Accept-Language": "en-US,en;q=0.8",
            "Accept-Encoding": "deflate",
            "User-Agent": self.ua_android,
            "Connection": "Keep-Alive",
            "Referer": "https://id.sonyentertainmentnetwork.com/signin/?service_entity=urn:service-entity:psn&ui=pr&service_logo=ps&response_type=code&scope=psn:s2s&client_id="+self.req_client_id+"&request_locale=en_US&redirect_uri=https://io.playstation.com/playstation/psn/acceptLogin&error=login_required&error_code=4165&error_description=User+is+not+authenticated"
        }

        payload = 'authentication_type=two_step&ticket_uuid='+ticket_uuid+'&code='+code+'&client_id='+self.login_client_id
        r = requests.post(url, headers=headers, cookies=self.load_cookies(), data=payload, verify=self.verify)
        json_source = r.json()
        self.save_cookies(r.cookies)

        if 'npsso' in json_source:
            npsso = json_source['npsso']
            self.addon.setSetting(id='npsso', value=npsso)
        elif 'error_description' in json_source:
            msg = json_source['error_description']
            self.notification_msg(self.localized(30200), msg)
            sys.exit()
        else:
            # Something went wrong during login
            self.notification_msg(self.localized(30200), self.localized(30201))
            sys.exit()


    def logout(self):
        url = self.api_url + '/ssocookie'
        headers = {
            "User-Agent": self.ua_sony,
            "Content-Type": "application/x-www-form-urlencoded",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }

        r = requests.delete(url, headers=headers, cookies=self.load_cookies(), verify=self.verify)
        self.save_cookies(r.cookies)
        # Clear addon settings
        self.addon.setSetting(id='reqPayload', value='')
        self.addon.setSetting(id='last_auth', value='')
        self.addon.setSetting(id='npsso', value='')
        self.addon.setSetting(id='default_profile', value='')


    def get_grant_code(self):
        url = self.api_url + '/oauth/authorize'
        url += '?response_type=code'
        url += '&client_id=' + self.req_client_id
        url += '&redirect_uri=https%3A%2F%2Fthemis.dl.playstation.net%2Fthemis%2Fzartan%2Fredirect.html'
        url += '&scope=psn%3As2s'
        url += '&signInOnly=true'
        url += '&service_entity=urn%3Aservice-entity%3Anp'
        url += '&prompt=none'
        url += '&duid=' + self.device_id

        headers = {
            "Accept-Encoding": "gzip",
            "User-Agent": self.ua_sony,
            "Connection": "Keep-Alive"
        }

        code = ''
        r = requests.get(url, headers=headers, allow_redirects=False, cookies=self.load_cookies(), verify=self.verify)
        if 'X-NP-GRANT-CODE' in r.headers:
            code = r.headers['X-NP-GRANT-CODE']
            self.save_cookies(r.cookies)
        else:
            self.notification_msg(self.localized(30207), self.localized(30208))
            sys.exit()

        return code


    def authorize_device(self):
        url = 'https://sentv-user-auth.totsuko.tv/sentv_user_auth/ws/oauth2/token'
        url += '?device_type_id=android_tablet'
        url += '&device_id=' + self.device_id
        url += '&code=' + self.get_grant_code()
        url += '&redirect_uri=https%3A%2F%2Fthemis.dl.playstation.net%2Fthemis%2Fzartan%2Fredirect.html'

        headers = {
            'Origin': 'https://themis.dl.playstation.net',
            'User-Agent': self.ua_android,
            'Accept': '*/*',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip'
        }
        if self.addon.getSetting(id='reqPayload') != '':
            headers['reauth'] = '1'
            headers['reqPayload'] = self.addon.getSetting(id='reqPayload')

        r = requests.get(url, headers=headers, verify=self.verify)
        if 'reqPayload' in r.headers:
            req_payload = str(r.headers['reqPayload'])
            self.addon.setSetting(id='reqPayload', value=req_payload)
            auth_time = r.json()['header']['time_stamp']
            self.addon.setSetting(id='last_auth', value=auth_time)
        else:
            self.notification_msg(self.localized(30207), self.localized(30209))
            sys.exit()


    def get_profiles(self):
        url = 'https://sentv-user-ext.totsuko.tv/sentv_user_ext/ws/v2/profile/ids'
        headers = {
            'User-Agent': self.ua_android,
            'reqPayload': self.addon.getSetting(id='reqPayload'),
            'Accept': '*/*',
            'Origin': 'https://themis.dl.playstation.net',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip'
        }

        r = requests.get(url, headers=headers, verify=self.verify)
        if 'body' in r.json() and 'profiles' in r.json()['body']:
            profiles = r.json()['body']['profiles']
            prof_dict = {}
            prof_list = []
            for profile in profiles:
                xbmc.log(str(profile['profile_id']) + ' ' + str(profile['profile_name']))
                prof_dict[str(profile['profile_name'])] = str(profile['profile_id'])
                prof_list.append(str(profile['profile_name']))

            dialog = xbmcgui.Dialog()
            ret = dialog.select(self.localized(30210), prof_list)
            if ret >= 0:
                self.set_profile(prof_dict[prof_list[ret]])
            else:
                sys.exit()
        else:
            self.notification_msg(self.localized(30205), self.localized(30206))
            sys.exit()


    def set_profile(self, profile_id):
        url = 'https://sentv-user-ext.totsuko.tv/sentv_user_ext/ws/v2/profile/' + profile_id
        headers = {
            'User-Agent': self.ua_android,
            'reqPayload': self.addon.getSetting(id='reqPayload'),
            'Accept': '*/*',
            'Origin': 'https://themis.dl.playstation.net',
            'Host': 'sentv-user-ext.totsuko.tv',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip'
        }

        r = requests.get(url, headers=headers, verify=self.verify)
        req_payload = str(r.headers['reqPayload'])
        self.addon.setSetting(id='reqPayload', value=req_payload)
        auth_time = r.json()['header']['time_stamp']
        self.addon.setSetting(id='last_auth', value=auth_time)
        self.addon.setSetting(id='default_profile', value=profile_id)


    def put_resume_time(self):
        """
        PUT https://sentv-user-action.totsuko.tv/sentv_user_action/ws/v2/watch_history HTTP/1.1
        Host: sentv-user-action.totsuko.tv
        Connection: keep-alive
        Content-Length: 247
        Accept: */*
        reqPayload: redacted
        User-Agent: Mozilla/5.0 (Linux; Android 6.0.1; Build/MOB31H; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/44.0.2403.119 Safari/537.36
        Origin: https://themis.dl.playstation.net
        Content-Type: application/json
        Referer: https://themis.dl.playstation.net/themis/zartan/2.2.2b/
        Accept-Encoding: gzip, deflate
        Accept-Language: en-US
        X-Requested-With: com.snei.vue.android

        {"series_id":redacted,"program_id":redacted,"channel_id":redacted,"tms_id":"EP005544655496","airing_id":redacted,"last_watch_date":"2017-04-28T00:40:43Z","last_timecode":"01:46:29","start_timecode":"00:00:00:00","fully_watched":false,"stream_type":"dvr"}
        """
        url = 'https://sentv-user-action.totsuko.tv/sentv_user_action/ws/v2/watch_history'
        headers = {"Accept": "*/*",
                   "Content-type": "application/json",
                   "Origin": "https://themis.dl.playstation.net",
                   "Accept-Language": "en-US",
                   "Referer": "https://themis.dl.playstation.net/themis/zartan/2.2.2b/",
                   "Accept-Encoding": "gzip, deflate",
                   "User-Agent": self.ua_android,
                   "Connection": "Keep-Alive",
                   'reqPayload': self.addon.getSetting(id='reqPayload'),
                   'X-Requested-With': 'com.snei.vue.android'
                   }

        payload = '{"series_id":redacted,'
        payload += '"program_id":redacted,'
        payload += '"channel_id":redacted,'
        payload += '"tms_id":"redacted",'
        payload += '"airing_id":redacted,'
        payload += '"last_watch_date":"2017-04-28T00:40:43Z",'
        payload += '"last_timecode":"01:46:29",'
        payload += '"start_timecode":"00:00:00:00",'
        payload += '"fully_watched":false,'
        payload += '"stream_type":"dvr"}'

        r = requests.put(url, headers=headers, data=payload, verify=self.verify)


    def save_cookies(self, cookiejar):
        addon_profile_path = xbmc.translatePath(self.addon.getAddonInfo('profile'))
        cookie_file = os.path.join(addon_profile_path, 'cookies.lwp')
        cj = cookielib.LWPCookieJar()
        cj.load(cookie_file,ignore_discard=True)
        for c in cookiejar:
            args = dict(vars(c).items())
            args['rest'] = args['_rest']
            del args['_rest']
            c = cookielib.Cookie(**args)
            cj.set_cookie(c)
        cj.save(cookie_file, ignore_discard=True)


    def load_cookies(self):
        addon_profile_path = xbmc.translatePath(self.addon.getAddonInfo('profile'))
        cookie_file = os.path.join(addon_profile_path, 'cookies.lwp')
        cj = cookielib.LWPCookieJar()
        try:
            cj.load(cookie_file, ignore_discard=True)
        except:
            pass

        return cj


    def notification_msg(self, title, msg):
        dialog = xbmcgui.Dialog()
        dialog.notification(title, msg, xbmcgui.NOTIFICATION_INFO, 5000)
