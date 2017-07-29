from de.generia.kodi.plugin.backend.zdf.ConfigurationResource import ConfigurationResource

from de.generia.kodi.plugin.frontend.base.Pagelet import Action        
from de.generia.kodi.plugin.frontend.base.Pagelet import Pagelet        

from de.generia.kodi.plugin.frontend.zdf.Constants import Constants


class Mediathek(Pagelet):

    def service(self, request, response):
        #configuration = ConfigurationResource(Constants.configUrl)
        #self._parse(configuration)
        #apiToken = configuration.apiToken
        apiToken = Constants.apiToken

        response.addFolder(self._(32005), Action('SearchMenuPage', {'apiToken': apiToken}))

        response.addFolder(self._(32003), Action('RubricsPage', {'apiToken': apiToken}))

        response.addFolder(self._(32031), Action('RubricPage', {'apiToken': apiToken, 'rubricUrl': '/bestbewertet'}))
        response.addFolder(self._(32032), Action('RubricPage', {'apiToken': apiToken, 'rubricUrl': '/meist-gesehen'}))
        response.addFolder(self._(32037), Action('ShowsAzPage', {'apiToken': apiToken}))
        #response.addFolder(self._(32034), Action('RubricPage', {'apiToken': apiToken, 'rubricUrl': '/barrierefreiheit-im-zdf'}))
        response.addFolder(self._(32036), Action('RubricPage', {'apiToken': apiToken, 'rubricUrl': '/sendung-verpasst'}))

        response.addFolder(self._(32035), Action('LiveTvPage', {'apiToken': apiToken}))
