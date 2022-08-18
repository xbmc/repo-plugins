# SPDX-License-Identifier: GPL-2.0-or-later
# Original plugin.video.mlbtv © eracknaphobia
# Modified for MiLB.TV compatibility and code cleanup

import requests
from resources.lib.utils import Util
from resources.lib.globals import *
from kodi_six import xbmc, xbmcaddon, xbmcgui
import time, uuid
import string
import random
import re

if sys.version_info[0] > 2:
    from urllib.parse import quote
else:
    from urllib import quote


class Account:
    addon = xbmcaddon.Addon()
    username = ''
    password = ''
    session_key = ''
    verify = True

    def __init__(self):
        self.username = self.addon.getSetting('username')
        self.password = self.addon.getSetting('password')
        self.session_key = self.addon.getSetting('session_key')
        self.util = Util()

    def login(self):
        # Check if username and password are provided
        if self.username == '':
            dialog = xbmcgui.Dialog()
            self.username = dialog.input(LOCAL_STRING(30405), type=xbmcgui.INPUT_ALPHANUM)
            self.addon.setSetting(id='username', value=self.username)

        if self.password == '':
            dialog = xbmcgui.Dialog()
            self.password = dialog.input(LOCAL_STRING(30406), type=xbmcgui.INPUT_ALPHANUM,
                                    option=xbmcgui.ALPHANUM_HIDE_INPUT)
            self.addon.setSetting(id='password', value=self.password)

        if self.username == '' or self.password == '':
            sys.exit()
        else:
            url = 'https://ids.milb.com/api/v1/authn'
            headers = {
                'User-Agent': UA_PC,
                'Accept-Encoding': 'identity',
                'Content-Type': 'application/json',
                'Referer': 'https://www.milb.com/',
                'Origin': 'https://www.milb.com'
            }
            payload = {
                'username': self.username,
                'password': self.password,
                'options': {
                    'multiOptionalFactorEnroll': False,
                    'warnBeforePasswordExpired': True
                }
            }

            r = requests.post(url, headers=headers, json=payload, verify=self.verify)
            if r.ok:
                login_token = r.json()['sessionToken']
                self.addon.setSetting('login_token', login_token)
                self.addon.setSetting('last_login', str(time.time()))
            else:
                dialog = xbmcgui.Dialog()
                title = LOCAL_STRING(30407)
                msg = LOCAL_STRING(30408)
                dialog.notification(title, msg, ICON, 5000, False)
                self.addon.setSetting('login_token', '')
                self.addon.setSetting('last_login', '')
                sys.exit()


    def logout(self):
        self.util.delete_cookies()
        self.addon.setSetting('login_token', '')
        self.addon.setSetting('last_login', '')
        self.addon.setSetting('access_token', '')
        self.addon.setSetting('last_access', '')
        self.addon.setSetting('username', '')
        self.addon.setSetting('password', '')

    def id_generator(self, size=64, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def access_token(self):
        if self.addon.getSetting('last_login') == '' or \
                (time.time() - float(self.addon.getSetting('last_login')) >= 86400):
            self.login()

        url = 'https://ids.milb.com/oauth2/aus9hfi7yyG0nCpgc356/v1/authorize?client_id=0oablr6l1aKpsXjZF356&redirect_uri=https%3A%2F%2Fwww.milb.com%2Flogin&response_type=id_token%20token&response_mode=okta_post_message&state=' + self.id_generator() + '&nonce=' + self.id_generator() + '&prompt=none&sessionToken=' + self.addon.getSetting('login_token') + '&scope=openid%20email'
        headers = {
            'User-Agent': UA_PC,
            'Accept-Encoding': 'identity',
            'Referer': 'https://www.milb.com/',
            'Origin': 'https://www.milb.com'
        }

        r = requests.get(url, headers=headers, verify=self.verify)
        if r.ok:
            if re.search("data.error = 'login_required'", r.text):
                return False
            else:
                x = re.findall("data.access_token = '([^']+)'", r.text)
                return x[0]

    def get_access_token(self):
        for x in range(0, 4):
            access_token = self.access_token()
            if ( access_token != False ):
                self.addon.setSetting('access_token', access_token)
                self.addon.setSetting('last_access', str(time.time()))
                return
        dialog = xbmcgui.Dialog()
        title = LOCAL_STRING(30409)
        msg = LOCAL_STRING(30408)
        dialog.notification(title, msg, ICON, 5000, False)
        self.addon.setSetting('access_token', '')
        self.addon.setSetting('last_access', '')
        sys.exit()

    def get_stream(self, game_pk):
        if self.addon.getSetting('last_access') == '' or \
                (time.time() - float(self.addon.getSetting('last_access')) >= 86400):
            self.get_access_token()

        url = 'https://services.mediaservices.mlbinfra.com/api/v1/playback/' + game_pk + '?sdp=WEB_MEDIAPLAYER'
        headers = {
            'Authorization': 'Bearer ' + self.addon.getSetting('access_token').replace("\\/", "/").encode().decode('unicode_escape'),
            'User-Agent': UA_PC,
            'Accept': '*/*',
            'Origin': 'https://www.milb.com',
            'Referer': 'https://www.milb.com/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-type': 'application/json'
        }

        r = requests.get(url, headers=headers, cookies=self.util.load_cookies(), verify=self.verify)
        if not r.ok:
            dialog = xbmcgui.Dialog()
            title = LOCAL_STRING(30410)
            msg = LOCAL_STRING(30411)
            dialog.notification(title, msg, ICON, 5000, False)
            sys.exit()

        stream_url = r.json()['data'][0]['value']

        if QUALITY == 'Always Ask':
            stream_url = self.get_stream_quality(stream_url)
        headers = 'User-Agent=' + UA_PC
        headers += '&Cookie='
        cookies = requests.utils.dict_from_cookiejar(self.util.load_cookies())
        if sys.version_info[0] <= 2:
            cookies = cookies.iteritems()
        for key, value in cookies:
            headers += key + '=' + value + '; '

        return stream_url, headers

    def get_stream_quality(self, stream_url):
        #Check if inputstream adaptive is on, if so warn user and return master m3u8
        if xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)') or (KODI_VERSION >= 19 and xbmc.getCondVisibility('System.AddonIsEnabled(inputstream.adaptive)')):
            dialog = xbmcgui.Dialog()
            dialog.ok(LOCAL_STRING(30370), LOCAL_STRING(30371))
            return stream_url

        stream_title = []
        stream_urls = []
        headers = {'User-Agent': UA_PC}

        r = requests.get(stream_url, headers=headers, verify=False)
        master = r.text

        line = re.compile("(.+?)\n").findall(master)

        for temp_url in line:
            if '#EXT' not in temp_url:
                match = re.findall('_(\d+)K.m3u8', temp_url, re.IGNORECASE)
                bandwidth = match[0] + ' kbps'
                stream_title.append(bandwidth)
                stream_urls.append(temp_url)

        stream_title.sort(key=self.util.natural_sort_key, reverse=True)
        stream_urls.sort(key=self.util.natural_sort_key, reverse=True)
        dialog = xbmcgui.Dialog()
        ret = dialog.select(LOCAL_STRING(30412), stream_title)
        if ret >= 0:
            if 'http' not in stream_urls[ret]:
                stream_url = stream_url.replace(stream_url.rsplit('/', 1)[-1], stream_urls[ret])
            else:
                stream_url = stream_urls[ret]
        else:
            sys.exit()

        return stream_url
