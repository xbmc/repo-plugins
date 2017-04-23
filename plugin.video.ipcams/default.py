import sys
import os
import urllib
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

__addon__ = xbmcaddon.Addon()
__addonID__ = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__path__ = __addon__.getAddonInfo('path')

__LS__ = __addon__.getLocalizedString

def paramsToDict(parameters):

    paramDict = {}
    if parameters:
        paramPairs = parameters.split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

def writeLog(message, level=xbmc.LOGNOTICE):
    xbmc.log('[%s] %s' % (__addonID__, message.encode('utf-8', errors='ignore')), level)

arguments = sys.argv

if len(arguments) > 1:
    if arguments[0][0:6] == 'plugin':
        _addonHandle = int(arguments[1])
        arguments.pop(0)
        arguments[1] = arguments[1][1:]

    params = paramsToDict(arguments[1])
    mode = urllib.unquote_plus(params.get('mode', ''))

    item = [__LS__(30011) % ('1'), __LS__(30011) % ('2'), __LS__(30011) % ('3')]
    cam  = [__addon__.getSetting('cam1'), __addon__.getSetting('cam2'), __addon__.getSetting('cam3')]
    loc  = [__addon__.getSetting('loc1'), __addon__.getSetting('loc2'), __addon__.getSetting('loc3')]


if mode is '':
    _atleast = False
    for i in range(int(__addon__.getSetting('numcams'))):
        icon = xbmc.translatePath(os.path.join( __path__,'resources', 'lib', 'media', 'ipcam_%s.png' % (i + 1)))
        _listitem = '%s - %s' % (item[i].encode('utf-8'), loc[i]) if loc[i] != '' else item[i]
        li = xbmcgui.ListItem(_listitem)
        li.setArt({'icon': icon})
        li.setProperty('isPlayable', 'true')

        if cam[i] != '':
            xbmcplugin.addDirectoryItem(_addonHandle, cam[i], li)
            _atleast = True

if _atleast:
    xbmcplugin.endOfDirectory(_addonHandle)
else:
    xbmcgui.Dialog().ok(__addonname__, __LS__(30015))