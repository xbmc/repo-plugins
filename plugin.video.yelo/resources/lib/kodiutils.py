# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
import json
import logging
import xbmc
import xbmcaddon
import xbmcgui

# read settings
ADDON = xbmcaddon.Addon()

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)


def notification(header, message, time=5000, icon=ADDON.getAddonInfo('icon'), sound=True):
    xbmcgui.Dialog().notification(header, message, icon, time, sound)


def show_settings():
    ADDON.openSettings()


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


def kodi_version():
    """Returns full Kodi version as string"""
    return xbmc.getInfoLabel('System.BuildVersion').split(' ')[0]


def kodi_version_major():
    """Returns major Kodi version as integer"""
    return int(kodi_version().split('.')[0])


def kodi_json_request(params):
    data = json.dumps(params)
    request = xbmc.executeJSONRPC(data)

    try:
        response = json.loads(request)
    except UnicodeDecodeError:
        response = json.loads(request.decode('utf-8', 'ignore'))

    result = response.get('result')
    if result is None:
        _LOGGER.debug("[%s] %s", params['method'], response['error']['message'])

    return result
