import urllib2
from xml.dom import minidom
import time
import datetime
import re
from email.utils import parsedate_tz
from email.utils import mktime_tz
from BeautifulSoup import BeautifulSoup
import xbmc

class GuardianTV:
    __USERAGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0"
    
    def __init__(self):
        opener = urllib2.build_opener()
        # Use Firefox User-Agent
        opener.addheaders = [('User-Agent', self.__USERAGENT)]
        urllib2.install_opener(opener)
        
    def getLatestVideoURL(self):
        return "http://www.theguardian.com/video/rss"

    def getChannels(self):
        pageUrl = "http://www.theguardian.com/video"
        data = urllib2.urlopen(pageUrl).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        links = tree.find("div", {"id": "editor-zone-1"}).findAll("a")
        channels = []
        for link in links:
            channel = {}
            channel["title"] = link.text
            channel["url"] = link["href"]
            channel["url"] = channel["url"] + "/rss"
            channels.append(channel)
        
        return channels
        
    def getSeries(self):
        pageUrl = "http://www.theguardian.com/video"
        data = urllib2.urlopen(pageUrl).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        links = tree.find("div", {"id": "editor-zone-2"}).find("ul", {"class": "tri trail trailblock"}).findAll("a")
        channels = []
        for link in links:
            channel = {}
            channel["title"] = link.text
            channel["url"] = link["href"]
            channel["url"] = channel["url"] + "/rss"
            channels.append(channel)
        
        return channels
        
    def getVideoByChannel(self, url):
        # RSS 2.0 only
        xmldata = urllib2.urlopen(url).read()
        dom = minidom.parseString(xmldata)

        videos = []
        for videoNode in dom.getElementsByTagName('item'):
            video = {}
            video["title"] = videoNode.getElementsByTagName('title')[0].firstChild.data.strip()
            
            try:
                video["description"] = videoNode.getElementsByTagName('description')[0].firstChild.data
            except:
                video["description"] = ""
            dt = videoNode.getElementsByTagName('pubDate')[0].firstChild.data
            video["date"] = time.gmtime((mktime_tz(parsedate_tz(dt))))
            
            for mediaContent in videoNode.getElementsByTagName('media:content'):
                mimeType = mediaContent.attributes["type"].value
                if mimeType == "video/mp4" or mimeType == "video/mpeg4":
                    video["url"] = mediaContent.attributes["url"].value
                if mimeType == "image/jpeg":
                    video["thumb"] = mediaContent.attributes["url"].value

            if "url" not in video:
                # Parse the HTML page to get the Video URL
                pageUrl = videoNode.getElementsByTagName('link')[0].firstChild.data.strip()
                htmlData = urllib2.urlopen(pageUrl).read()
                match = re.compile("file\s+: '(.+?)'").findall(htmlData)
                if match:
                    video["url"] = match[0]

            videos.append(video)
            
        return videos
