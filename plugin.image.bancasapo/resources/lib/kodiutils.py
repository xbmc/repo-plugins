# -*- coding: utf-8 -*-
import xbmcaddon
from sys import version_info

PY3 = version_info > (3, 0)
ADDON = xbmcaddon.Addon()


def translate(string_id):
    if PY3:
        return ADDON.getLocalizedString(string_id)
    return ADDON.getLocalizedString(string_id).encode('utf-8')


def get_setting(setting):
    if PY3:
        return ADDON.getSetting(setting).strip()
    return ADDON.getSetting(setting).strip().decode('utf-8')


def get_setting_as_bool(setting):
    return get_setting(setting).lower() == "true"