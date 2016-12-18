import urllib
import urlparse
import math

import xbmc
import xbmcgui
import xbmcplugin

from de.generia.kodi.plugin.backend.zdf.SearchResource import SearchResource       

from de.generia.kodi.plugin.frontend.base.Pagelet import Item        
from de.generia.kodi.plugin.frontend.base.Pagelet import Action        
from de.generia.kodi.plugin.frontend.base.Pagelet import Pagelet        

from de.generia.kodi.plugin.frontend.zdf.AbstractPage import AbstractPage
from de.generia.kodi.plugin.frontend.zdf.Constants import Constants

class SearchHistoryPage(AbstractPage):

    def __init__(self, searchHistory):
        super(SearchHistoryPage, self).__init__()
        self.searchHistory = searchHistory

    def service(self, request, response):
        apiToken = request.getParam('apiToken')

        entries = self.searchHistory.getEntries()
        
        for entry in entries:
            params = {'apiToken': apiToken, 'q': entry.query }
            if entry.contentTypes is not None:
                params['contentTypes'] = entry.contentTypes
                
            response.addFolder(self._(32029, entry.date, entry.query), Action('SearchPage', params), date=entry.date)
