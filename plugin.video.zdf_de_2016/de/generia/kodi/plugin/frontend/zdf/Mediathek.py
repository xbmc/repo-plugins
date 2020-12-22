
from de.generia.kodi.plugin.frontend.base.Pagelet import Action        
from de.generia.kodi.plugin.frontend.base.Pagelet import Pagelet        

from de.generia.kodi.plugin.frontend.zdf.Constants import Constants


class Mediathek(Pagelet):

    def service(self, request, response):
        response.addFolder(self._(32005), Action('SearchMenuPage'))

        response.addFolder(self._(32003), Action('RubricsPage'))

        response.addFolder(self._(32043), Action('RubricPage', {'rubricUrl': '/'}))
        response.addFolder(self._(32032), Action('RubricPage', {'rubricUrl': '/meist-gesehen'}))
        response.addFolder(self._(32037), Action('ShowsAzPage'))
        #response.addFolder(self._(32034), Action('RubricPage', {'rubricUrl': '/barrierefreiheit-im-zdf'}))
        response.addFolder(self._(32036), Action('RubricPage', {'rubricUrl': '/sendung-verpasst'}))

        response.addFolder(self._(32035), Action('LiveTvPage'))
