from de.generia.kodi.plugin.backend.web.HtmlResource import HtmlResource

from de.generia.kodi.plugin.backend.zdf import stripHtml
from de.generia.kodi.plugin.backend.zdf.Regex import getTagPattern
from de.generia.kodi.plugin.backend.zdf.Regex import getTag
from de.generia.kodi.plugin.backend.zdf.Regex import compile

from de.generia.kodi.plugin.backend.zdf.Teaser import Teaser

fallbackTitlePattern = compile('<li class="item current"[^>]*>[^<]*<a[^>]*>([^<]*)</a>')
'''
<li class="item current" itemprop="itemListElement" itemscope="" itemtype="http://schema.org/ListItem">
    
    
        <a href="/serien/die-chefin" class="link js-track-click" data-track="{&quot;element&quot;: &quot;Breadcrumb&quot;, &quot;action&quot;: &quot;Click_Breadcrumb&quot;, &quot;actionDetail&quot;: &quot;{textContent}&quot;}" itemprop="item">
    
    Die Chefin
    
        </a>
'''

listPattern = compile('<[^ ]*>[^>]*class="([^"]*b-cluster m-filter[^"]*|[^"]*b-content-teaser-list[^"]*)"[^>]*>')

sectionTitlePattern = compile('<h2 class="[^"]*title[^"]*"[^>]*>([^<]*)</h2>')
sectionItemPattern = getTagPattern('article', 'b-content-teaser-item')

clusterTitlePattern = compile('<h2 class="[^"]*cluster-title[^"]*"[^>]*>([^<]*)</h2>')
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

        self.clusters = []
        if self.listType is None:
            
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
                titlePattern = clusterTitlePattern
                listType = 'cluster'
                if class_.find('b-content-teaser-list') != -1:
                    titlePattern = sectionTitlePattern
                    listType = 'content'
                    
                titleMatch = titlePattern.search(self.content, pos)
                if titleMatch is not None:
                    title = stripHtml(titleMatch.group(1))
                    pos = titleMatch.end(0)
                    
                cluster = Cluster(title, listType, pos)
                self.clusters.append(cluster)
                
                match = listPattern.search(self.content, pos)

                if match is not None:
                    cluster.listEnd = match.start(0)-1
                else:
                    cluster.listEnd = len(self.content)-1

        else:
            cluster = Cluster(None, self.listType, self.listStart, self.listEnd)
            self.clusters.append(cluster)
            itemPattern = sectionItemPattern
            if self.listType == 'cluster':
                itemPattern = clusterItemPattern
            pos = self.listStart
            itemMatch = itemPattern.search(self.content, pos)
            while pos < self.listEnd and itemMatch is not None:
                teaser = Teaser()
                pos = teaser.parse(self.content, pos, itemMatch)
                if teaser.valid():
                    cluster.teasers.append(teaser)

                itemMatch = itemPattern.search(self.content, pos)
            
