# v.0.3.5

import xbmc
import xbmcaddon
import xbmcvfs

ADDON = xbmcaddon.Addon()
ADDONNAME = ADDON.getAddonInfo('id')
ADDONLONGNAME = ADDON.getAddonInfo('name')
ADDONVERSION = ADDON.getAddonInfo('version')
ADDONPATH = ADDON.getAddonInfo('path')
ADDONDATAPATH = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
ADDONICON = xbmcvfs.translatePath('%s/icon.png' % ADDONPATH)
ADDONLANGUAGE = ADDON.getLocalizedString
SKINNAME = xbmc.getSkinDir()


def _get_setting(setting_name, default, thetype="string"):
    if thetype.lower() == "bool":
        if ADDON.getSetting(setting_name).lower() == 'true':
            return True
        if ADDON.getSetting(setting_name).lower() == 'false':
            return False
        return default
    if thetype.lower() == "int":
        try:
            return int(ADDON.getSetting(setting_name))
        except ValueError:
            return default
    if thetype.lower() == "number":
        try:
            return float(ADDON.getSetting(setting_name))
        except ValueError:
            return default
    else:
        setting = ADDON.getSetting(setting_name)
        if setting:
            return setting
        else:
            return default


def getSettingBool(setting_name, default=False):
    return _get_setting(setting_name, default, 'bool')


def getSettingInt(setting_name, default=0):
    return _get_setting(setting_name, default, 'int')


def getSettingNumber(setting_name, default=0.0):
    return _get_setting(setting_name, default, 'number')


def getSettingString(setting_name, default=''):
    return _get_setting(setting_name, default, 'string')
