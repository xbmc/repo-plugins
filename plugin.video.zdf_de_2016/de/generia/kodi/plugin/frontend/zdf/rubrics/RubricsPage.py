from de.generia.kodi.plugin.backend.zdf.NavigationResource import NavigationResource

from de.generia.kodi.plugin.frontend.base.Pagelet import Action        

from de.generia.kodi.plugin.frontend.zdf.AbstractPage import AbstractPage
from de.generia.kodi.plugin.frontend.zdf.Constants import Constants


class RubricsPage(AbstractPage):

    excludedRubricUrls = [
        Constants.showsAzUrl,
        '/bestbewertet',
        '/meist-gesehen',
        #'/barrierefreiheit-im-zdf'
    ]
    
    def service(self, request, response):

        navigation = NavigationResource(Constants.baseUrl)
        self._parse(navigation)

        for rubric in navigation.rubrics:
            if self._isExcluded(rubric):
                continue
            response.addFolder(str(self._(32004)) + ' - ' + rubric.title, Action('RubricPage', {'rubricUrl': rubric.url}))

    def _isExcluded(self, rubric):
        for url in self.excludedRubricUrls:
            if url == rubric.url:
                return True
        return False