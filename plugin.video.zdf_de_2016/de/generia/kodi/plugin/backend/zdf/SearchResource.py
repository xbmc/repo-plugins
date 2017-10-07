from de.generia.kodi.plugin.backend.zdf.AbstractPageResource import AbstractPageResource

from de.generia.kodi.plugin.backend.zdf.Regex import compile
from de.generia.kodi.plugin.backend.zdf.Teaser import Teaser

resultsPattern = compile('<div\s*class="[^"]*"\s*data-loadmore-size="([^"]*)"\s*data-loadmore-result-count="([^"]*)"\s*data-module="loadmore">')
loadMorePattern = compile('<a\s*href="([^"]*)"[^>]*class="[^"]*load-more[^"]*"')

class SearchResource(AbstractPageResource):

    def __init__(self, url):
        super(SearchResource, self).__init__(url)
            
    def parse(self):
        super(SearchResource, self).parse()
        
        self.teasers = []
        self.resultsPerPage = 0
        self.results = 0

        pos = 0
        resultsMatch = resultsPattern.search(self.content, pos)
        if resultsMatch is not None:
            loadMoreSize = resultsMatch.group(1)
            if loadMoreSize is not None and loadMoreSize != '':
                self.resultsPerPage = int(loadMoreSize)
            loadMoreCount = resultsMatch.group(2)
            if loadMoreCount is None or loadMoreCount == '':
                return;
            self.results = int(loadMoreCount)
            pos = resultsMatch.end(0)
            
        prevPos = 0
        while pos != -1:
            teaser = Teaser()
            prevPos = pos
            pos = teaser.parse(self.content, pos, self._getBaseUrl())
            if teaser.valid():
                self.teasers.append(teaser)
        
        loadMoreMatch = loadMorePattern.search(self.content, prevPos)
        self.moreUrl = None
        if loadMoreMatch is not None:
            self.moreUrl = loadMoreMatch.group(1).strip()
