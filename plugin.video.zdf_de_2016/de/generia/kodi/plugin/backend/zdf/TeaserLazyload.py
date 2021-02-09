import re
import urllib
from json import JSONDecoder
from datetime import datetime

from de.generia.kodi.plugin.backend.zdf.Regex import getAttrPattern
from de.generia.kodi.plugin.backend.zdf.Teaser import Teaser

teaserXhrUrlAttrPattern = getAttrPattern("data-teaser-xhr-url")


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
        
        urlMatch = teaserXhrUrlAttrPattern.search(teaser)
        url = None
        if urlMatch is not None:
            url = urlMatch.group(1)
            url = url.replace("&amp;", "&")

        self.url = url
        self.baseUrl = baseUrl
        
        return endPos
