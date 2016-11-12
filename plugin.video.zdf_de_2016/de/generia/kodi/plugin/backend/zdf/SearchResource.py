from de.generia.kodi.plugin.backend.web.HtmlResource import HtmlResource

from de.generia.kodi.plugin.backend.zdf.Regex import compile
from de.generia.kodi.plugin.backend.zdf.Teaser import Teaser

resultsPattern = compile('<div class="[^"]*" data-loadmore-size="([^"]*)" data-loadmore-result-count="([^"]*)" data-module="loadmore">')
loadMorePattern = compile('<a href="([^"]*)"[^>]*class="[^"]*load-more[^"]*"')

class SearchResource(HtmlResource):

    def __init__(self, url):
        super(SearchResource, self).__init__(url)
            
    def parse(self):
        super(SearchResource, self).parse()
        
        pos = 0
        resultsMatch = resultsPattern.search(self.content, pos)
        if resultsMatch is not None:
            self.results = int(resultsMatch.group(2))
            self.resultsPerPage = int(resultsMatch.group(1))
            pos = resultsMatch.end(0)
            
        self.teasers = []
        prevPos = 0
        while pos != -1:
            teaser = Teaser()
            prevPos = pos
            pos = teaser.parse(self.content, pos)
            if teaser.valid():
                self.teasers.append(teaser)
        
        loadMoreMatch = loadMorePattern.search(self.content, prevPos)
        self.moreUrl = None
        if loadMoreMatch is not None:
            self.moreUrl = loadMoreMatch.group(1).strip()
