from globals import *

class SONY:
    addon = xbmcaddon.Addon()
    api_url = 'https://auth.api.sonyentertainmentnetwork.com/2.0'
    user_action_url = 'https://sentv-user-action.totsuko.tv/sentv_user_action/ws/v2'
    device_id = ''
    device_type = 'android_tv'
    localized = addon.getLocalizedString
    login_client_id = '811e7389-7cf2-4927-87f9-e8db00078b12'
    andriod_tv_client_id = '0a5fe341-cb16-47d9-991e-0110fff49713'
    npsso = ''
    password = ''
    req_client_id = 'dee6a88d-c3be-4e17-aec5-1018514cee40'
    ua_browser = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                 'Chrome/75.0.3770.80 Safari/537.36'
    ua_android_tv = 'Mozilla/5.0 (Linux; Android 6.0.1; Hub Build/MHC19J; wv) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                    'Version/4.0 Chrome/72.0.3626.105 Safari/537.36'
    ua_sony = 'com.sony.snei.np.android.sso.share.oauth.versa.USER_AGENT'
    themis = 'https://themis.dl.playstation.net/themis/destro/redirect.html'

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
            self.password = dialog.input(self.localized(30203), type=xbmcgui.INPUT_ALPHANUM,
                                         option=xbmcgui.ALPHANUM_HIDE_INPUT)
            if self.password != '':
                self.addon.setSetting(id='password', value=self.password)
            else:
                sys.exit()

        if self.username != '' and self.password != '':
            s = requests.Session()

            better_referer = 'https://id.sonyentertainmentnetwork.com/id/tv/signin/' \
                             '?ui=ds' \
                             '&hidePageElements=noAccountSection,troubleSigningInLink&service_logo=ps' \
                             '&smcid=tv:psvue' \
                             '&client_id=811e7389-7cf2-4927-87f9-e8db00078b12' \
                             '&response_type=code' \
                             '&scope=psn:s2s,oauth:delete_token,kamaji:megaphone,kamaji:vue_metadata_services,versa:user_preview_order' \
                             '&redirect_uri=https://theia.dl.playstation.net/destro/redirect.html' \
                             '&state=119982410' \
                             '&service_entity=urn:service-entity:np' \
                             '&duid=' + self.device_id + \
                             '&error=login_required' \
                             '&error_code=4165' \
                             '&error_description=User is not authenticated' \
                             '&no_captcha=false'

            url = self.api_url + '/ssocookie'
            # "Referer": "https://id.sonyentertainmentnetwork.com/",
            headers = {
                "Host": "auth.api.sonyentertainmentnetwork.com",
                "X-Requested-With": "com.snei.vue.atv",
                "Origin": "https://id.sonyentertainmentnetwork.com",
                "User-Agent": self.ua_browser,
                "Content-Type": "application/json; charset=UTF-8",
                "Accept": "*/*",
                "Referer": urllib.quote(better_referer),
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9,ru-UA;q=0.8,ru;q=0.7"
            }

            json_payload = {
                "authentication_type": "password",
                "username": self.username,
                "password": self.password,
                "client_id": self.login_client_id
            }

            r = requests.post(url, headers=headers, cookies=self.load_cookies(), json=json_payload, verify=self.verify)
            self.save_cookies(r.cookies)
            json_source = r.json()

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
            "User-Agent": self.ua_android_tv,
            "Connection": "Keep-Alive",
            "Referer": "https://id.sonyentertainmentnetwork.com/signin/?service_entity=urn:service-entity:psn"
                       "&ui=pr&service_logo=ps&response_type=code&scope=psn:s2s&client_id=" + self.req_client_id
                       + "&request_locale=en_US&redirect_uri=https://io.playstation.com/playstation/psn/acceptLogin"
                         "&error=login_required&error_code=4165&error_description=User+is+not+authenticated"
        }

        payload = 'authentication_type=two_step&ticket_uuid=' + ticket_uuid \
                  + '&code=' + code + '&client_id=' + self.login_client_id
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
            "Accept-Encoding": "gzip",
            "X-Requested-With": "com.snei.vue.atv"
        }

        r = requests.delete(url, headers=headers, cookies=self.load_cookies(), verify=self.verify)
        self.save_cookies(r.cookies)
        # Clear addon settings
        self.addon.setSetting(id='EPGreqPayload', value='')
        self.addon.setSetting(id='reqPayload', value='')
        self.addon.setSetting(id='last_auth', value='')
        self.addon.setSetting(id='npsso', value='')
        self.addon.setSetting(id='default_profile', value='')

    def get_grant_code(self):
        url = self.api_url + '/oauth/authorize'
        url += '?request_theme=tv'
        url += '&ui=ds'
        url += '&client_id=' + self.req_client_id
        url += '&hidePageElements=noAccountSection'
        url += '&redirect_uri=' + urllib.quote_plus(self.themis)
        url += '&request_locale=en'
        url += '&response_type=code'
        url += '&resolution=1080'
        url += '&scope=psn%3As2s'
        url += '&service_logo=ps'
        url += '&smcid=tv%3Apsvue'
        url += '&duid=' + self.device_id

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US",
            "User-Agent": self.ua_android_tv,
            "Connection": "Keep-Alive",
            "X-Requested-With": "com.snei.vue.atv"
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
        url = 'https://sentv-user-auth.totsuko.tv/sentv_user_auth/ws/auth2/token'
        url += '?device_type_id=' + self.device_type
        url += '&device_id=' + self.device_id
        url += '&code=' + self.get_grant_code()
        url += '&redirect_uri=' + urllib.quote_plus(self.themis)

        headers = {
            'Origin': 'https://themis.dl.playstation.net',
            'User-Agent': self.ua_android_tv,
            'Accept': '*/*',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            "X-Requested-With": "com.snei.vue.atv"
        }
        if self.addon.getSetting(id='reqPayload') != '':
            headers['reauth'] = '1'
            headers['reqPayload'] = self.addon.getSetting(id='reqPayload')

        r = requests.get(url, headers=headers, verify=self.verify)
        device_status = str(r.json()['body']['status'])

        if device_status == "UNAUTHORIZED":
            auth_error = str(r.json()['header']['error']['message'])
            error_code = str(r.json()['header']['error']['code'])
            self.notification_msg("Error Code: " + error_code, auth_error)
            sys.exit()
        elif 'reqPayload' in r.headers:
            req_payload = str(r.headers['reqPayload'])
            self.addon.setSetting(id='reqPayload', value=req_payload)
            auth_time = r.json()['header']['time_stamp']
            self.addon.setSetting(id='last_auth', value=auth_time)
            if self.addon.getSetting(id='default_profile') != "":
                self.set_profile(self.addon.getSetting(id='default_profile'))
            else:
                self.get_profiles()
        else:
            self.notification_msg(self.localized(30207), self.localized(30209))
            sys.exit()

    def get_profiles(self):
        url = 'https://sentv-user-ext.totsuko.tv/sentv_user_ext/ws/v2/profile/ids'
        headers = {
            'User-Agent': self.ua_android_tv,
            'reqPayload': self.addon.getSetting(id='reqPayload'),
            'Accept': '*/*',
            'Origin': 'https://themis.dl.playstation.net',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            "X-Requested-With": "com.snei.vue.atv"
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
            'User-Agent': self.ua_android_tv,
            'reqPayload': self.addon.getSetting(id='reqPayload'),
            'Accept': '*/*',
            'Origin': 'https://themis.dl.playstation.net',
            'Host': 'sentv-user-ext.totsuko.tv',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            "X-Requested-With": "com.snei.vue.atv"
        }

        r = requests.get(url, headers=headers, verify=self.verify)
        EPGreqPayload = str(r.headers['reqPayload'])
        self.addon.setSetting(id='EPGreqPayload', value=EPGreqPayload)
        auth_time = r.json()['header']['time_stamp']
        self.addon.setSetting(id='last_auth', value=auth_time)
        self.addon.setSetting(id='default_profile', value=profile_id)

    def add_to_favorites(self, fav_type, ids):
        url = self.user_action_url + '/favorite'
        headers = {"Accept": "*/*",
                   "Content-type": "application/json",
                   "Origin": "https://vue.playstation.com",
                   "Referer": "https://vue.playstation.com/watch/home",
                   "Accept-Language": "en-US,en;q=0.8",
                   "Accept-Encoding": "gzip, deflate, br",
                   "User-Agent": self.ua_android_tv,
                   "Connection": "Keep-Alive",
                   "reqPayload": self.addon.getSetting(id='EPGreqPayload'),
                   "X-Requested-With": "com.snei.vue.atv"
                   }

        if fav_type == 'channel':
            location = self.addon.getLocalizedString(30102)
            payload = '{"channel_id":' + ids['channel_id'] + '}'
        else:
            location = self.addon.getLocalizedString(30101)
            payload = '{"program_id":' + ids['program_id'] + ',"series_id":' + ids['series_id'] \
                      + ',"tms_id":"' + ids['tms_id'] + '"}'

        r = requests.post(url, headers=headers, cookies=self.load_cookies(), data=payload, verify=self.verify)

        if r.status_code == 200:
            self.notification_msg("Success!", "Added to " + location)
        else:
            self.notification_msg("Fail", "Not added")

    def remove_from_favorites(self, fav_type, ids):
        url = self.user_action_url + '/favorite'
        headers = {"Accept": "*/*",
                   "Content-type": "application/json",
                   "Origin": "https://vue.playstation.com",
                   "Referer": "https://vue.playstation.com/watch/home",
                   "Accept-Language": "en-US,en;q=0.8",
                   "Accept-Encoding": "gzip, deflate, br",
                   "User-Agent": self.ua_android_tv,
                   "Connection": "Keep-Alive",
                   "reqPayload": self.addon.getSetting(id='EPGreqPayload'),
                   "X-Requested-With": "com.snei.vue.atv"
                   }

        if fav_type == 'channel':
            location = self.addon.getLocalizedString(30102)
            payload = '{"channel_id":' + ids['channel_id'] + '}'
        else:
            location = self.addon.getLocalizedString(30101)
            payload = '{"program_id":' + ids['program_id'] + ',"series_id":' + ids['series_id'] \
                      + ',"tms_id":"' + ids['tms_id'] + '"}'

        msg = 'Are you sure you want to remove this from ' + location + '?'
        dialog = xbmcgui.Dialog()
        remove = dialog.yesno(location, msg)
        if remove:
            r = requests.delete(url, headers=headers, cookies=self.load_cookies(), data=payload, verify=self.verify)

            if r.status_code == 200:
                self.notification_msg("Success!", "Removed from " + location)
            else:
                self.notification_msg("Fail", "Not added")

    def put_resume_time(self, airing_id, channel_id, program_id, series_id, tms_id, res_time, cur_time, watched):
        url = self.user_action_url + '/watch_history'
        headers = {'Accept': '*/*',
                   'Content-type': 'application/json',
                   'Origin': 'https://vue.playstation.com',
                   'Accept-Language': 'en-US,en;q-0.5',
                   'Referer': 'https://vue.playstation.com/watch/my-vue',
                   'Accept-Encoding': 'gzip, deflate, br',
                   'User-Agent': self.ua_android_tv,
                   'Connection': 'Keep-Alive',
                   'Host': 'sentv-user-action.totsuko.tv',
                   'reqPayload': self.addon.getSetting(id='EPGreqPayload'),
                   'X-Requested-With': 'com.snei.vue.android'
                   }

        payload = '{"series_id":' + series_id + ','
        payload += '"program_id":' + program_id + ','
        payload += '"channel_id":' + channel_id + ','
        payload += '"tms_id":"' + tms_id + '",'
        payload += '"airing_id":' + airing_id + ','
        payload += '"last_watch_date":' + '"' + cur_time + '"' + ','
        payload += '"last_timecode":' + '"' + res_time + '"' + ','
        payload += '"start_timecode":"00:00:00:00",'
        payload += '"fully_watched":' + watched + ','
        payload += '"stream_type":"null"}'

        requests.put(url, headers=headers, data=payload, verify=self.verify)

    def save_cookies(self, cookiejar):
        addon_profile_path = xbmc.translatePath(self.addon.getAddonInfo('profile'))
        cookie_file = os.path.join(addon_profile_path, 'cookies.lwp')
        cj = cookielib.LWPCookieJar()
        try:
            cj.load(cookie_file, ignore_discard=True)
        except:
            pass
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

    def valid_cookie(self, cookie_name):
        valid_cookie = False
        addon_profile_path = xbmc.translatePath(self.addon.getAddonInfo('profile'))
        try:
            cj = cookielib.LWPCookieJar()
            cj.load(os.path.join(addon_profile_path, 'cookies.lwp'), ignore_discard=True)
            for cookie in cj:
                if cookie.name == cookie_name:
                    xbmc.log('Cookie Expired? ' + str(cookie.is_expired()))
                    if not cookie.is_expired():
                        valid_cookie = True
                    if cookie_name == '_abck' and '~0~' not in str(cookie.value):
                        xbmc.log('Cookie Value: ' + str(cookie.value))
                        valid_cookie = False
                    break


        except:
            pass

        xbmc.log('Is cookie valid? '+ str(valid_cookie))
        return valid_cookie

    def notification_msg(self, title, msg):
        dialog = xbmcgui.Dialog()
        dialog.notification(title, msg, xbmcgui.NOTIFICATION_INFO, 9000)

    def sign(self, cs, api):
        temp_string = ""
        cs_length = len(cs)
        api_length = len(api)

        if api_length > 0:
            for index in range(0, cs_length):
                temp_char = cs[index]
                temp_code = ord(temp_char)
                temp_code_2 = ord(api[index % api_length])
                new_code = self.get_code(temp_code, 47, 57, temp_code_2)
                new_char = ""
                if new_code != cs[index]:
                    new_char = chr(new_code)
                    try:
                        temp_string += new_char
                    except:
                        xbmc.log("Unprintable character => %s" % new_char)

                xbmc.log("Index: %i\tCharacter %i:%s\t\tModulus %i\t\tModulus Code %i:%s\t\tNew Code %i:%s" %
                         (index, temp_code, temp_char, (index % api_length), temp_code_2, chr(temp_code_2), new_code,
                          new_char))
        else:
            xbmc.log("Signature cannot be blank")

        # xbmc.log("\r\nTarget Signature: 7a74G7m23Vrp0o5c")
        xbmc.log("Result signature: %s" % temp_string[0:16])

        return temp_string[0:16]

    def get_code(self, char_code, const_1, const_2, char_result):
        if const_1 < char_code <= const_2:
            char_code += char_result % (const_2 - const_1)
            if char_code > const_2:
                char_code = char_code - const_2 + const_1

        return char_code

    def get_sensor_data(self, cookie):
        CS_KEY = "0a46G5m17Vrp4o4c"
        API_KEY = "afSbep8yjnZUjq3aL010jO15Sawj2VZfdYK8uY90uxq"
        VERSION = "1.41"
        USER_AGENT = self.ua_browser
        REQUEST_INFO = "12147"
        PRODUCT_SUB = "20030107"
        LANGUAGE = "en-US"
        ENGINE = "Gecko"
        PLUGIN_COUNT = "3"
        HEADLESS = "0"
        NEW_WINDOW = "0"
        SPAM_BOT = "0"
        AVAIL_WIDTH = "1920"
        AVAIL_HEIGHT = "1040"
        SCREEN_WIDTH = "1920"
        SCREEN_HEIGHT = "1080"
        WINDOW_WIDTH = "1920"
        WINDOW_HEIGHT = "937"
        WINDOW_OWIDTH = "1920"
        IS_IE = "0"
        DOC_MODE = "1"
        CHROME_WEB_STORE = "0"
        ON_LINE = "1"
        OPERA = "0"
        FIREFOX = "0"
        SAFARI = "0"
        RTC_SUPPORT = "1"
        WINDOW_TOP = "0"
        VIBRATION = "1"
        BATTERY = "1"
        FOR_EACH = "0"
        FILE_READER = "1"
        ORIENTATION = "do_en"
        MOTION = "dm_en"
        TOUCH = "t_en"
        INFORM_INFO = ""
        FORM_INFO = ""
        K_ACT = ""
        M_ACT = ""
        T_ACT = ""
        DO_ACT = ""
        DM_ACT = ""
        P_ACT = ""
        VC_ACT = ""
        AJ_TYPE = "0"
        AJ_INDEX = "0"
        MN_R = ""
        FP_VALUE = "-1"

        url = "https://id.sonyentertainmentnetwork.com/signin/#/signin?entry=%2Fsignin"

        signature = self.sign(CS_KEY, API_KEY)
        date_floor = int(math.floor(int(time.time() * 1000) / 36e5))
        signature += self.sign(str(date_floor), signature)

        timestamp = int(time.time() * 1000)
        time_calc = int(timestamp / (2016 * 2016))
        time_calc2 = int(timestamp % 1e7)
        time_calc3 = int(time_calc / 23)
        time_calc4 = int(time_calc3 / 6)
        xbmc.Monitor().waitForAbort(.25)
        time_calc5 = int(time.time() * 1000) - timestamp

        #xbmc.log("Dated Signature: %s" % signature)

        sensor_string = \
            VERSION + "-1,2,-94,-100," + USER_AGENT + ",uaend," + REQUEST_INFO + "," + PRODUCT_SUB + "," + \
            LANGUAGE + "," + ENGINE + "," + PLUGIN_COUNT + "," + HEADLESS + "," + NEW_WINDOW + "," + \
            SPAM_BOT + "," + str(time_calc) + "," + str(time_calc2) + "," + AVAIL_WIDTH + "," + AVAIL_HEIGHT + \
            "," + SCREEN_WIDTH + "," + SCREEN_HEIGHT + "," + WINDOW_WIDTH + "," + WINDOW_HEIGHT + "," + \
            WINDOW_OWIDTH + ",,cpen:" + HEADLESS + ",i1:" + IS_IE + ",dm:" + DOC_MODE + ",cwen:" + \
            CHROME_WEB_STORE + ",non:" + ON_LINE + ",opc:" + OPERA + ",fc:" + FIREFOX + ",sc:" + SAFARI + \
            ",wrc:" + RTC_SUPPORT + ",isc:" + WINDOW_TOP + ",vib:" + VIBRATION + ",bat:" + BATTERY + ",x11:" + \
            FOR_EACH + ",x12:" + FILE_READER + "," + str(self.txt_func(USER_AGENT)) + "," + str(random.random())[0:13] + \
            "," + str(timestamp / 2) + ",loc:" + "-1,2,-94,-101" + "," + ORIENTATION + "," + MOTION + "," + \
            TOUCH + "-1,2,-94,-105," + INFORM_INFO + "-1,2,-94,-102," + FORM_INFO + "-1,2,-94,-108," + \
            K_ACT + "-1,2,-94,-110," + M_ACT + "-1,2,-94,-117," + T_ACT + "-1,2,-94,-111," + DO_ACT + \
            "-1,2,-94,-109," + DM_ACT + "-1,2,-94,-114," + P_ACT + "-1,2,-94,-103," + VC_ACT + \
            "-1,2,-94,-112," + url + "-1,2,-94,-115," + "1,1,0,0,0,0,0,1,0," + str(timestamp) + ",-999999," + \
            str(time_calc3) + "," + "0," + "0," + str(time_calc4) + ",0" + ",0" + "," + str(time_calc5) + \
            ",0" + ",0" + "," + cookie + "," + str(self.txt_func(cookie)) + ",-1" + ",-1" + ",30261693" + \
            "-1,2,-94,-106," + AJ_TYPE + "," + AJ_INDEX + "-1,2,-94,-119," + "-1" + \
            "-1,2,-94,-122," + "0,0,0,0,1,0,0" + "-1,2,-94,-123," + MN_R

        txt_val = self.txt_func(sensor_string)

        sensor_string += "-1,2,-94,-70," + FP_VALUE + "-1,2,-94,-80," + \
                         str(self.txt_func(FP_VALUE)) + "-1,2,-94,-116," + str(self.time_func(time_calc2)) + \
                         "-1,2,-94,-118," + str(txt_val) + "-1,2,-94,-121,"

        sensor_string = signature + sensor_string + ";" + str(int(time.time() * 1000) - timestamp) + ";-1;0"

        sensor_string = '{"sensor_data":"' + sensor_string + '"}'

        #xbmc.log("Sensor String:\n%s" % sensor_string)

        return sensor_string

    def txt_func(self, agent):
        result = -1
        if agent != "":
            try:
                temp_result = 0
                for index in range(0, len(agent)):
                    temp_code = ord(agent[index])
                    if temp_code < 128:
                        temp_result += temp_code
                result = temp_result
            except:
                result = -1

        return str(result)

    def time_func(self, timestamp):
        temp_val = timestamp
        for index in range(0, 5):
            temp_val2 = int(temp_val / math.pow(10, index)) % 10
            temp_val3 = temp_val2 + 1
            operator = self.get_operator(temp_val3)
            if operator == "+":
                temp_val += temp_val3
            elif operator == "-":
                temp_val -= temp_val3
            elif operator == "*":
                temp_val *= temp_val3
            elif operator == "/":
                temp_val /= temp_val3

        return temp_val

    def get_operator(self, temp_val):
        temp_result = temp_val % 4
        if temp_result == 2:
            temp_result = 3
        result = 42 + temp_result

        return str(result)
