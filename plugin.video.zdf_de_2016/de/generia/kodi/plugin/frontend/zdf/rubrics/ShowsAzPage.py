from de.generia.kodi.plugin.frontend.base.Pagelet import Action        

from de.generia.kodi.plugin.frontend.zdf.AbstractPage import AbstractPage
from de.generia.kodi.plugin.frontend.zdf.Constants import Constants


class ShowsAzPage(AbstractPage):

    def service(self, request, response):
        rubricBaseUrl = Constants.showsAzUrl + '?group='
        groups = []
        for i in range (0, 26):
            group = chr(ord('a') + i)
            groups.append(group)
        groups.append('0 - 9')
        
        for group in groups:
            url = rubricBaseUrl + group.replace(' ', '+')
            response.addFolder(self._(32038, group.upper()), Action('RubricPage', {'rubricUrl': url}))
        