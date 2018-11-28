# -*- coding: utf-8 -*-

import json
import os
import re
import urllib
import xbmc
import xbmcaddon
import xbmcgui

from .sources.local import LOCAL
from .sources.imvdb import IMVDB
from .sources.youtube import YT

class Common:

    def __init__(self, addon_handle=None, addon_url=None):
        self.addon = xbmcaddon.Addon()
        self.addon_handle = addon_handle
        self.addon_url = addon_url
        self.addon_id = self.addon.getAddonInfo('id')
        self.addon_name = self.addon.getAddonInfo('name')
        self.addon_version = self.addon.getAddonInfo('version')
        self.addon_icon = self.addon.getAddonInfo('icon')
        self.addon_fanart = self.addon.getAddonInfo('fanart')
        self.datapath = self.utfdec(xbmc.translatePath(self.addon.getAddonInfo('profile')))

    def log(self, msg):
        xbmc.log(str(msg), xbmc.LOGDEBUG)

    def build_url(self, query):
        return self.addon_url + '?' + urllib.urlencode(query)

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

    def tostr(self, var):
        result = var
        if isinstance(var, int):
            result = str(var)
        return result
            
    def get_addon(self):
        return self.addon

    def get_dialog(self):
        return xbmcgui.Dialog()

    def set_setting(self, key, value):
        return self.get_addon().setSetting(key, value)

    def get_setting(self, key):
        return self.get_addon().getSetting(key)

    def get_string(self, id_):
        return self.utfenc(self.get_addon().getLocalizedString(id_))

    def dialog_ok(self, id_):
        self.get_dialog().ok(self.addon_name, self.get_string(id_))

    def notification(self, title, msg, thumb, duration):
        self.get_dialog().notification(title, msg, thumb, duration)

    def file_path(self, file_name):
        return os.path.join(self.datapath, file_name)

    def enter_artist(self):
        artist = None
        artist = self.get_dialog().input(self.get_string(30101), type=xbmcgui.INPUT_ALPHANUM)
        return artist

    def sites(self):
        sites = [
            ('local', 'true'),
            ('imvdb', self.get_setting('imvdb')),
            ('youtube', self.get_setting('youtube'))
        ]
        sites = [i[0] for i in sites if i[1] == 'true']
        return sites

    def import_site(self, site, plugin):
        if site == 'local':
            return LOCAL(plugin)
        elif site == 'imvdb':
            return IMVDB(plugin)
        elif site == 'youtube':
            return YT(plugin)

    def standardize_title(self, title):
        title = self.utfenc(title)
        title = title.replace('[', '(').replace('【', '(')
        title = title.replace(']', ')').replace('】', ')')
        title = title.replace('’', '\'').replace('´', '\'').replace('`', '\'')
        title = re.sub('lyric video\s*$|\(lyric video\)|\(official lyric video\)|\(lyric version\)|\(lyrics\)', '(Lyric Video)', title, flags=re.I)
        return title

    def clean_title(self, title):
        title = self.standardize_title(title)
        title = re.sub('\(.*?[^(]official.*?\)|video\s*-\s*dvd|\(video\)|\(visual\)|official.*(?:video|clip)|offizielles\s*video|official\s*dvd|official\s*video\s*hd|official\s*music\s*video|music\s*video|download\s*link', '', title, flags=re.I)
        title = re.sub('"|\'|\”|\“|\‘|PV\s*$|MV\s*|M/V\s*|hd|hq|1080p|720p|4k|\d+\s*fps|\s*new\!\s*$|widescreen|(?:\s*|\.).flv|full\s*(?:size|version|ver.)|\(full\)|music\s*clip', '', title, flags=re.I)
        title = re.sub('high quality|  quality\s*$|\s*\+\s*download|\s*\d{4}\s*$', '', title, flags=re.I)
        title = re.sub('\(\s*\)|\(\s*$|\+\s*$', '', title, flags=re.I)
        title = re.sub('(?:--\s*$|-\s*$)', '', title, flags=re.I)
        title = re.sub('\s{2}', ' ', title, flags=re.I)
        return title.strip()
