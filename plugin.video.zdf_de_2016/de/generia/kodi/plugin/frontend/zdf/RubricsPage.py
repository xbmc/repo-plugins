from de.generia.kodi.plugin.backend.zdf.NavigationResource import NavigationResource

from de.generia.kodi.plugin.frontend.base.Pagelet import Action        

from de.generia.kodi.plugin.frontend.zdf.Constants import Constants
from de.generia.kodi.plugin.frontend.zdf.ItemPage import ItemPage


class RubricsPage(ItemPage):

    def service(self, request, response):
        apiToken = request.getParam('apiToken')

        navigation = NavigationResource(Constants.baseUrl)
        self._parse(navigation)
        for rubric in navigation.rubrics:
            response.addFolder(self._(32004) + ' - ' + rubric.title, Action('RubricPage', {'apiToken': apiToken, 'rubricUrl': rubric.url}))
