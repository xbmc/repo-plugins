# -*- coding: utf-8 -*-

import base64
import datetime
import hashlib
import json
import os
import string
import time
import urllib
import uuid
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import _strptime
from inputstreamhelper import Helper

class Common:

    def __init__(self, addon_handle=None, addon_url=None):
        self.api_base = 'https://isl.dazn.com/misl/'
        self.time_format = '%Y-%m-%dT%H:%M:%SZ'
        self.date_format = '%Y-%m-%d'
        self.portability_list = ['AT', 'DE', 'IT', 'ES']

        self.addon = xbmcaddon.Addon()
        self.addon_handle = addon_handle
        self.addon_url = addon_url
        self.addon_id = self.addon.getAddonInfo('id')
        self.addon_name = self.addon.getAddonInfo('name')
        self.addon_version = self.addon.getAddonInfo('version')
        self.addon_icon = self.addon.getAddonInfo('icon')
        self.addon_fanart = self.addon.getAddonInfo('fanart')
        self.content = self.addon.getSetting('content')
        self.view_id = self.addon.getSetting('view_id')
        self.view_id_videos = self.addon.getSetting('view_id_videos')
        self.view_id_epg = self.addon.getSetting('view_id_epg')
        self.force_view = self.addon.getSetting('force_view') == 'true'
        self.startup = self.addon.getSetting('startup') == 'true'
        self.select_cdn = self.addon.getSetting('select_cdn') == 'true'
        self.preferred_cdn = self.addon.getSetting('preferred_cdn')
        self.max_bw = self.addon.getSetting('max_bw')

    def log(self, msg):
        xbmc.log(str(msg), xbmc.LOGDEBUG)

    def build_url(self, query):
        return self.addon_url + '?' + urllib.urlencode(query)

    def gui_language(self):
        language = xbmc.getLanguage().split(' (')[0]
        return xbmc.convertLanguage(language, xbmc.ISO_639_1)

    def get_addon(self):
        return self.addon

    def get_datapath(self):
        return self.utfdec(xbmc.translatePath(self.get_addon().getAddonInfo('profile')))

    def get_filepath(self, file_name):
        if file_name.startswith('http'):
            file_name = file_name.split('/')[-1]
        return os.path.join(self.get_datapath(), file_name)

    def get_dialog(self):
        return xbmcgui.Dialog()

    def set_setting(self, key, value):
        return self.get_addon().setSetting(key, value)

    def get_setting(self, key):
        return self.get_addon().getSetting(key)

    def get_string(self, id_):
        return self.utfenc(self.get_addon().getLocalizedString(id_))

    def dialog_ok(self, msg):
        self.get_dialog().ok(self.addon_name, msg)

    def dialog_yesno(self, msg):
        return self.get_dialog().yesno(self.addon_name, msg)

    def notification(self, title, msg, thumb, duration):
        self.get_dialog().notification(title, msg, thumb, duration)

    def utfenc(self, text):
        result = text
        if isinstance(text, unicode):
            result = text.encode('utf-8')
        return result

    def utfdec(self, text):
        result = text
        if isinstance(text, str):
            result = text.decode('utf-8')
        return result

    def b64dec(self, data):
        missing_padding = len(data) % 4
        if missing_padding != 0:
            data += b'='* (4 - missing_padding)
        return base64.b64decode(data)

    def get_resource(self, text, prefix=''):
        data = self.get_cache('ResourceStrings')
        if data.get('Strings'):
            strings = data['Strings']
            try:
                text = strings['{0}{1}'.format(prefix, text.replace(' ', ''))]
            except KeyError:
                text = text.replace('_',' ')
        return self.utfenc(self.initcap(text))

    def get_credentials(self):
        email = self.get_dialog().input(self.get_resource('signin_emaillabel'), type=xbmcgui.INPUT_ALPHANUM)
        if '@' in email:
            password = self.get_dialog().input(self.get_resource('signin_passwordlabel'), type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
            if len(password) > 4:
                return {
                    'email': email,
                    'password': password
                }
        return {}

    def logout(self):
        return self.dialog_yesno(self.get_resource('signout_body'))

    def time_now(self):
        return datetime.datetime.now().strftime(self.time_format)

    def time_stamp(self, str_date):
        return datetime.datetime.fromtimestamp(time.mktime(time.strptime(str_date, self.time_format)))

    def timedelta_total_seconds(self, timedelta):
        return (
            timedelta.microseconds + 0.0 +
            (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) / 10 ** 6

    def utc2local(self, date_string):
        if str(date_string).startswith('2'):
            utc = datetime.datetime(*(time.strptime(date_string, self.time_format)[0:6]))
            epoch = time.mktime(utc.timetuple())
            offset = datetime.datetime.fromtimestamp(epoch) - datetime.datetime.utcfromtimestamp(epoch)
            return (utc + offset).strftime(self.time_format)

    def uniq_id(self):
        device_id = ''
        mac_addr = xbmc.getInfoLabel('Network.MacAddress')
        if not ":" in mac_addr:
            mac_addr = xbmc.getInfoLabel('Network.MacAddress')
        # hack response busy
        i = 0
        while not ":" in mac_addr and i < 3:
            i += 1
            time.sleep(1)
            mac_addr = xbmc.getInfoLabel('Network.MacAddress')
        if ":" in mac_addr:
            device_id = str(uuid.UUID(hashlib.md5(str(mac_addr.decode("utf-8"))).hexdigest()))
        elif self.get_setting('device_id'):
            device_id = self.get_setting('device_id')
        else:
            self.log("[{0}] error: failed to get device id ({1})".format(self.addon_id, str(mac_addr)))
            self.dialog_ok(self.get_resource('error_4005_ConnectionLost'))
        self.set_setting('device_id', device_id)
        return device_id

    def open_is_settings(self):
        xbmcaddon.Addon(id='inputstream.adaptive').openSettings()

    def start_is_helper(self):
        helper = Helper(protocol='mpd', drm='widevine')
        return helper.check_inputstream()

    def days(self, title, now, start):
        today = datetime.date.today()
        if start and not title == 'Live':
            if now[:10] == start[:10]:
                return self.get_resource('tileLabelToday', 'browseui_')
            elif str(today + datetime.timedelta(days=1)) == start[:10]:
                return self.get_resource('tileLabelTomorrow', 'browseui_')
            else:
                for i in range(2,8):
                    if str(today + datetime.timedelta(days=i)) == start[:10]:
                        return self.get_resource((today + datetime.timedelta(days=i)).strftime('%A'), 'calendar_')
        return self.get_resource(title, 'browseui_')

    def epg_date(self, date):
        return datetime.datetime.fromtimestamp(time.mktime(time.strptime(date, self.date_format)))

    def get_prev_day(self, date):
        return (date - datetime.timedelta(days=1))

    def get_next_day(self, date):
        return (date + datetime.timedelta(days=1))

    def get_date(self):
        date = 'today'
        dlg = self.get_dialog().numeric(1, self.get_string(30230))
        if dlg:
            spl = dlg.split('/')
            date = '%s-%s-%s' % (spl[2], spl[1], spl[0])
        return date

    def get_mpx(self, token):
        token_data = json.loads(self.b64dec(token.split('.')[1]))
        return token_data['mpx']

    def language(self, language, languages):
        gui_lang = self.gui_language()
        for i in languages:
            if i.lower() == gui_lang.lower():
                language = i
                break
        return language

    def portability_country(self, country, user_country):
        if user_country in self.portability_list:
            country = user_country
        return country

    def get_cache(self, file_name):
        json_data = {}
        file_ = self.get_filepath(file_name)
        if xbmcvfs.exists(file_):
            try:
                f = xbmcvfs.File(file_, 'r')
                json_data = json.load(f)
                f.close()
            except Exception as e:
                self.log("[{0}] get cache error: {1}".format(self.addon_id, e))
        return json_data

    def cache(self, file_name, data):
        file_ = self.get_filepath(file_name)
        try:
            f = xbmcvfs.File(file_, 'w')
            json.dump(data, f)
            f.close()
        except Exception as e:
            self.log("[{0}] cache error: {1}".format(self.addon_id, e))

    def split_on_uppercase(self, s, keep_contiguous=False):
        string_length = len(s)
        is_lower_around = (lambda: s[i-1].islower() or 
                           string_length > (i + 1) and s[i + 1].islower())

        start = 0
        parts = []
        for i in range(1, string_length):
            if s[i].isupper() and (not keep_contiguous or is_lower_around()):
                parts.append(s[start: i])
                start = i
        parts.append(s[start:])

        return parts

    def initcap(self, text):
        if text.isupper() and len(text) > 3:
            text = string.capwords(text)
            text = text.replace('Dazn', 'DAZN')
        elif not text.isupper() and not ' ' in text:
            parts = self.split_on_uppercase(text, True)
            text = ' '.join(parts)
        return text

    def get_cdn(self, cdns):
        if self.select_cdn:
            ret = self.get_dialog().select(self.get_string(30023), cdns)
            if not ret == -1:
                self.preferred_cdn = cdns[ret]
                self.set_setting('preferred_cdn', self.preferred_cdn)
                self.set_setting('select_cdn', 'false')
        return self.preferred_cdn

    def validate_pin(self, pin):
        result = False
        if len(pin) == 4 and pin.isdigit():
            result = True
        return result

    def youth_protection_pin(self, verify_age):
        pin = ''
        if verify_age:
            pin = self.get_dialog().input(self.get_resource('youthProtectionTV_verified_body'), type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
        return pin
