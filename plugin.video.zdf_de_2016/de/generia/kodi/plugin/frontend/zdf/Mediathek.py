from de.generia.kodi.plugin.backend.zdf.ConfigurationResource import ConfigurationResource
from de.generia.kodi.plugin.backend.zdf.NavigationResource import NavigationResource

from de.generia.kodi.plugin.frontend.base.Pagelet import Item        
from de.generia.kodi.plugin.frontend.base.Pagelet import Action        
from de.generia.kodi.plugin.frontend.base.Pagelet import Pagelet        
from de.generia.kodi.plugin.frontend.base.Pagelet import PageletFactory        

from de.generia.kodi.plugin.frontend.zdf.Constants import Constants
from de.generia.kodi.plugin.frontend.zdf.SearchPage import SearchPage       
from de.generia.kodi.plugin.frontend.zdf.RubricsPage import RubricsPage       
from de.generia.kodi.plugin.frontend.zdf.RubricPage import RubricPage       
from de.generia.kodi.plugin.frontend.zdf.PlayVideo import PlayVideo        

class MediathekFactory(PageletFactory):

    def __init__(self):
        super(MediathekFactory, self).__init__()
        
    def createPagelet(self, pageletId, params):
        if pageletId == 'SearchPage':
            return SearchPage()
        if pageletId == 'RubricsPage':
            return RubricsPage()
        if pageletId == 'RubricPage':
            return RubricPage()
        if pageletId == 'PlayVideo':
            return PlayVideo()
        
        return Mediathek()
        

class Mediathek(Pagelet):

    def service(self, request, response):
        configuration = ConfigurationResource(Constants.configUrl)
        self._parse(configuration)
        apiToken = configuration.apiToken

        #response.addItem(Item(title='Direct Stuttgart', isFolder=False, isPlayable=True, action=Action(url='https://zdfvodnone-vh.akamaihd.net/i/meta-files/zdf/smil/m3u8/300/16/09/160908_das_versprechen_ps_sok8/2/160908_das_versprechen_ps_sok8.smil/master.m3u8')))
        #response.addFolder('Soko Stuttgart', Action('RubricPage', {'apiToken': apiToken, 'rubricUrl':'/serien/soko-stuttgart'}))

        #response.addFolder('Suche - Soko', Action('SearchPage', {'apiToken': apiToken, 'q':'Soko', 'contentTypes':'episode'}))
        response.addFolder(self._(32001), Action('SearchPage', {'apiToken': apiToken, 'contentTypes':'episode'}))
        response.addFolder(self._(32002), Action('SearchPage', {'apiToken': apiToken}))

        response.addFolder(self._(32003), Action('RubricsPage', {'apiToken': apiToken}))
