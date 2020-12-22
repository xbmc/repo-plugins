import re
import urllib
from json import JSONDecoder
from datetime import datetime

from de.generia.kodi.plugin.backend.zdf.Regex import getAttrPattern
from de.generia.kodi.plugin.backend.zdf.Teaser import Teaser


def getJsonAttrPattern(attr):
    return re.compile('&quot;' + attr + '&quot;\s*:\s*&quot;([^&]*)&quot;', re.DOTALL)

idPattern = getJsonAttrPattern('sophoraId')
stylePattern = getJsonAttrPattern('style')
headlinePattern = getJsonAttrPattern('teaserHeadline')
textPattern = getJsonAttrPattern('teasertext')
sourceModuleTypePattern = getJsonAttrPattern('sourceModuleType')


class TeaserLazyload(object):
    url = None
    
    def __init__(self, teaserPattern):
        self.teaserPattern = teaserPattern
                    
    def valid(self):
        return self.url is not None
     
    def __str__(self):
        return "<TeaserLazyload url='%s'>" % (self.url)
        

    def parse(self, string, pos=0, baseUrl=None, teaserMatch=None):
        if teaserMatch is None:
            return -1
        teaser = teaserMatch.group(0)
        endPos = teaserMatch.end(0)

        teaser = teaser.replace('\&quot;', '\\"');
        jsonDecoder = JSONDecoder('UTF-8')

        id = self._parseAttr(jsonDecoder, teaser, idPattern)
        style = self._parseAttr(jsonDecoder, teaser, stylePattern)
        headline = self._parseAttr(jsonDecoder, teaser, headlinePattern)
        text = self._parseAttr(jsonDecoder, teaser, textPattern)
        sourceModuleType = self._parseAttr(jsonDecoder, teaser, sourceModuleTypePattern)
        
        url = None
        url = self._appendUrl(url, 'sophoraId', id)
        url = self._appendUrl(url, 'style', style)
        url = self._appendUrl(url, 'teaserHeadline', headline)
        url = self._appendUrl(url, 'teasertext', text)
        url = self._appendUrl(url, 'sourceModuleType', sourceModuleType)
        
        if url is not None:
            url = baseUrl + '/teaserElement' + url
        self.url = url
        self.baseUrl = baseUrl
        
        return endPos

    def _parseAttr(self, jsonDecoder, teaser, pattern):
        match = pattern.search(teaser)
        value = None
        if match is not None:
            value = match.group(1)

            if value is not None:
                #print ("_parseAttr", value)
                obj = '{"s":"' + value + '"}'
                entry = jsonDecoder.decode(obj)
                if entry is not None:
                    value = entry['s']

        return value


    def _appendUrl(self, url, attr, value):
        if value is None:
            return url
        encodedValue = urllib.quote(value.encode('UTF-8'), '')
        if url is None:
            return '?' + attr + '=' + encodedValue
         
        return url + '&' + attr + '=' + encodedValue 
    