# -*- coding: utf-8 -*-
import xbmcaddon

ADDON = xbmcaddon.Addon()

def translate(string_id):
	return ADDON.getLocalizedString(string_id).encode('utf-8')

def get_setting(setting):
    return ADDON.getSetting(setting).strip().decode('utf-8')

def get_setting_as_bool(setting):
    return get_setting(setting).lower() == "true"