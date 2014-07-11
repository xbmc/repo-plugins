# -*- coding: utf-8 -*-

import xbmcplugin
import xbmcgui
import xbmcaddon

import os
import json
import urllib
import urllib2

#import pydevd
#pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)

from bromixbmc import Bromixbmc
bromixbmc = Bromixbmc("plugin.video.dmax_de", sys.argv)

import discoverychannel
__fusion_client__ = discoverychannel.fusion.Client(discoverychannel.fusion.__CONFIG_DMAX_DE__)

__FANART__ = os.path.join(bromixbmc.Addon.Path, "fanart.jpg")
__ICON_HIGHLIGHTS__ = os.path.join(bromixbmc.Addon.Path, "resources/media/highlight.png")
__ICON_LIBRARY__ = os.path.join(bromixbmc.Addon.Path, "resources/media/library.png")
__ICON_FAVOURITES__ = os.path.join(bromixbmc.Addon.Path, "resources/media/pin.png")

__ACTION_SHOW_HIGHLIGHTS__ = 'showHighlights'
__ACTION_SHOW_LIBRARY__ = 'showLibrary'
__ACTION_SHOW_EPISODES__ = 'showEpisodes'
__ACTION_ADD_TO_FAV__ = 'addToFav'
__ACTION_REMOVE_FROM_FAVS__ = 'removeFromFavs'
__ACTION_SHOW_FAVS__ = 'showFavs'
__ACTION_PLAY__ = 'play'

SETTING_SHOW_FANART = bromixbmc.Addon.getSetting('showFanart')=="true"
if not SETTING_SHOW_FANART:
    __FANART__ = ""

def _listEpisodes(episodes, showSeriesTitle=True):
    episodes_list = episodes.get('episodes-list', {})
    
    xbmcplugin.setContent(bromixbmc.Addon.Handle, 'episodes')
    for episode in episodes_list:
        thumbnailImage = episode.get('episode-cloudinary-image', None)
        if thumbnailImage!=None:
            thumbnailImage =  'http://res.cloudinary.com/db79cecgq/image/upload/c_fill,g_faces,h_270,w_480/'+thumbnailImage
            
        title = episode.get('episode-title', "")
        subtitle = episode.get('episode-subtitle', "")
        plot = episode.get('episode-long-description', "")
        
        id = episode.get('episode-additional-info', None)
        if id!=None:
            id = id.get('episode-brightcove-id', None)
        
        if showSeriesTitle:
            name = title
            if len(subtitle)>0:
                name = name+" - "+subtitle
        else:
            if len(subtitle)>0:
                name = subtitle
            else:
                name = title
        
        if id!=None:
            params = {'action': __ACTION_PLAY__,
                      'episode': id}
            
            additionalInfoLabels = {'plot': plot}
            bromixbmc.addVideoLink(name, params=params, thumbnailImage=thumbnailImage, fanart=__FANART__, additionalInfoLabels=additionalInfoLabels)
    
def _listSeries(series):
    def _sort_key(d):
        return d.get('series-title', "").lower()
    
    _series_list = series.get('series-list', {})
    series_list = sorted(_series_list, key=_sort_key, reverse=False)
    
    for series in series_list:
        name = series.get('series-title', None)
        id = series.get('series-id', None)
        
        thumbnailImage = series.get('series-cloudinary-image', None)
        if thumbnailImage!=None:
            thumbnailImage =  'http://res.cloudinary.com/db79cecgq/image/upload/c_fill,g_faces,h_270,w_480/'+thumbnailImage
        
        if name!=None and id!=None:
            params = {'action': __ACTION_SHOW_EPISODES__,
                      'series': id}
            
            contextParams = {'action': __ACTION_ADD_TO_FAV__,
                             'series': id,
                             'title': name.encode('utf-8'),
                             'thumb': thumbnailImage
                             }
            contextRun = 'RunPlugin('+bromixbmc.createUrl(contextParams)+')'
            contextMenu = [("[B]"+bromixbmc.Addon.localize(30002)+"[/B]", contextRun)]
            bromixbmc.addDir(name, params=params, thumbnailImage=thumbnailImage, fanart=__FANART__, contextMenu=contextMenu)
            pass

def _listJsonResult(jsonResult, showSeriesTitle=True):
    episodes = jsonResult.get('episodes', None)
    if episodes!=None:
        _listEpisodes(episodes, showSeriesTitle)
        
    series = jsonResult.get('series', None)
    if series!=None:
        _listSeries(series)

