# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import json as json

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")


def notification(header, message, time=5000, icon=ADDON.getAddonInfo('icon'), sound=True):
    xbmcgui.Dialog().notification(header, message, icon, time, sound)


def show_settings():
    ADDON.openSettings()


def log(message,level):
    prefix = b"[%s] " % ADDON_ID
    formatter = prefix + b'%(name)s: %(message)s'
    try:
        xbmc.log(formatter, level)
    except UnicodeEncodeError:
        xbmc.log(formatter.encode(
            'utf-8', 'ignore'), level)


def get_setting(setting):
    return ADDON.getSetting(setting).strip().decode('utf-8')


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
    return ADDON.getLocalizedString(string_id).encode('utf-8', 'ignore')


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
        log("[%s] %s" %
                    (params['method'], response['error']['message']),level=xbmc.LOGWARNING)
        return None

def add_sort_methods(handle):
    sort_methods = [xbmcplugin.SORT_METHOD_UNSORTED, xbmcplugin.SORT_METHOD_LABEL,
                    xbmcplugin.SORT_METHOD_DATE, xbmcplugin.SORT_METHOD_DURATION,
                    xbmcplugin.SORT_METHOD_EPISODE]
    for method in sort_methods:
        xbmcplugin.addSortMethod(handle, sortMethod=method)
    return