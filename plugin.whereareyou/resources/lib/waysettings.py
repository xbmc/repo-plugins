
from resources.lib.kodisettings import *

SETTINGSLIST = [{'name': 'mappings', 'default': ''},
                {'name': 'harmonycontrol', 'default': False},
                {'name': 'hub_ip', 'default': ''},
                {'name': 'timeout', 'default': 30},
                {'name': 'delay', 'default': 250},
                {'name': 'harmonyadvanced', 'default': False},
                {'name': 'use_custom_skin_menu', 'default': True},
                {'name': 'include_skin_mods', 'default': True},
                {'name': 'version_upgrade', 'default': ''},
                {'name': 'debug', 'default': False}
                ]


def loadSettings():
    settings = {}
    settings['ADDON'] = ADDON
    settings['ADDONNAME'] = ADDONNAME
    settings['ADDONLONGNAME'] = ADDONLONGNAME
    settings['ADDONVERSION'] = ADDONVERSION
    settings['ADDONPATH'] = ADDONPATH
    settings['ADDONDATAPATH'] = ADDONDATAPATH
    settings['ADDONICON'] = ADDONICON
    settings['ADDONLANGUAGE'] = ADDONLANGUAGE
    for item in SETTINGSLIST:
        if isinstance(item['default'], bool):
            getset = getSettingBool
        elif isinstance(item['default'], int):
            getset = getSettingInt
        elif isinstance(item['default'], float):
            getset = getSettingNumber
        else:
            getset = getSettingString
        settings[item['name']] = getset(item['name'], item['default'])
    return settings
