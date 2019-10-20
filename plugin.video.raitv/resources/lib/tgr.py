# -*- coding: utf-8 -*-
try:
  import urllib.request as urllib2
except ImportError:
    import urllib2
from xml.dom import minidom

class TGR:
    _baseurl = "http://www.tgr.rai.it"
    
    def getProgrammes(self):
        url = "http://www.tgr.rai.it/dl/tgr/mhp/home.xml"
        xmldata = urllib2.urlopen(url).read()
        dom = minidom.parseString(xmldata)
        
        programmes = []
        for node in dom.getElementsByTagName('item'):
            item = {}
            # behaviour = {region, select, list}
            item["behaviour"] = node.attributes["behaviour"].value
            item["title"] = node.getElementsByTagName('label')[0].childNodes[0].data
            for url in  node.getElementsByTagName('url'):
                if url.attributes["type"].value == "image":
                    item["image"] = self._baseurl + url.childNodes[0].data
                elif url.attributes["type"].value == "list":
                    item["url"] = self._baseurl + url.childNodes[0].data
            programmes.append(item)
                
        return programmes
     
    def getList(self, url):
        xmldata = urllib2.urlopen(url).read()
        dom = minidom.parseString(xmldata)

        items = []
        for node in dom.getElementsByTagName('item'):
            item = {}
            # behaviour = {list, video}
            item["behaviour"] = node.attributes["behaviour"].value
            item["title"] = node.getElementsByTagName('label')[0].childNodes[0].data
            for url in  node.getElementsByTagName('url'):
                foundUrl = False
                if url.attributes["type"].value == "list":
                    item["url"] = self._baseurl + url.childNodes[0].data
                    foundUrl = True
                elif url.attributes["type"].value == "video":
                    if url.attributes["type"].value == "video":
                        item["url"] = url.childNodes[0].data
                        foundUrl = True
                if foundUrl:
                    items.append(item)
                
        return items
