
from de.generia.kodi.plugin.backend.web.HtmlResource import HtmlResource
from de.generia.kodi.plugin.backend.zdf.Teaser import Teaser


class TeaserLazyloadResource(HtmlResource):
    baseUrl = None
    
    def __init__(self, teaserLazyload):
        super(TeaserLazyloadResource, self).__init__(teaserLazyload.url)
        self.teaserLazyload = teaserLazyload
            
    def parse(self):
        super(TeaserLazyloadResource, self).parse()

        teaser = Teaser()
        pos = 0
        teaserMatch = self.teaserLazyload.teaserPattern.search(self.content, pos)
        teaser.parse(self.content, pos, self.teaserLazyload.baseUrl, teaserMatch)

        self.teaser = None
        if teaser.valid():
            #teaser.title = "LL: " + teaser.title
            self.teaser = teaser
