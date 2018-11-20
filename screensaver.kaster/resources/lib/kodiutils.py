# -*- coding: utf-8 -*-
"""
    screensaver.kaster
    Copyright (C) 2017 enen92

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import xbmc
import xbmcaddon
import xbmcgui
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
    try:
        return ADDON.getSetting(setting).strip().decode('utf-8')
    except AttributeError:
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
