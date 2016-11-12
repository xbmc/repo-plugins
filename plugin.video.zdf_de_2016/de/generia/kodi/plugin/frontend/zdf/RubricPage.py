from de.generia.kodi.plugin.backend.zdf.RubricResource import RubricResource       

from de.generia.kodi.plugin.frontend.base.Pagelet import Item        
from de.generia.kodi.plugin.frontend.base.Pagelet import Action        
from de.generia.kodi.plugin.frontend.base.Pagelet import Pagelet        

from de.generia.kodi.plugin.frontend.zdf.Constants import Constants
from de.generia.kodi.plugin.frontend.zdf.ItemPage import ItemPage


class RubricPage(ItemPage):

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
                self._renderCluster(clusters[0], response, apiToken)
            else:
                self.warn("can't find cluster of type '{}' in rubric-url '{}'", listType, rubricUrl)
        else:
            self._renderClusters(clusters, response, apiToken, rubricUrl)
            
        
    def _renderClusters(self, clusters, response, apiToken, rubricUrl):
        for cluster in clusters:
            clusterTitle = cluster.title #.encode('ascii', 'ignore')
            action = Action(pagelet='RubricPage', params={'apiToken': apiToken, 'rubricUrl': rubricUrl, 'listType': cluster.listType, 'listStart': str(cluster.listStart), 'listEnd': str(cluster.listEnd)})
            item = Item(cluster.title, action, isFolder=True)
            response.addItem(item)            
    
    def _renderCluster(self, cluster, response, apiToken):
        for teaser in cluster.teasers:
            item = self._createItem(teaser, apiToken)
            if item is not None:
                response.addItem(item)
            else:
                self.warn("can't find content-name for teaser-url '{}' and teaser-title '{}', skipping item ...", teaser.url, teaser.title)
        