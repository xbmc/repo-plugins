# -*- coding: utf-8 -*-

"""Kodi gui and settings helpers"""

__author__ = "fraser"

import os

import xbmc
import xbmcaddon
import xbmcgui

ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo("name")
ADDON_PATH = ADDON.getAddonInfo("path")
MEDIA_URI = os.path.join(ADDON_PATH, "resources", "media")


def art(image):
    # type: (str) -> dict
    return {
        "icon": image.replace("368x207", "640x360"),
        "thumb": image.replace("368x207", "960x540"),
        "fanart": image.replace("368x207", "1920x1080"),
        "poster": image.replace("368x207", "1000x1500")
    }


def icon(image):
    # type: (str) -> dict
    """Creates the application folder icon info for main menu items"""
    return {"icon": os.path.join(MEDIA_URI, image)}


def user_input():
    # type: () -> Union[str, bool]
    keyboard = xbmc.Keyboard("", "{} {}".format(localize(32007), ADDON_NAME))  # search
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    return False


def confirm():
    # type: () -> bool
    return xbmcgui.Dialog().yesno(ADDON_NAME, localize(32022))  # Are you sure?


def notification(header, message, time=5000, image=ADDON.getAddonInfo("icon"), sound=True):
    # type: (str, str, int, str, bool) -> None
    xbmcgui.Dialog().notification(header, str(message), image, time, sound)


def show_settings():
    # type: () -> None
    ADDON.openSettings()


def get_setting(setting):
    # type: (str) -> str
    return ADDON.getSetting(setting).strip()


def set_setting(setting, value):
    # type: (str, Any) -> None
    ADDON.setSetting(setting, str(value))


def get_setting_as_bool(setting):
    # type: (str) -> bool
    return ADDON.getSettingBool(setting)


def get_setting_as_float(setting):
    # type: (str) -> float
    try:
        return ADDON.getSettingNumber(setting)
    except ValueError:
        return 0


def get_setting_as_int(setting):
    # type: (str) -> int
    try:
        return ADDON.getSettingInt(setting)
    except ValueError:
        return 0


def localize(token):
    # type: (int) -> str
    return ADDON.getLocalizedString(token).encode("utf-8", "ignore").decode("utf-8")
