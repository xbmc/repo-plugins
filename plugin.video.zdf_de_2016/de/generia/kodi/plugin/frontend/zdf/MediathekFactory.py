import os

import xbmc

from xbmcaddon import Addon

from de.generia.kodi.plugin.frontend.base.PageletFactory import PageletFactory        

from de.generia.kodi.plugin.frontend.zdf.Constants import Constants
from de.generia.kodi.plugin.frontend.zdf.Mediathek import Mediathek

from de.generia.kodi.plugin.frontend.zdf.player.PlayVideo import PlayVideo        
from de.generia.kodi.plugin.frontend.zdf.player.PlayerStore import PlayerStore        

from de.generia.kodi.plugin.frontend.zdf.rubrics.LiveTvPage import LiveTvPage       
from de.generia.kodi.plugin.frontend.zdf.rubrics.RubricPage import RubricPage       
from de.generia.kodi.plugin.frontend.zdf.rubrics.RubricsPage import RubricsPage       
from de.generia.kodi.plugin.frontend.zdf.rubrics.ShowsAzPage import ShowsAzPage       

from de.generia.kodi.plugin.frontend.zdf.search.SearchPage import SearchPage       
from de.generia.kodi.plugin.frontend.zdf.search.SearchMenuPage import SearchMenuPage       
from de.generia.kodi.plugin.frontend.zdf.search.SearchHistory import SearchHistory       
from de.generia.kodi.plugin.frontend.zdf.search.SearchHistoryPage import SearchHistoryPage       


class MediathekFactory(PageletFactory):
    settings = None
    
    def __init__(self, log, settings=None):
        super(MediathekFactory, self).__init__(log)
        self.settings = settings
        
    def createPagelet(self, context, pageletId, params):
        if pageletId == 'SearchPage':
            return SearchPage(self._createSearchHistory(context))
        if pageletId == 'SearchMenuPage':
            return SearchMenuPage()
        if pageletId == 'SearchHistoryPage':
            return SearchHistoryPage(self._createSearchHistory(context))
        if pageletId == 'RubricsPage':
            return RubricsPage()
        if pageletId == 'RubricPage':
            rubricUrl = params['rubricUrl']
            # redirect to ShowsAzPage, if url matches
            if rubricUrl == Constants.showsAzUrl:
                return ShowsAzPage()
            return RubricPage()
        if pageletId == 'LiveTvPage':
            return LiveTvPage()
        if pageletId == 'ShowsAzPage':
            return ShowsAzPage()
        if pageletId == 'PlayVideo':
            return PlayVideo(self._createPlayerStore(context), self.settings.filterMasterPlaylist)
        
        return Mediathek()
        
    def _createSearchHistory(self, context):
        profileDir = context.getProfileDir()
        storeFile  = os.path.join(profileDir, 'searchHistory.txt') 
        return SearchHistory(self.log, storeFile, self.settings.searchHistorySize)
        
    def _createPlayerStore(self, context):
        profileDir = context.getProfileDir()
        apiTokenFile  = os.path.join(profileDir, 'tokenCache.txt') 
        playlistFile  = os.path.join(profileDir, 'tmpFilteredPlaylist.m3u8') 
        return PlayerStore(self.log, apiTokenFile, playlistFile)
