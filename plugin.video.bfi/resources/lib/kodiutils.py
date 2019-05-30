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


def art(domain, image):
    return ({
                "thumb": "{}{}".format(domain, image.get("data-img-800", "")),
                "fanart": "{}{}".format(domain, image.get("data-img-1440", "")),
                "poster": "{}{}".format(domain, image.get("data-img-960", ""))
            } if "src" in image else {
        "thumb": "{}{}".format(domain, image),
        "fanart": "{}{}".format(domain, image),
        "poster": "{}{}".format(domain, image)
    })


def icon(image):
    return {"icon": translate_path("{}{}".format(MEDIA_URI, image))}


def user_input():
    keyboard = xbmc.Keyboard("",
                             "{} {}".format(get_string(32007),  # Search
                                            ADDON.getAddonInfo("name")))
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    return False


def confirm():
    return xbmcgui.Dialog().yesno("BFI Player", get_string(32023))  # Are you sure?


def notification(header, message, time=5000, image=ADDON.getAddonInfo("icon"), sound=True):
    xbmcgui.Dialog().notification(header, message, image, time, sound)


def translate_path(path):
    return xbmc.translatePath(path).decode("utf-8")


def show_settings():
    ADDON.openSettings()


def get_setting(setting):
    return ADDON.getSetting(setting).strip().decode("utf-8")


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
    return ADDON.getLocalizedString(string_id).encode("utf-8", "ignore")


def kodi_json_request(params):
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
        logger.warn("[%s] %s" %
                    (params["method"], response["error"]["message"]))
        return None
