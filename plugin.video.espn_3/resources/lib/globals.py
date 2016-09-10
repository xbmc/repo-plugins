import os
import sys
import xbmc
import xbmcaddon

selfAddon = xbmcaddon.Addon()
addon_data_path = xbmc.translatePath(selfAddon.getAddonInfo('path')).decode('utf-8')
translation = selfAddon.getLocalizedString
defaultimage = os.path.join(addon_data_path, 'icon.png')
defaultfanart = os.path.join(addon_data_path, 'fanart.jpg')
defaultlive = os.path.join(addon_data_path, 'resources/media/new_live.png')
defaultreplay = os.path.join(addon_data_path, 'resources/media/new_replay.png')
defaultupcoming = os.path.join(addon_data_path, 'resources/media/new_upcoming.png')
pluginhandle = int(sys.argv[1])

ADDON_PATH_PROFILE = xbmc.translatePath(selfAddon.getAddonInfo('profile')).decode('utf-8')
if not os.path.exists(ADDON_PATH_PROFILE):
        os.makedirs(ADDON_PATH_PROFILE)

# User Agents
UA_PC = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
UA_ATV = 'AppleCoreMedia/1.0.0.13Y234 (Apple TV; U; CPU OS 9_2 like Mac OS X; en_us)'

def CLEAR_SAVED_DATA():
    try:
        os.remove(os.path.join(ADDON_PATH_PROFILE, 'adobe-cookies.lwp'))
    except:
        pass
    try:
        os.remove(os.path.join(ADDON_PATH_PROFILE, 'user_data.json'))
    except:
        pass
    try:
        for root, dirs, files in os.walk(ADDON_PATH_PROFILE):
            for currentFile in files:
                if currentFile.lower().endswith('.xml') and not currentFile.lower() == 'settings.xml':
                    os.remove(os.path.join(ADDON_PATH_PROFILE, currentFile))
    except:
        pass
    selfAddon.setSetting(id='ClearData', value='false')

if selfAddon.getSetting('ClearData') == 'true':
    CLEAR_SAVED_DATA()

if selfAddon.getSetting('DisableSSL') == 'true':
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
