# -*- coding: utf-8 -*-

"""Kodi gui and settings helpers"""

__author__ = "fraser"

import logging
import os

import xbmc
import xbmcaddon
import xbmcgui

logger = logging.getLogger(__name__)

ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo("name")
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_PATH = ADDON.getAddonInfo("path")
MEDIA_URI = os.path.join(ADDON_PATH, "resources", "media")


def art(image):
    return {
        "thumb": image,
        "fanart": image,
        "poster": image
    }


def icon(image):
    # type (str) -> dict
    """Creates the application folder icon info for main menu items"""
    return {"icon": os.path.join(MEDIA_URI, image)}


def user_input():
    # type () -> Union[str, bool}
    keyboard = xbmc.Keyboard("", "{} {}".format(localize(32007), ADDON_NAME))  # search
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    return False


def confirm():
    # type () -> bool
    return xbmcgui.Dialog().yesno(ADDON_NAME, localize(32022))  # Are you sure?


def notification(header, message, time=5000, image=ADDON.getAddonInfo("icon"), sound=True):
    # type (str, str, int, str, bool) -> None
    xbmcgui.Dialog().notification(header, str(message), image, time, sound)


def show_settings():
    # type () -> None
    ADDON.openSettings()


def get_setting(setting):
    # type (str) -> str
    return ADDON.getSetting(setting).strip().decode("utf-8")


def set_setting(setting, value):
    # type (str, Any) -> None
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


def localize(string_id):
    # type (str) -> str
    return ADDON.getLocalizedString(string_id).encode("utf-8", "ignore")
