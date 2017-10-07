from de.generia.kodi.plugin.backend.zdf.LiveTvResource import LiveTvResource
from de.generia.kodi.plugin.backend.zdf.Teaser import Teaser

from de.generia.kodi.plugin.frontend.zdf.AbstractPage import AbstractPage
from de.generia.kodi.plugin.frontend.zdf.Constants import Constants


class LiveTvPage(AbstractPage):

    def service(self, request, response):
        liveTvUrl = Constants.baseUrl + '/live-tv'
        liveTvResource = LiveTvResource(liveTvUrl)
        self._parse(liveTvResource)

        for teaser in liveTvResource.teasers:
            item = self._createItem(teaser)
            if item is not None:
                response.addItem(item)
