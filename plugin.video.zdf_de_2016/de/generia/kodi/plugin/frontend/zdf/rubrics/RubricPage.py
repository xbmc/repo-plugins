import xbmcgui

from de.generia.kodi.plugin.backend.zdf.RubricResource import RubricResource       
from de.generia.kodi.plugin.backend.zdf.TeaserLazyloadResolver import TeaserLazyloadResolver       
from de.generia.kodi.plugin.backend.zdf.api.VideoContentResource import VideoContentResource

from de.generia.kodi.plugin.frontend.base.Pagelet import Item        
from de.generia.kodi.plugin.frontend.base.Pagelet import Action        

from de.generia.kodi.plugin.frontend.zdf.AbstractPage import AbstractPage
from de.generia.kodi.plugin.frontend.zdf.Constants import Constants


class RubricPage(AbstractPage):

    def service(self, request, response):
        rubricUrl = request.getParam('rubricUrl')
        listType = request.getParam('listType')
        listStart = int(request.getParam('listStart', -1))
        listEnd = int(request.getParam('listEnd', -1))
        
        self.info("rubric-page: url='{}', listType='{}', listStart='{}', listEnd='{}'", rubricUrl, listType, listStart, listEnd)

        rubricResource = RubricResource(Constants.baseUrl + rubricUrl, listType, listStart, listEnd)
        self._parse(rubricResource)
        self._resolveLazyloadTeasers(rubricResource)
        
        if rubricResource.isRedirect:
            self.info("redirect detected to url='{}', skipping ...", rubricResource.responseLocation)
            dialog = xbmcgui.Dialog()
            dialog.ok(self._(32041), self._(32042, rubricUrl, rubricResource.responseLocation))
            return
        
        clusters = rubricResource.clusters
        
        if listType is not None:
            if len(clusters) == 1:
                self._renderTeasers(clusters[0].teasers, response)
            else:
                self.warn("can't find cluster of type '{}' in rubric-url '{}'", listType, rubricUrl)
        else:
            self._checkTeasers(rubricResource.teasers, rubricResource.configApiToken)
            self._renderTeasers(rubricResource.teasers, response)
            self._renderClusters(clusters, response, rubricUrl)
            
    
    def _resolveLazyloadTeasers(self, rubricResource):
        teaserLazyloadResolver = TeaserLazyloadResolver(self.log)
        for cluster in rubricResource.clusters:
            cluster.teasers.extend(teaserLazyloadResolver.resolveTeasers(cluster.lazyloadTeasers))
   
    def _renderClusters(self, clusters, response, rubricUrl):
        for cluster in clusters:
            clusterTitle = cluster.title #.encode('ascii', 'ignore')
            action = Action(pagelet='RubricPage', params={'rubricUrl': rubricUrl, 'listType': cluster.listType, 'listStart': str(cluster.listStart), 'listEnd': str(cluster.listEnd)})
            item = Item(cluster.title, action, cluster.image, isFolder=True)
            response.addItem(item)            
    
    
    def _checkTeasers(self, teasers, apiToken):
        for teaser in teasers:
            if teaser.image is None and teaser.contentName is not None:
                videoContentUrl = Constants.apiContentUrl + teaser.contentName + '.json?profile=player'
                self.debug("downloading video-content-url '{1}' ...", videoContentUrl)
                videoContent = VideoContentResource(videoContentUrl, Constants.apiBaseUrl, apiToken)
                self._parse(videoContent)
                teaser.image = videoContent.image
                    
    def _renderTeasers(self, teasers, response):
        for teaser in teasers:
            item = self._createItem(teaser)
            if item is not None:
                response.addItem(item)
            else:
                self.warn("can't find content-name for teaser-url '{}' and teaser-title '{}', skipping item ...", teaser.url, teaser.title)
        