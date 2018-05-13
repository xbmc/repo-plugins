import urllib
from datetime import datetime

from de.generia.kodi.plugin.backend.zdf.Regex import getAttrPattern
from de.generia.kodi.plugin.backend.zdf.Teaser import Teaser

idPattern = getAttrPattern('data-teaser-id')
typePattern = getAttrPattern('data-teaser-type')
stylePattern = getAttrPattern('data-teaser-style')
headlinePattern = getAttrPattern('data-teaser-headline')
textPattern = getAttrPattern('data-teaser-text')
sourceModuleTypePattern = getAttrPattern('data-source-module-type')
titlePattern = getAttrPattern('data-cluster-title')


class TeaserLazyload(object):

    def __init__(self, teaserPattern):
        self.teaserPattern = teaserPattern
                    
    def valid(self):
        return True 
     
    def __str__(self):
        return "<TeaserLazyload url='%s'>" % (self.url)
        

    def parse(self, string, pos=0, baseUrl=None, teaserMatch=None):
        if teaserMatch is None:
            return -1
        teaser = teaserMatch.group(0)

        endPos = teaserMatch.end(0)
        id = self._parseAttr(teaser, idPattern)
        type = self._parseAttr(teaser, typePattern)
        style = self._parseAttr(teaser, stylePattern)
        headline = self._parseAttr(teaser, headlinePattern)
        text = self._parseAttr(teaser, textPattern)
        sourceModuleType = self._parseAttr(teaser, sourceModuleTypePattern)
        title = self._parseAttr(teaser, titlePattern)
        
        url = None
        url = self._appendUrl(url, 'sophoraId', id)
        url = self._appendUrl(url, 'type', type)
        url = self._appendUrl(url, 'sourceModuleType', sourceModuleType)
        url = self._appendUrl(url, 'style', style)
        url = self._appendUrl(url, 'teaserHeadline', headline)
        url = self._appendUrl(url, 'teasertext', text)
        url = self._appendUrl(url, 'clusterTitle', title)
        
        url = baseUrl + '/teaserElement' + url
        self.url = url
        self.baseUrl = baseUrl
        print "teaser-lazyload: " + url      
        
        return endPos

    def _parseAttr(self, teaser, pattern):
        match = pattern.search(teaser)
        value = None
        if match is not None:
            value = match.group(1)
        return value


    def _appendUrl(self, url, attr, value):
        encodedValue = urllib.quote(value, '')
        if url is None:
            return '?' + attr + '=' + encodedValue
         
        return url + '&' + attr + '=' + encodedValue 
    