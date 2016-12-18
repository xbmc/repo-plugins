from de.generia.kodi.plugin.backend.zdf.RubricResource import RubricResource       
from de.generia.kodi.plugin.backend.zdf.api.VideoContentResource import VideoContentResource

from de.generia.kodi.plugin.frontend.base.Pagelet import Item        
from de.generia.kodi.plugin.frontend.base.Pagelet import Action        

from de.generia.kodi.plugin.frontend.zdf.AbstractPage import AbstractPage
from de.generia.kodi.plugin.frontend.zdf.Constants import Constants


class RubricPage(AbstractPage):

    def service(self, request, response):
        apiToken = request.getParam('apiToken')
        rubricUrl = request.getParam('rubricUrl')
        listType = request.getParam('listType')
        listStart = int(request.getParam('listStart', -1))
        listEnd = int(request.getParam('listEnd', -1))
        
        self.info("rubric-page: url='{}', listType='{}', listStart='{}', listEnd='{}'", rubricUrl, listType, listStart, listEnd)

        rubricResource = RubricResource(Constants.baseUrl + rubricUrl, listType, listStart, listEnd)
        self._parse(rubricResource)
        clusters = rubricResource.clusters
        
        if listType is not None:
            if len(clusters) == 1:
                self._renderTeasers(clusters[0].teasers, response, apiToken)
            else:
                self.warn("can't find cluster of type '{}' in rubric-url '{}'", listType, rubricUrl)
        else:
            self._checkTeasers(rubricResource.teasers, apiToken)
            self._renderTeasers(rubricResource.teasers, response, apiToken)
            self._renderClusters(clusters, response, apiToken, rubricUrl)
            
        
    def _renderClusters(self, clusters, response, apiToken, rubricUrl):
        for cluster in clusters:
            clusterTitle = cluster.title #.encode('ascii', 'ignore')
            action = Action(pagelet='RubricPage', params={'apiToken': apiToken, 'rubricUrl': rubricUrl, 'listType': cluster.listType, 'listStart': str(cluster.listStart), 'listEnd': str(cluster.listEnd)})
            item = Item(cluster.title, action, isFolder=True)
            response.addItem(item)            
    
    
    def _checkTeasers(self, teasers, apiToken):
        for teaser in teasers:
            if teaser.image is None and teaser.contentName is not None:
                videoContentUrl = Constants.apiBaseUrl + '/content/documents/' + teaser.contentName + '.json?profile=player'
                self.debug("downloading video-content-url '{1}' ...", videoContentUrl)
                videoContent = VideoContentResource(videoContentUrl, Constants.apiBaseUrl, apiToken)
                self._parse(videoContent)
                teaser.image = videoContent.image
                    
    def _renderTeasers(self, teasers, response, apiToken):
        for teaser in teasers:
            item = self._createItem(teaser, apiToken)
            if item is not None:
                response.addItem(item)
            else:
                self.warn("can't find content-name for teaser-url '{}' and teaser-title '{}', skipping item ...", teaser.url, teaser.title)
        