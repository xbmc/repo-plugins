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

from de.generia.kodi.plugin.frontend.zdf.search.SearchHistory import HistoryEntry       


class SearchPage(AbstractPage):
    searchHistory = None
    
    def __init__(self, searchHistory):
        super(SearchPage, self).__init__()
        self.searchHistory = searchHistory

    def service(self, request, response):
        pages = int(request.getParam('pages', -1))
        page = int(request.getParam('page', 1))
        
        query = dict(request.params)
        if 'pages' in query:
            del query['pages']
        
        query['from'] = ''
        query['to'] = ''
        query['sender'] = 'alle Sender'
        query['attrs'] = ''
        
        if 'q' not in query:
            self.info("Timer - getting search-string from keyboard ...")
            start = self.context.log.start()
            text = self._getKeyboardInput()
            self.info("Timer - getting search-string from keyboard ... done. [{} ms]", self.context.log.stop(start))
            if text is not None:
                query['q'] = text
            else:
                response.sendInfo(self._(32006))
                return

        self.info("Timer - loading results  ...")
        start = self.context.log.start()
        self._progress = xbmcgui.DialogProgress()
        try:
            msg = self._(32021)
            if pages != -1:
                msg = self._(32022, page, pages)
            self._progress.create(self._(32020), msg)
            self._progress.update(0, msg)
            self._loadResults(request, response, pages, page, query)
            
            # add search history entry
            self._saveQuery(query)
            
        #except:
        #    self.warn("Timer - loading results ... exception")            
        finally:
            self.info("Timer - loading results ... done. [{} ms]", self.context.log.stop(start))
            self._progress.close();

    def _saveQuery(self, query):
        if self.results > 0:
            contentTypes = None
            if 'contentTypes' in query:
                contentTypes = query['contentTypes']
            self.searchHistory.addEntry(HistoryEntry(query['q'].strip(), contentTypes))

    def _loadResults(self, request, response, pages, page, query):
        queryParams = urllib.urlencode(query)
        searchUrl = Constants.baseUrl + "/suche?" + queryParams
        
        self.info("searching url: '{}' ...", searchUrl)
        searchPage = SearchResource(searchUrl)
        self._parse(searchPage)
        self.info("found '{}' results.", len(searchPage.teasers))

        if len(searchPage.teasers) == 0:
            response.sendInfo(self._(32013))
        
        pages = int(math.ceil(float(searchPage.results) / float(searchPage.resultsPerPage)))
        
        self.results = 0
        self._addItems(response, searchPage.teasers)
        
        if len(searchPage.teasers) == 0:
            return
        
        if self.settings.loadAllSearchResults:
            self._addMoreResults(response, searchPage.moreUrl, pages, page)
        else:
            self._addMoreFolder(response, searchPage.moreUrl, pages, page)
            
        self._progress.update(percent=100)
        self.info("added '{}' result-items.", self.results)


    def _addItems(self, response, teasers):
        self.debug("Timer - creating list items  ...")
        start = self.context.log.start()
        for teaser in teasers:
            if not self.settings.showOnlyPlayableSearchResults or teaser.playable: 
                item = self._createItem(teaser)
                response.addItem(item)
                self.results += 1
        self.debug("Timer - creating list items ... done. [{} ms]", self.context.log.stop(start))

    def _addMoreResults(self, response, moreUrl, pages, page):

        while moreUrl is not None and page < pages and not self._progress.iscanceled():
            moreUrl = moreUrl.replace('&#x3D;', '=')
            moreUrl = moreUrl.replace('&amp;', '&')

            page += 1
            percent = page*100/pages
            self._progress.update(percent, self._(32022, page, pages))

            searchUrl = Constants.baseUrl + moreUrl
            self.info("searching url: '{}' ...", searchUrl)
            searchPage = SearchResource(searchUrl)
            self._parse(searchPage)
            
            if len(searchPage.teasers) > 0:
                self._addItems(response, searchPage.teasers)
                moreUrl = searchPage.moreUrl
            else: 
                moreUrl = None
            self.info("found '{}' results.", len(searchPage.teasers))

    def _addMoreFolder(self, response, moreUrl, pages, page):
        if page < pages:                
            page += 1
            moreAction = self._getMoreAction(moreUrl, pages, page)
            response.addFolder(self._(32017, page, pages), moreAction)

    def _getMoreAction(self, moreUrl, pages, page):
        i = moreUrl.find('?')
        if i != -1:
            moreQuery = moreUrl[i+1:]
            moreQuery = moreQuery.replace('&#x3D;', '=')
            moreQuery = moreQuery.replace('&amp;', '&')
            searchArgs = urlparse.parse_qs(moreQuery)
            for key, value in searchArgs.iteritems():
                searchArgs[key] = value[0]
            searchArgs['pages'] = pages
            searchArgs['page'] = page
            moreAction = Action('SearchPage', searchArgs)
            return moreAction
        

    def _getKeyboardInput(self):
        keyboard = xbmc.Keyboard('', self._(32005))
        keyboard.doModal()
        text = None
        if keyboard.isConfirmed() and keyboard.getText():
            text = keyboard.getText()
        return text

