import sys
import urlparse

import xbmc
import xbmcgui
import xbmcplugin

from xbmcaddon import Addon

from de.generia.kodi.plugin.frontend.base.Log import Log
from de.generia.kodi.plugin.frontend.base.Pagelet import Context
from de.generia.kodi.plugin.frontend.base.Pagelet import Request
from de.generia.kodi.plugin.frontend.base.Pagelet import Response
from de.generia.kodi.plugin.frontend.base.Pagelet import Action

from de.generia.kodi.plugin.frontend.zdf.MediathekFactory import MediathekFactory


class XbmcLog(Log):
    def __init__(self, prefix):
        super(XbmcLog, self).__init__()
        self.prefix = prefix
        
    def _getFormatMessage(self, message):
        j = message.find('{}')
        if j == -1:
            return message
        formatMessage = ''
        i = 0
        index = 0;
        while j != -1:
            formatMessage += message[i:j] + "{" + str(index) + "}"
            i = j + len("{}")
            j = message.find('{}', i)
            index += 1
        formatMessage += message[i:]
        return formatMessage
            
    def _log(self, level, message, *args):
        parts = []
        for arg in args:
            part = arg
            if isinstance(arg, basestring):
                part = arg # arg.decode('utf-8')
            parts.append(part)
        formatMessage = self._getFormatMessage(message)
        msg = self.prefix + formatMessage.format(*parts)
        xbmc.log(msg, level=level)

    def debug(self, message, *args):
        self._log(xbmc.LOGDEBUG, message, *args)
    
    def info(self, message, *args):
        self._log(xbmc.LOGNOTICE, message, *args)

    def warn(self, message, *args):
        self._log(xbmc.LOGWARNING, message, *args)
    
    def error(self, message, *args):
        self._log(xbmc.LOGERROR, message, *args)

class XbmcContext(Context):
    def __init__(self, log, settings):
        super(XbmcContext, self).__init__(log, settings)
        self.addon = Addon()

    def getLocalizedString(self, id):
        return self.addon.getLocalizedString(id)    
    
    def getProfileDir(self):
        profileDir = xbmc.translatePath(self.addon.getAddonInfo('profile'))
        return profileDir

class XbmcRequest(Request):
    def __init__(self, context, baseUrl, handle, params):
        super(XbmcRequest, self).__init__(context, baseUrl, handle, params)
    
class XbmcResponse(Response):
    def __init__(self, context, baseUrl, handle):
        super(XbmcResponse, self).__init__(context, baseUrl, handle)
    
    def addItem(self, item):
        if item is None:
            return

        title = item.title

        infoLabels = {}
        infoLabels['title'] = title
        infoLabels['sorttitle'] = title
        infoLabels['genre'] = item.genre
        plot = ""
        sep = ""
        if item.genre is not None:
            plot = item.genre
            sep = "\n"
        if item.text is not None:
            plot = plot + sep + item.text
        infoLabels['plot'] = plot

        date = item.date
        if date is not None and date != "":
            infoLabels['date'] = date

        duration = item.duration
        if duration is not None and duration != "":
            infoLabels['Duration'] = duration

        li = xbmcgui.ListItem(title, item.text)
        if item.image is not None:
            li.setArt({'poster': item.image, 'banner': item.image, 'thumb': item.image, 'icon': item.image, 'fanart': item.image})
        li.setInfo(type="Video", infoLabels=infoLabels)
        li.setProperty('IsPlayable', str(item.isPlayable))
        url = self.encodeUrl(item.action)
        #li.addContextMenuItems([('Suche -AK','xbmc.RunPlugin(%s?nix=da)'%(self.baseUrl))])
        #li.addContextMenuItems(['Item-Menu', 'RunPlugin(plugin://'+ self.handle +'/'])
        #self.context.log.info("[Response] - {} -> {}, title='{}' date='{}'", item.isFolder, url, title, date)
        xbmcplugin.addDirectoryItem(handle=self.handle, url=url, listitem=li, isFolder=item.isFolder)
    
    def close(self):
        xbmcplugin.endOfDirectory(self.handle)
        
    def sendError(self, message, action=Action()):
        self._sendMessage(xbmcgui.NOTIFICATION_ERROR, self.context._(32039), message, action)
        
    def sendInfo(self, message, action=Action()):
        self._sendMessage(xbmcgui.NOTIFICATION_INFO, self.context._(32040), message, action)
        
    def _sendMessage(self, level, caption, message, action=Action()):
        dialog = xbmcgui.Dialog()
        dialog.notification(caption, message, level)
        url = self.encodeUrl(action)
        self.context.log.info("[Response] - send{} '{}', redirecting to '{}'", caption, message, url)
        listItem = xbmcgui.ListItem()
        xbmcplugin.setResolvedUrl(self.handle, False, listItem)


class Settings(object):
    def __init__(self, handle):
        # Searching
        self.mergeCategoryAndTitle = xbmcplugin.getSetting(handle, 'mergeCategoryAndTitle') == 'true'
        self.loadAllSearchResults = xbmcplugin.getSetting(handle, 'loadAllSearchResults') == 'true'
        self.showOnlyPlayableSearchResults = xbmcplugin.getSetting(handle, 'showOnlyPlayableSearchResults') == 'true'
        self.searchHistorySize = int(xbmcplugin.getSetting(handle, 'searchHistorySize'))
        self.itemPattern = xbmcplugin.getSetting(handle, 'itemPattern')
        # Labeling
        self.showDateInTitle = xbmcplugin.getSetting(handle, 'showDataInTitle') == 'true'
        self.showGenreInTitle = xbmcplugin.getSetting(handle, 'showGenreInTitle') == 'true'
        self.showPlayableInTitle = xbmcplugin.getSetting(handle, 'showPlayableInTitle') == 'true'
        self.showTagsInTitle = xbmcplugin.getSetting(handle, 'showTagsInTitle') == 'true'
        self.showEpisodeInTitle = xbmcplugin.getSetting(handle, 'showEpisodeInTitle') == 'true'
        # Player
        self.filterMasterPlaylist = xbmcplugin.getSetting(handle, 'filterMasterPlaylist') == 'true'
        self.disableSubtitles = xbmcplugin.getSetting(handle, 'disableSubtitles') == 'true'


baseUrl = sys.argv[0]
handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
pageletId = None
params = {}
for key, value in args.iteritems():
    if key == 'pagelet':
        pageletId = value[0];
    else:
        params[key] = value[0]
        
log = XbmcLog('ZDF Mediathek 2016 [' + str(handle) + ']: ')
log.info('[Plugin] - Python-Version: {} {}',  (sys.executable or sys.platform), sys.version)
log.info('[Plugin] - executing url={}{} ...', baseUrl, sys.argv[2][0:])
start = log.start()
#xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_DATE)
xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_GENRE)
xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_DURATION)

settings = Settings(handle)
context = XbmcContext(log, settings)
factory = MediathekFactory(log, settings)
pagelet = factory.createPagelet(context, pageletId, params)
pagelet.init(context)
request = XbmcRequest(context, baseUrl, handle, params)
response = XbmcResponse(context, baseUrl, handle)

pagelet.service(request, response)
response.close()

log.info('[Plugin] - executing url={}{} ... done. [{} ms]', baseUrl, sys.argv[2][0:], log.stop(start))
