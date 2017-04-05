from xbmcswift2 import xbmc, xbmcaddon
import os

UA_PS4 = 'PS4Application libhttp/1.000 (PS4) libhttp/3.15 (PlayStation 4)'
UA_PC = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36'
COOKIE_PATH = xbmc.translatePath(os.path.join(xbmcaddon.Addon().getAddonInfo('profile'), 'cookies.p'))
ADDON_PATH_PROFILE = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))