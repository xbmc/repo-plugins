from de.generia.kodi.plugin.backend.zdf.AbstractPageResource import AbstractPageResource

from de.generia.kodi.plugin.backend.zdf import stripHtml
from de.generia.kodi.plugin.backend.zdf.Regex import getTagPattern
from de.generia.kodi.plugin.backend.zdf.Regex import getTag
from de.generia.kodi.plugin.backend.zdf.Regex import compile
from de.generia.kodi.plugin.backend.zdf.Teaser import Teaser

livetvCellPattern = getTagPattern('div', 'js-livetv-scroller-cell')
titlePattern = compile('<h2[^>]*>([^<]*)</h2>')
contentNamePattern = compile('data-zdfplayer-id="([^"]*)"')
imagePattern = compile('data-src="([^"]*)"')


class LiveTvResource(AbstractPageResource):

    def __init__(self, url):
        super(LiveTvResource, self).__init__(url)

    def parse(self):
        super(LiveTvResource, self).parse()
        livetvCellMatch = livetvCellPattern.search(self.content)
        if livetvCellMatch is None:
            #self.warn("can't find live-tv cells in page '{}', no channels will be available ...", self.url)
            return
        
        self.teasers = []
        while livetvCellMatch is not None:
            pos = livetvCellMatch.end(0)
            teaser = Teaser()
            pos = self._parseTitle(pos, teaser)
            pos = self._parseContentName(pos, teaser)
            pos = self._parseApiToken(pos, teaser)
            pos = self._parseImage(pos, teaser)
            if teaser.title is not None and teaser.contentName is not None:
                self.teasers.append(teaser)        
            livetvCellMatch = livetvCellPattern.search(self.content, pos)
            
    def _parseApiToken(self, pos, teaser):
        pos = teaser.parseApiToken(self.content, pos)
        return pos
            
    def _parseTitle(self, pos, teaser):
        titleMatch = titlePattern.search(self.content, pos)
        if titleMatch is None:
            #self.warn("can't find title in live-tv cell at pos '{}' in page '{}', skipping ...", pos, self.url)
            return pos
        
        title = titleMatch.group(1).strip()
        teaser.title = title
        pos = titleMatch.end(0)
        return pos
            
    def _parseContentName(self, pos, teaser):
        contentNameMatch = contentNamePattern.search(self.content, pos)
        if contentNameMatch is None:
            #self.warn("can't find content-name in live-tv cell at pos '{}' in page '{}', skipping ...", pos, self.url)
            return pos
        
        contentName = contentNameMatch.group(1).strip()
        teaser.contentName = contentName
        teaser.playable = True
        pos = contentNameMatch.end(0)
        return pos
    
    def _parseImage(self, pos, teaser):
        imageMatch = imagePattern.search(self.content, pos)
        if imageMatch is None:
            #self.warn("can't find image in live-tv cell at pos '{}' in page '{}', skipping ...", pos, self.url)
            return pos
        
        image = imageMatch.group(1).strip()
        teaser.image = image
        pos = imageMatch.end(0)
        return pos