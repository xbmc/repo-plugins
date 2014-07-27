import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui

import os
import sys
import urllib
import json

__SORT_METHOD_ALBUM__ = 13
__SORT_METHOD_ALBUM_IGNORE_THE__ = 14
__SORT_METHOD_ARTIST__ = 11
__SORT_METHOD_ARTIST_IGNORE_THE__ = 12
__SORT_METHOD_BITRATE__ = 39
__SORT_METHOD_CHANNEL__ = 38
__SORT_METHOD_COUNTRY__ = 16
__SORT_METHOD_DATE__ = 3
__SORT_METHOD_DATEADDED__ = 19
__SORT_METHOD_DATE_TAKEN__ = 40
__SORT_METHOD_DRIVE_TYPE__ = 6
__SORT_METHOD_DURATION__ = 8
__SORT_METHOD_EPISODE__ = 22
__SORT_METHOD_FILE__ = 5
__SORT_METHOD_FULLPATH__ = 32
__SORT_METHOD_GENRE__ = 15
__SORT_METHOD_LABEL__ = 1
__SORT_METHOD_LABEL_IGNORE_FOLDERS__ = 33
__SORT_METHOD_LABEL_IGNORE_THE__ = 2
__SORT_METHOD_LASTPLAYED__ = 34
__SORT_METHOD_LISTENERS__ = 36
__SORT_METHOD_MPAA_RATING__ = 28
__SORT_METHOD_NONE__ = 0
__SORT_METHOD_PLAYCOUNT__ = 35
__SORT_METHOD_PLAYLIST_ORDER__ = 21
__SORT_METHOD_PRODUCTIONCODE__ = 26
__SORT_METHOD_PROGRAM_COUNT__ = 20
__SORT_METHOD_SIZE__ = 4
__SORT_METHOD_SONG_RATING__ = 27
__SORT_METHOD_STUDIO__ = 30
__SORT_METHOD_STUDIO_IGNORE_THE__ = 31
__SORT_METHOD_TITLE__ = 9
__SORT_METHOD_TITLE_IGNORE_THE__ = 10
__SORT_METHOD_TRACKNUM__ = 7
__SORT_METHOD_UNSORTED__ = 37
__SORT_METHOD_VIDEO_RATING__ = 18
__SORT_METHOD_VIDEO_RUNTIME__ = 29
__SORT_METHOD_VIDEO_SORT_TITLE__ = 24
__SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE__ = 25
__SORT_METHOD_VIDEO_TITLE__ = 23
__SORT_METHOD_VIDEO_YEAR__ = 17

class Plugin(object):
    def __init__(self, name=None, addon_id=None):
        if addon_id:
            self._addon = xbmcaddon.Addon(id=addon_id)
        else:
            self._addon =  xbmcaddon.Addon()

        self._addon_uri = sys.argv[0]
        self._addon_handle = int(sys.argv[1])            
        self._addon_id = addon_id or self._addon.getAddonInfo('id')
        self._name = name or self._addon.getAddonInfo('name')
        self._addon_path = xbmc.translatePath(self._addon.getAddonInfo('path'))
        
        self._addon_data_path = xbmc.translatePath('special://profile/addon_data/%s' % self._addon_id)
        if not os.path.isdir(self._addon_data_path):
            os.mkdir(self._addon_data_path)
            
        self._favs_file = os.path.join(self._addon_data_path, "favs.dat")
        
    def createUrl(self, params={}):
        if params and len(params)>0:
            return self._addon_uri + '?' + urllib.urlencode(params)
        
        # default
        return self._addon_uri
    
    def getHandle(self):
        return self._addon_handle
    
    def setContent(self, content_type):
        xbmcplugin.setContent(self._addon_handle, content_type)
        
    def getPath(self):
        return self._addon_path
    
    def localize(self, text_id):
        return self._addon.getLocalizedString(text_id)
    
    def getSettingAsBool(self, name):
        return self._addon.getSetting(name)=="true"
    
    def getSettingAsInt(self, name, default=-1):
        try:
            return int(self._addon.getSetting(name))
        except:
            # do nothing
            pass
        
        return default
    
    def addSortMethod(self, sort_method=__SORT_METHOD_LABEL__):
        xbmcplugin.addSortMethod(self._addon_handle, sort_method)
        
    def addDirectory(self, name, params={}, thumbnailImage='', fanart='', contextMenu=None):
        url = self.createUrl(params)
        
        item = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=thumbnailImage)
        if fanart and len(fanart)>0:
            item.setProperty("fanart_image", fanart)
            
        if contextMenu!=None:
            item.addContextMenuItems(contextMenu);
            
        return xbmcplugin.addDirectoryItem(handle=self._addon_handle,url=url,listitem=item,isFolder=True)
    
    def addImage(self, name, image_url, fanart='', contextMenu=None):
        item = xbmcgui.ListItem(name, thumbnailImage=image_url)
        if fanart and len(fanart)>0:
            item.setProperty("fanart_image", fanart)
            
        if contextMenu!=None:
            item.addContextMenuItems(contextMenu);
            
        item.setInfo(type="pictures", infoLabels={'title': name})
            
        return xbmcplugin.addDirectoryItem(handle=self._addon_handle,url=image_url,listitem=item)
    
    def addVideoLink(self, name, params={}, thumbnailImage='', fanart='', infoLabels={}):
        url = self.createUrl(params)
        
        item = xbmcgui.ListItem(unicode(name), iconImage="DefaultVideo.png", thumbnailImage=thumbnailImage)
        
        # prepare infoLabels
        _infoLabels = {'title': name}
        _infoLabels.update(infoLabels)
            
        item.setInfo(type="video", infoLabels=_infoLabels)
        item.setProperty('IsPlayable', 'true')
        if fanart and len(fanart)>0:
            item.setProperty("fanart_image", fanart)
        
        return xbmcplugin.addDirectoryItem(handle=self._addon_handle, url=url, listitem=item)
    
    def endOfDirectory(self, success=True):
        xbmcplugin.endOfDirectory(self._addon_handle, succeeded=success)
        
    def setResolvedUrl(self, url, isLiveStream=False):
        listitem = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(self._addon_handle, True, listitem)
        
        # just to be sure :)
        if not isLiveStream:
            tries = 100
            while tries>0:
                xbmc.sleep(50)
                if xbmc.Player().isPlaying() and xbmc.getCondVisibility("Player.Paused"):
                    xbmc.Player().pause()
                    break
                tries-=1
            
    def _loadFavs(self):
        favs = {'favs': {}}
        if self._favs_file and os.path.exists(self._favs_file):
            try:
                file = open(self._favs_file, 'r')
                favs = json.loads(file.read(), encoding='utf-8')
            except:
                #do nothing
                pass
                
        return favs
    
    def getFavorites(self):
        favs = self._loadFavs()
        return favs.get('favs', {}).items()
    
    def setFavorite(self, id, fav):
        favs = self._loadFavs()
        
        favs['favs'][id] = fav
        self._storeFavs(favs)
        
    def removeFavorite(self, id):
        favs = self._loadFavs()
        fav = favs.get('favs', {}).get(id, None)
        if fav!=None:
            del favs['favs'][id]
            self._storeFavs(favs)
            
        return self.getFavorites()
    
    def _storeFavs(self, favs):
        if self._favs_file and favs:
            with open(self._favs_file, 'w') as outfile:
                json.dump(favs, outfile, sort_keys = True, indent = 4, encoding='utf-8')