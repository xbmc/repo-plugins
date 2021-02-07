from de.generia.kodi.plugin.backend.zdf.AbstractPageResource import AbstractPageResource

from de.generia.kodi.plugin.backend.zdf import stripHtml
from de.generia.kodi.plugin.backend.zdf.Regex import getTagPattern
from de.generia.kodi.plugin.backend.zdf.Regex import getTag
from de.generia.kodi.plugin.backend.zdf.Regex import compile
from de.generia.kodi.plugin.backend.zdf.Regex import stripTag

from de.generia.kodi.plugin.backend.zdf.Teaser import Teaser
from de.generia.kodi.plugin.backend.zdf.TeaserLazyload import TeaserLazyload

from urlparse import urlparse

fallbackTitlePattern = compile('<li\s*class="item current"[^>]*>[^<]*<a[^>]*>([^<]*)</a>')
fallbackTitlePattern2 = compile('<h\d\s*class="[^"]*stage-title[^"]*"[^>]*>([^<]*)</h\d>')

moduleItemPattern = getTagPattern('div', 'item-caption')
moduleItemTextPattern = compile('class="item-description"[^>]*>([^<]*)</?[^>]*>')
moduleItemDatePattern = compile('<time[^>]*>([^<]*)</time>')
moduleItemImagePattern = compile('class="item-img[^"]*"[^>]*data-srcset="([^"]*)"')
moduleItemVideoPattern = compile('&quot;1280x720&quot;:&quot;([^\?]*)\?cb')

postContentPattern = getTagPattern('div', 'details')

stageTeaserPattern = getTagPattern('div', 'title-table')
stageTeaserTextPattern = compile('class="teaser-text"[^>]*>([^<]*)</?[^>]*>')

listPattern = compile('class="([^"]*b-cluster|[^"]*b-cluster\s[^"]*|[^"]*b-content-teaser-list[^"]*|[^"]*b-group-persons[^"]*|[^"]*b-post-content[^"]*|[^"]*b-(content|video)-module[^"]*|[^"]*stage-content[^"]|[^"]*(b-topics-module|b-newsstream)[^"]*)"[^>]*>')

sectionTitlePattern = compile('<h2\s*class="[^"]*title[^"]*"[^>]*>([^<]*)</h2>')
sectionItemPattern = getTagPattern('article', 'b-content-teaser-item')

clusterTitlePattern = compile('<h2\s*class="[^"]*cluster-title[^"]*"[^>]*>([^<]*)</h2>')
clusterItemPattern = compile('<[^>]*class="([^"]*b-cluster-teaser[^"]*)"[^>]*>')

topicsModuleTitlePattern = compile('x-notitle|<h2\s*class="[^"]*big-headline[^"]*"[^>]*>([^<]*)</h2>')
newsStreamTitlePattern = compile('<h2\s*class="[^"]*visuallyhidden[^"]*"[^>]*>([^<]*)</h2>')

MODULE_TYPE_POST_CONTENT = 'post-content'
MODULE_TYPE_STAGE_TEASER = 'stage-teaser'
MODULE_TYPE_DEFAULT = 'default'

class Cluster(object):

    def __init__(self, title, listType, listStart, listEnd=-1, image=None):
        self.title = title
        self.listType = listType
        self.listStart = listStart
        self.listEnd = listEnd
        self.image = image
        self.teasers = []
        self.lazyloadTeasers = []
                        
    def __str__(self):
        return "<Cluster '%s' teasers='%d'>" % (self.title, len(self.teasers))
    
    
