import sys
import urllib
import urllib2
import httplib
import time
from xml.dom import minidom
from xml.parsers import expat

class Ansa:
    # Android
    __DEVICEVAL = "5"

    def getChannels(self):
        url = "http://ansa.cloudapp.net/ANSA2.0/getCategory.aspx?device=" + self.__DEVICEVAL
        xmldata = urllib2.urlopen(url).read()
        dom = minidom.parseString(xmldata)

        channels = []
        for node in dom.getElementsByTagName('video')[0].childNodes:
            if node.nodeType==node.ELEMENT_NODE:
                channel = {}
                channel["title"] = node.getElementsByTagName('name')[0].childNodes[0].data
                channel["url"] =  node.getElementsByTagName('feed')[0].childNodes[0].data
                channel["url"] = channel["url"].replace("DEVICE_VAL", self.__DEVICEVAL)
                channels.append(channel)
       
        return channels

    def getVideoByChannel(self, url):
        # Questi feed non sono aggiornati quanto le sezioni presenti sul sito www.ansa.it
        xmldata = urllib2.urlopen(url).read()
        dom = minidom.parseString(xmldata)

        videos = []
        for videoNode in dom.getElementsByTagName('item'):
            video = {}
            try:
                video["title"] = videoNode.getElementsByTagName('title')[0].childNodes[0].data
            except IndexError: 
                # Alcune video notizie sono prive di titolo
                video["title"] = ""
            dateTime = videoNode.getElementsByTagName('data_trasmissione')[0].childNodes[0].data
            video["date"] = time.strptime(dateTime, "%d/%m/%Y %H:%M")
            thumb = videoNode.getElementsByTagName('thumb')[0].childNodes[0].data
            # Cambiamo il resize in modo che w=256
            video["thumb"] = thumb.replace("&w=180&h=135", "&w=256&h=144")
            video["url"] = videoNode.getElementsByTagName('video')[0].childNodes[0].data
            videos.append(video)
            
        return videos
