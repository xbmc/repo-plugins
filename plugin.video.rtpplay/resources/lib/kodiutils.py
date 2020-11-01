# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import sys
import os
import logging
import json as json

PY3 =  sys.version_info > (3, 0)

if PY3:
    from html.parser import HTMLParser
else:
    from HTMLParser import HTMLParser


# read settings
ADDON = xbmcaddon.Addon()

if PY3:
    ICON = xbmcvfs.translatePath(ADDON.getAddonInfo("icon"))
    FANART = xbmcvfs.translatePath(ADDON.getAddonInfo("fanart"))
else:
    ICON = xbmc.translatePath(ADDON.getAddonInfo("icon"))
    FANART = xbmc.translatePath(ADDON.getAddonInfo("fanart"))

logger = logging.getLogger(__name__)


class HTMLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        if PY3:
            self.strict = False
            self.convert_charrefs = True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_html_tags(html):
    s = HTMLStripper()
    s.feed(html)
    return s.get_data()

def compat_py23str(x):
    if PY3:
        return str(x)
    else:
        if isinstance(x, unicode):
            try:
                return unicode(x).encode("utf-8")
            except UnicodeEncodeError:
                try:
                    return unicode(x).encode("utf-8")
                except:
                   return str(x)
        else:
            return str(x)


def ok(heading, line1, line2="", line3=""):
    xbmcgui.Dialog().ok(heading, line1, line2, line3)


def notification(header, message, time=5000, icon=ADDON.getAddonInfo('icon'), sound=True):
    xbmcgui.Dialog().notification(header, message, icon, time, sound)


def show_settings():
    ADDON.openSettings()


def get_setting(setting):
    return ADDON.getSetting(setting).strip()

def set_setting(setting, value):
    ADDON.setSetting(setting, str(value))


def get_setting_as_bool(setting):
    return get_setting(setting).lower() == "true"


def get_setting_as_float(setting):
    try:
        return float(get_setting(setting))
    except ValueError:
        return 0


def get_setting_as_int(setting):
    try:
        return int(get_setting_as_float(setting))
    except ValueError:
        return 0


def get_string(string_id):
    return compat_py23str(ADDON.getLocalizedString(string_id))


def kodi_json_request(params):
    data = json.dumps(params)
    request = xbmc.executeJSONRPC(data)

    try:
        response = json.loads(request)
    except UnicodeDecodeError:
        response = json.loads(request.decode('utf-8', 'ignore'))

    try:
        if 'result' in response:
            return response['result']
        return None
    except KeyError:
        logger.warn("[%s] %s" %
                    (params['method'], response['error']['message']))
        return None
