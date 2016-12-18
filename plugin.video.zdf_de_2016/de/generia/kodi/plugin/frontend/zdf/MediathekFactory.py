import os

import xbmc

from xbmcaddon import Addon

from de.generia.kodi.plugin.frontend.base.PageletFactory import PageletFactory        

from de.generia.kodi.plugin.frontend.zdf.Constants import Constants
from de.generia.kodi.plugin.frontend.zdf.Mediathek import Mediathek

from de.generia.kodi.plugin.frontend.zdf.player.PlayVideo import PlayVideo        

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
    
    def __init__(self, settings=None):
        super(MediathekFactory, self).__init__()
        self.settings = settings
        
    def createPagelet(self, pageletId, params):
        if pageletId == 'SearchPage':
            return SearchPage(self._createSearchHistory())
        if pageletId == 'SearchMenuPage':
            return SearchMenuPage()
        if pageletId == 'SearchHistoryPage':
            return SearchHistoryPage(self._createSearchHistory())
        if pageletId == 'RubricsPage':
            return RubricsPage()
        if pageletId == 'RubricPage':
            return RubricPage()
        if pageletId == 'LiveTvPage':
            return LiveTvPage()
        if pageletId == 'ShowsAzPage':
            return ShowsAzPage()
        if pageletId == 'PlayVideo':
            return PlayVideo()
        
        return Mediathek()
        
    def _createSearchHistory(self):
        addon = Addon()
        profileDir = xbmc.translatePath(addon.getAddonInfo('profile'))
        storeFile  = os.path.join(profileDir, 'searchHistory.txt') 
        return SearchHistory(storeFile, self.settings.searchHistorySize)
