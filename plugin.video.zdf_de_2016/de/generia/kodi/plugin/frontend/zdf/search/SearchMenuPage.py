from de.generia.kodi.plugin.backend.zdf.NavigationResource import NavigationResource

from de.generia.kodi.plugin.frontend.base.Pagelet import Action        

from de.generia.kodi.plugin.frontend.zdf.AbstractPage import AbstractPage
from de.generia.kodi.plugin.frontend.zdf.Constants import Constants


class SearchMenuPage(AbstractPage):

    def service(self, request, response):
        response.addFolder(self._(32030), Action('SearchHistoryPage'))
        response.addFolder(self._(32001), Action('SearchPage', {'contentTypes':'episode'}))
        response.addFolder(self._(32002), Action('SearchPage'))
