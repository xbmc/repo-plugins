import os
import xbmc
import xbmcaddon

addon = xbmcaddon.Addon('plugin.video.funimation')
name = addon.getAddonInfo('name')
icon = addon.getAddonInfo('icon')

duration = ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10][int(addon.getSetting('notification_length'))]) * 1000
msg = addon.getLocalizedString(30602)

# remove cookie
cookie_path = xbmc.translatePath(addon.getAddonInfo('profile'))
cookie_path = os.path.join(cookie_path, 'fun-cookiejar.txt')
if os.path.exists(cookie_path):
    os.remove(cookie_path)

# clear cache server
try:
    import StorageServer
    cache = StorageServer.StorageServer(name)
    cache.delete('%')
except ImportError:
    # plugin cache is not installed so do nothing
    pass

xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(name, msg, duration, icon))
