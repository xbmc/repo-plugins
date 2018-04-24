# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

import json as json
import logging

import xbmc
import xbmcaddon
import xbmcgui

# read settings
ADDON = xbmcaddon.Addon()
logger = logging.getLogger(__name__)

ADDON_ID = ADDON.getAddonInfo("id")
MEDIA_URI = "special://home/addons/{}/resources/media/".format(ADDON_ID)


def art(image):
    return {
        "thumb": image,
        "fanart": image,
        "poster": image
    }


def icon(image):
    # type (str) -> dict
    """Creates the application folder icon info for main menu items"""
    return {"icon": translate_path("{}{}".format(MEDIA_URI, image))}


def user_input():
    # type () -> Union[str, bool}
    keyboard = xbmc.Keyboard("",
                             "{} {}".format(get_string(32007),  # Search
                                            ADDON.getAddonInfo("name")))
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    return False


def confirm():
    # type () -> bool
    return xbmcgui.Dialog().yesno(ADDON.getAddonInfo("name"), get_string(32022))  # Are you sure?


def notification(header, message, time=5000, image=ADDON.getAddonInfo("icon"), sound=True):
    # type (str, str, int, str, bool) -> None
    xbmcgui.Dialog().notification(header, message, image, time, sound)


def translate_path(path):
    # type (str) -> str
    return xbmc.translatePath(path).decode("utf-8")


def show_settings():
    # type () -> None
    ADDON.openSettings()


def get_setting(setting):
    # type (str) -> str
    return ADDON.getSetting(setting).strip().decode("utf-8")


def set_setting(setting, value):
    # type (Any) -> None
    ADDON.setSetting(setting, str(value))


def get_setting_as_bool(setting):
    # type (str) -> bool
    return get_setting(setting).lower() == "true"


def get_setting_as_float(setting):
    # type (str) -> float
    try:
        return float(get_setting(setting))
    except ValueError:
        return 0


def get_setting_as_int(setting):
    # type (str) -> int
    try:
        return int(get_setting_as_float(setting))
    except ValueError:
        return 0


def get_string(string_id):
    # type (str) -> str
    return ADDON.getLocalizedString(string_id).encode("utf-8", "ignore")


def kodi_json_request(params):
    # type (str) -> str
    data = json.dumps(params)
    request = xbmc.executeJSONRPC(data)

    try:
        response = json.loads(request)
    except UnicodeDecodeError:
        response = json.loads(request.decode("utf-8", "ignore"))

    try:
        if "result" in response:
            return response["result"]
        return None
    except KeyError:
        logger.debug("[{}] {}".format(params["method"], response["error"]["message"]))
        return None
