import os
import sys
from urllib.parse import parse_qsl
from urllib.parse import urlencode

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

ADDON = xbmcaddon.Addon()
ID = ADDON.getAddonInfo('id')
NAME = ADDON.getAddonInfo('name')
VERSION = ADDON.getAddonInfo('version')
ICON = ADDON.getAddonInfo('icon')
FANART = ADDON.getAddonInfo('fanart')
PATH = ADDON.getAddonInfo('path')
DATA_PATH = ADDON.getAddonInfo('profile')
PATH_T = xbmcvfs.translatePath(PATH)
DATA_PATH_T = xbmcvfs.translatePath(DATA_PATH)
IMAGE_PATH_T = os.path.join(PATH_T, 'resources', 'media')
LANGUAGE = ADDON.getLocalizedString
KODILANGUAGE = xbmc.getLocalizedString

HANDLE = int(sys.argv[1])


def executebuiltin(func, block=False):
    xbmc.executebuiltin(func, block)


def notify(msg):
    xbmcgui.Dialog().notification(NAME, msg, ICON)


def log(msg, level=xbmc.LOGDEBUG):
    # DEBUG = 0, INFO = 1, WARNING = 2, ERROR = 3, FATAL = 4
    xbmc.log(f"[{ID}/{VERSION}] {msg}", level=level)


def getParams():
    if not sys.argv[2]:
        return {}
    return dict(parse_qsl(sys.argv[2][1:]))


def parameters(p, host=sys.argv[0]):
    for k, v in list(p.items()):
        if v:
            p[k] = v
        else:
            p.pop(k, None)
    return f"{host}?{urlencode(p)}"


def getSetting(setting):
    return ADDON.getSetting(setting).strip()


def getSettingAsBool(setting):
    return getSetting(setting).lower() == 'true'


def getSettingAsNum(setting):
    num = 0
    try:
        num = float(getSetting(setting))
    except ValueError:
        pass
    return num


def getSettingAsInt(setting):
    return int(getSettingAsNum(setting))


def setSetting(setting, value):
    ADDON.setSetting(id=setting, value=str(value))


def showOkDialog(line, heading=NAME):
    xbmcgui.Dialog().ok(heading, line)


def createListItem(
        label='', params=None, label2=None,
        thumb=None, fanart=None, poster=None, arts={},
        videoInfo=None, properties={}, isFolder=True,
        path=None, subs=None):
    item = xbmcgui.ListItem(label, label2, path, offscreen=True)
    if thumb:
        arts['thumb'] = thumb
    if fanart:
        arts['fanart'] = fanart
    if poster:
        arts['poster'] = poster
    item.setArt(arts)
    item.setInfo('video', videoInfo)
    if subs is not None:
        item.setSubtitles(subs)
    if not isFolder:
        properties['IsPlayable'] = 'true'
    for key, value in list(properties.items()):
        item.setProperty(key, value)
    return item


def addListItem(
        label='', params=None, label2=None,
        thumb=None, fanart=None, poster=None, arts={},
        videoInfo=None, properties={}, isFolder=True,
        path=None, subs=None):
    if isinstance(params, dict):
        url = parameters(params)
    else:
        url = params
    item = createListItem(
        label=label, params=params, label2=label2,
        thumb=thumb, fanart=fanart, poster=poster, arts=arts,
        videoInfo=videoInfo, properties=properties, isFolder=isFolder,
        path=path, subs=subs)
    return xbmcplugin.addDirectoryItem(
        handle=HANDLE, url=url, listitem=item, isFolder=isFolder)


def getPlaylist(type=xbmc.PLAYLIST_VIDEO, clear=True):
    plst = xbmc.PlayList(type)
    if clear:
        plst.clear()
        xbmc.sleep(200)
    return plst


def setResolvedUrl(
        url='', solved=True, headers=None, subs=None,
        item=None, exit=True):
    headerUrl = ''
    if headers:
        headerUrl = urlencode(headers)
    item = xbmcgui.ListItem(
        path=f"{url}|{headerUrl}", offscreen=True) if item is None else item
    if subs is not None:
        item.setSubtitles(subs)
    xbmcplugin.setResolvedUrl(HANDLE, solved, item)
    if exit:
        sys.exit(0)


def setContent(ctype='videos'):
    xbmcplugin.setContent(HANDLE, ctype)


def endScript(message=None, loglevel=2, closedir=True, exit=True):
    if message:
        log(message, loglevel)
    if closedir:
        xbmcplugin.endOfDirectory(handle=HANDLE, succeeded=True)
    if exit:
        sys.exit(0)


log(f"Starting with command \"{sys.argv[2]}\"", 1)
