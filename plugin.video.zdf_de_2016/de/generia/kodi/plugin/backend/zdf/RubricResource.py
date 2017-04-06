from de.generia.kodi.plugin.backend.web.HtmlResource import HtmlResource

from de.generia.kodi.plugin.backend.zdf import stripHtml
from de.generia.kodi.plugin.backend.zdf.Regex import getTagPattern
from de.generia.kodi.plugin.backend.zdf.Regex import getTag
from de.generia.kodi.plugin.backend.zdf.Regex import compile

from de.generia.kodi.plugin.backend.zdf.Teaser import Teaser

fallbackTitlePattern = compile('<li\s*class="item current"[^>]*>[^<]*<a[^>]*>([^<]*)</a>')

moduleItemPattern = getTagPattern('div', 'item-caption')
moduleItemTextPattern = compile('class="item-description"[^>]*>([^<]*)<span')
moduleItemDatePattern = compile('<time[^>]*>([^<]*)</time>')

listPattern = compile('class="([^"]*b-cluster|[^"]*b-cluster [^"]*|[^"]*b-content-teaser-list[^"]*|[^"]*b-content-module[^"]*)"[^>]*>')

sectionTitlePattern = compile('<h2\s*class="[^"]*title[^"]*"[^>]*>([^<]*)</h2>')
sectionItemPattern = getTagPattern('article', 'b-content-teaser-item')

clusterTitlePattern = compile('<h2\s*class="[^"]*cluster-title[^"]*"[^>]*>([^<]*)</h2>')
clusterItemPattern = getTagPattern('article', 'b-cluster-teaser')

class Cluster(object):

    def __init__(self, title, listType, listStart, listEnd=-1):
        self.title = title
        self.listType = listType
        self.listStart = listStart
        self.listEnd = listEnd
        self.teasers = []
                        
    def __str__(self):
        return "<Cluster '%s' teasers='%d'>" % (self.title, len(self.teasers))
    
    
class RubricResource(HtmlResource):

    def __init__(self, url, listType=None, listStart=-1, listEnd=-1):
        super(RubricResource, self).__init__(url)
        self.listType = listType
        self.listStart = listStart
        self.listEnd = listEnd
            
    #
    # NOTE: content-teaser-lists and cluster-teaser-lists can occur in arbitrary order
    #
    def parse(self):
        super(RubricResource, self).parse()

        self.teasers = []
        self.clusters = []
        if self.listType is None:
            self._parseClusters()
            # return teasers directly, if there is only one cluster
            if len(self.clusters) == 1:
                cluster = self.clusters[0]
                self._parseClusterTeasers(cluster)
                self.teasers.extend(cluster.teasers)
                self.clusters = []
        else:
            cluster = Cluster(None, self.listType, self.listStart, self.listEnd)
            self.clusters.append(cluster)
            self._parseClusterTeasers(cluster)
            
    def _parseClusters(self):
            
        pos = 0
        title = None
        fallbackTitleMatch = fallbackTitlePattern.search(self.content, pos)
        if fallbackTitleMatch is not None:
            title = stripHtml(fallbackTitleMatch.group(1))
            pos = fallbackTitleMatch.end(0)
            
        match = listPattern.search(self.content, pos)
        while match is not None:
            pos = match.end(0)
            class_ = match.group(1)
            if class_.find('b-content-module') != -1:
                match = self._parseModule(pos)
            else:
                match = self._parseCluster(pos, class_, title)

    def _parseModule(self, pos):
        match = listPattern.search(self.content, pos)

        moduleItemMatch = moduleItemPattern.search(self.content, pos)
        if moduleItemMatch is not None:
            pos = moduleItemMatch.end(0)
            end = len(self.content)-1
            if match is not None:
                end = match.end(0)
            item = self.content[pos:end]
            teaser = Teaser()
            p = teaser.parseLabel(item, 0)
            p = teaser.parseCategory(item, p)
            p = teaser.parseTitle(item, p, self._getBaseUrl())
            p = teaser.parseText(item, p, moduleItemTextPattern)
            p = teaser.parseDate(item, p, moduleItemDatePattern)
            if teaser.valid():
                self.teasers.append(teaser)

        return match
         
    def _parseCluster(self, pos, class_, fallbackTitle):
        titlePattern = clusterTitlePattern
        listType = 'cluster'
        if class_.find('b-content-teaser-list') != -1:
            titlePattern = sectionTitlePattern
            listType = 'content'
            
        titleMatch = titlePattern.search(self.content, pos)
        cluster = None
        title = fallbackTitle
        if class_.find('x-notitle') != -1:
            if len(self.clusters) > 0:
                cluster = self.clusters[len(self.clusters)-1]
        elif titleMatch is not None:
            title = stripHtml(titleMatch.group(1))
            pos = titleMatch.end(0)

        if cluster is None:
            cluster = Cluster(title, listType, pos)
            self.clusters.append(cluster)
        
        match = listPattern.search(self.content, pos)

        if match is not None:
            cluster.listEnd = match.start(0)-1
        else:
            cluster.listEnd = len(self.content)-1
        return match
    
    def _parseClusterTeasers(self, cluster):
        itemPattern = sectionItemPattern
        if cluster.listType == 'cluster':
            itemPattern = clusterItemPattern
        pos = cluster.listStart
        itemMatch = itemPattern.search(self.content, pos)
        while pos < cluster.listEnd and itemMatch is not None:
            teaser = Teaser()
            pos = teaser.parse(self.content, pos, self._getBaseUrl(), itemMatch)
            if teaser.valid():
                cluster.teasers.append(teaser)

            itemMatch = itemPattern.search(self.content, pos)
            if itemMatch is not None:
                pos = itemMatch.start(0)