class RubricResource(AbstractPageResource):

    def __init__(self, url, listType=None, listStart=-1, listEnd=-1, image=None):
        super(RubricResource, self).__init__(url)
        self.listType = listType
        self.listStart = listStart
        self.listEnd = listEnd
        self.image = image
            
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
            
        self.isRedirect = len(self.clusters) == 0 and len(self.teasers) == 0 and self.responseLocation != self.url

    def _parseClusters(self):
            
        pos = 0
        title = None
        fallbackTitleMatch = fallbackTitlePattern.search(self.content, pos)
        if fallbackTitleMatch is None:
            fallbackTitleMatch = fallbackTitlePattern2.search(self.content, pos)
        if fallbackTitleMatch is not None:
            title = stripTag('span', fallbackTitleMatch.group(1))
            title = stripHtml(title)
            pos = fallbackTitleMatch.end(0)
        self.fallbackTitle = title
            
        match = listPattern.search(self.content, pos)
        while match is not None:
            pos = match.end(0)
            class_ = match.group(1)
            if self._isModule(class_):
                match = self._parseModule(pos, moduleItemPattern, moduleItemTextPattern, moduleItemDatePattern, MODULE_TYPE_DEFAULT)
            elif self._isPostContent(class_):
                match = self._parseModule(pos, postContentPattern, moduleItemTextPattern, moduleItemDatePattern, MODULE_TYPE_POST_CONTENT)
            elif self._isStageTeaser(class_):
                match = self._parseModule(pos, stageTeaserPattern, stageTeaserTextPattern, moduleItemDatePattern, MODULE_TYPE_STAGE_TEASER)
            elif self._isGroupPersons(class_):
                # just skip group persons, no teasers in this section
                match = listPattern.search(self.content, pos)
            else:
                match = self._parseCluster(pos, class_, title)

    def _isModule(self, class_):
        return class_.find('b-content-module') != -1
    
    def _isPostContent(self, class_):
        return class_.find('b-post-content') != -1
    
    def _isStageTeaser(self, class_):
        return class_.find('stage-content') != -1
    
    def _isGroupPersons(self, class_):
        return class_.find('b-group-persons') != -1
    
    def _parseModule(self, pos, contentPattern, textPattern, datePattern, moduleType):
        match = listPattern.search(self.content, pos)
        end = len(self.content)-1
        if match is not None:
            end = match.end(0)
        self._parseModuleRange(pos, end, contentPattern, textPattern, datePattern, moduleType)
        return match
    
    def _parseModuleRange(self, pos, end, contentPattern, textPattern, datePattern, moduleType, cluster=None):
        item = self.content[pos:end]
        pos = 0
        
        teaser = Teaser()
        pos = teaser.parseApiToken(item, pos)

        contentMatch = contentPattern.search(item, pos)
        if contentMatch is not None:
            pos = contentMatch.end(0)
            # the teaser image for videos is encoded in the video players json parameter 
            if teaser.apiToken is not None:
                p = teaser.parseImage(item, 0, moduleItemVideoPattern)
                image = teaser.image
                if image is not None:
                    image = image.replace('\\', '')
                    teaser.image = image
            else:
                p = teaser.parseImage(item, 0, moduleItemImagePattern)
            if moduleType == MODULE_TYPE_POST_CONTENT:
                url = urlparse(self.url)
                teaser.url = url.path
                teaser.title = self.fallbackTitle
            else:
                p = teaser.parseLabel(item, pos)
                p = teaser.parseCategory(item, p)
                p = teaser.parseTitle(item, p, self._getBaseUrl())
            p = teaser.parseText(item, p, textPattern)
            p = teaser.parseFoot(item, p)
            if teaser.valid():
                teasers = self.teasers
                if cluster is not None:
                    teasers = cluster.teasers
                teasers.append(teaser)
    
    def _parseCluster(self, pos, class_, fallbackTitle):
        titlePattern = clusterTitlePattern
        listType = 'cluster'
        if class_.find('b-content-teaser-list') != -1:
            titlePattern = sectionTitlePattern
            listType = 'content'
        elif class_.find('b-newsstream') != -1:
            titlePattern = newsStreamTitlePattern
            listType = 'cluster'
        elif class_.find('b-topics-module') != -1:
            titlePattern = topicsModuleTitlePattern
            listType = 'topics'
            
        titleMatch = titlePattern.search(self.content, pos)
        cluster = None
        title = fallbackTitle
        # if content-teaser-list has no title, use previous cluster to calculate list end
        if class_.find('b-content-teaser-list no-title') != -1:
            if len(self.clusters) > 0:
                cluster = self.clusters[len(self.clusters)-1]
            else:
                nextClusterMatch = listPattern.search(self.content, pos)
                tmpCluster = Cluster(None, listType, pos, nextClusterMatch.end(0))
                self._parseClusterTeasers(tmpCluster)
                self.teasers.extend(tmpCluster.teasers)
                return nextClusterMatch
                
        elif titleMatch is not None:
            # title can be None in case of 'x-notitle' in 'topics' list
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

        # use first teaser image as cluster image
        if cluster.image is None:
            tmpCluster = Cluster(None, listType, cluster.listStart, cluster.listEnd)
            self._parseClusterTeasers(tmpCluster, True)
            if len(tmpCluster.teasers) > 0:
                tmpTeaser = tmpCluster.teasers[0]
                cluster.image = tmpTeaser.image
                # use teaser.title as cluster fallback
                if cluster.title is None:
                    cluster.title = tmpTeaser.title

        return match
    
    def _parseClusterTeasers(self, cluster, firstTeaserOnly=False):
        itemPattern = sectionItemPattern
        if cluster.listType == 'cluster':
            itemPattern = clusterItemPattern
        pos = cluster.listStart
        itemMatch = itemPattern.search(self.content, pos)
        
        if cluster.listType == 'topics':
            moduleEnd = cluster.listEnd
            if itemMatch is not None and itemMatch.start() < cluster.listEnd:
                moduleEnd = itemMatch.start()
            self._parseModuleRange(pos, moduleEnd, moduleItemPattern, moduleItemTextPattern, moduleItemDatePattern, MODULE_TYPE_DEFAULT, cluster)
            pos = moduleEnd
            if firstTeaserOnly:
                return

        while pos < cluster.listEnd and itemMatch is not None:
            teaser = self._createTeaser(itemMatch, itemPattern)
            pos = teaser.parse(self.content, pos, self._getBaseUrl(), itemMatch)
            if teaser.valid():
                if isinstance(teaser, TeaserLazyload):
                    cluster.lazyloadTeasers.append(teaser)
                else:
                    cluster.teasers.append(teaser)
                if firstTeaserOnly:
                    return
            itemMatch = itemPattern.search(self.content, pos)
            if itemMatch is not None:
                pos = itemMatch.start(0)

    def _createTeaser(self, itemMatch, itemPattern):
        class_ = itemMatch.group(1)
        teaser = None
        if class_.find('lazyload') != -1:
            teaser = TeaserLazyload(itemPattern)
        else:
            teaser = Teaser()
        return teaser