def showIndex():
    # show favourties
    if len(bromixbmc.Addon.getFavorites())>0:
        params = {'action': __ACTION_SHOW_FAVS__}
        bromixbmc.addDir("[B]"+bromixbmc.Addon.localize(30004)+"[/B]", thumbnailImage=__ICON_FAVOURITES__, params=params, fanart=__FANART__)
    
    # add 'Videotheke'
    params = {'action': __ACTION_SHOW_LIBRARY__}
    bromixbmc.addDir(bromixbmc.Addon.localize(30000), params = params, thumbnailImage=__ICON_LIBRARY__, fanart=__FANART__)
    
    # add 'Highlights'
    params = {'action': __ACTION_SHOW_HIGHLIGHTS__}
    bromixbmc.addDir(bromixbmc.Addon.localize(30001), params = params, thumbnailImage=__ICON_HIGHLIGHTS__, fanart=__FANART__)
    
    xbmcplugin.endOfDirectory(bromixbmc.Addon.Handle)
    return True

def showHighlights():
    json = __fusion_client__.getHighlights()
    
    _listJsonResult(json, showSeriesTitle=True)
    
    xbmcplugin.endOfDirectory(bromixbmc.Addon.Handle)
    return True

def showLibrary():
    json = __fusion_client__.getLibrary()
    
    _listJsonResult(json)
    
    xbmcplugin.endOfDirectory(bromixbmc.Addon.Handle)
    return True

def showEpisodes(series_id):
    json = __fusion_client__.getEpisodes(series_id)
    
    _listJsonResult(json, showSeriesTitle=False)
    
    xbmcplugin.endOfDirectory(bromixbmc.Addon.Handle)
    return True

def _getVideoResolution():
    resolution = 720
    
    vq = bromixbmc.Addon.getSetting('videoQuality')
    if vq=='1':
        resolution=720
    elif vq=='0':
        resolution=480
    else:
        resolution=720
        
    return resolution

def _getBestVideoUrl(json):
    url = None
    resolution = _getVideoResolution()
    last_resolution=0
    for stream in json.get('renditions', []):
        test_resolution = stream.get('frameHeight', 0)
        if test_resolution>=last_resolution and test_resolution<=resolution:
            last_resolution = test_resolution
            url = stream.get('url', None)
        pass
    
    return url

def play(episode_id):
    result = __fusion_client__.getVideoStreams(episode_id)
    url = _getBestVideoUrl(result)
    if url!=None:
        listitem = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(bromixbmc.Addon.Handle, True, listitem)
        
        # prevend infinite loop
        tries = 100
        while tries>0:
            xbmc.sleep(50)
            if xbmc.Player().isPlaying() and xbmc.getCondVisibility("Player.Paused"):
                xbmc.Player().pause()
                break
            tries-=1
    else:
        bromixbmc.showNotification(bromixbmc.Addon.localize(30999))
        
def addToFavs(series_id):
    title = bromixbmc.getParam('title', '').decode('utf-8')
    thumbnailImage = bromixbmc.getParam('thumb', '')
    if title!='' and series_id!=None:
        newFav = {}
        newFav['title'] = title
        newFav['image'] = thumbnailImage
        
        bromixbmc.Addon.addFavorite(series_id, newFav)
        
def removeFromFavs(series_id):
    favs = bromixbmc.Addon.removeFavorite(series_id)
    xbmc.executebuiltin("Container.Refresh");
        
def showFavs():
    def _sort_key(d):
        return d[1].get('title', "")
    
    _favs = bromixbmc.Addon.getFavorites()
    favs = sorted(_favs, key=_sort_key, reverse=False)
    
    for series in favs:
        if len(series)==2:
            item = series[1]
            name = item.get('title', None)
            thumbnailImage = item.get('image', "")
            
            if name!=None:
                params = {'action': __ACTION_SHOW_EPISODES__,
                          'series': series[0]}
                
                contextParams = {'action': __ACTION_REMOVE_FROM_FAVS__,
                                 'series': series[0]}
                contextRun = 'RunPlugin('+bromixbmc.createUrl(contextParams)+')'
                contextMenu = [("[B]"+bromixbmc.Addon.localize(30003)+"[/B]", contextRun)]
                
                bromixbmc.addDir(name, params=params, thumbnailImage=thumbnailImage, fanart=__FANART__, contextMenu=contextMenu)
            
    xbmcplugin.endOfDirectory(bromixbmc.Addon.Handle)
    return True

action = bromixbmc.getParam('action')
series_id = bromixbmc.getParam('series')
episode_id = bromixbmc.getParam('episode')

if action==__ACTION_SHOW_HIGHLIGHTS__:
    showHighlights()
elif action==__ACTION_SHOW_LIBRARY__:
    showLibrary()
elif action==__ACTION_SHOW_EPISODES__ and series_id!=None:
    showEpisodes(series_id)
elif action==__ACTION_PLAY__ and episode_id!=None:
    play(episode_id)
elif action==__ACTION_ADD_TO_FAV__ and series_id!=None:
    addToFavs(series_id)
elif action==__ACTION_REMOVE_FROM_FAVS__ and series_id!=None:
    removeFromFavs(series_id)
elif action==__ACTION_SHOW_FAVS__:
    showFavs()
else:
    showIndex()
