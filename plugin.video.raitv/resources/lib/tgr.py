# -*- coding: utf-8 -*-
import sys
from xml.dom import minidom
import resources.lib.utils as utils

PY3 = sys.version_info.major >= 3

if PY3:
    import urllib.request as urllib2
else:
    import urllib2


class TGR:
    _baseurl = "http://www.tgr.rai.it"
    
    def getProgrammes(self):
        url = "http://www.tgr.rai.it/dl/tgr/mhp/home.xml"
        try:
            xmldata = urllib2.urlopen(url).read()
            xmldata = utils.checkStr(xmldata)
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
        
        except:
            return []
     
    def getList(self, url):
        
        try:
            xmldata = urllib2.urlopen(url).read()
            xmldata = utils.checkStr(xmldata)
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

        except:
            return []
        
