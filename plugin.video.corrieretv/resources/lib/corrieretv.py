import urllib2
import time
from xml.dom import minidom
from BeautifulSoup import BeautifulSoup

class CorriereTV:
    __USERAGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0"

    def __init__(self):
        opener = urllib2.build_opener()
        # Use Firefox User-Agent
        opener.addheaders = [('User-Agent', self.__USERAGENT)]
        urllib2.install_opener(opener)

    def getChannels(self):
        pageUrl = "http://www.corriere.it/rss/"
        data = urllib2.urlopen(pageUrl).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        links = tree.find("div", {"id": "rss"}).findAll("a")
        channels = []
        for link in links:
            channel = {}
            channel["title"] = link.text
            channel["url"] = link["href"]
            if channel["url"].find("http://static.video.corriereobjects.it/widget/content/playlist/xml/") == -1:
                continue
            channel["url"] = channel["url"].replace("http://static.video.corriereobjects.it/widget/content/playlist/xml/playlist_",
                "http://static.video.corriereobjects.it/widget/content/playlist/playlist_")
            channel["url"] = channel["url"].replace("_dateDesc.xml", "_dateDesc.rss")
            channels.append(channel)
        
        return channels

    def getVideoByChannel(self, url):
        # RSS 2.0 only
        xmldata = urllib2.urlopen(url).read()
        dom = minidom.parseString(xmldata)

        videos = []
        for videoNode in dom.getElementsByTagName('item'):
            video = {}
            videoId = videoNode.getElementsByTagName('guid')[0].firstChild.data
            video["title"] = videoNode.getElementsByTagName('title')[0].firstChild.data.strip()
            # print video["title"].encode('utf-8')
            
            try:
                video["description"] = videoNode.getElementsByTagName('description')[0].firstChild.data
            except:
                video["description"] = ""
            dt = videoNode.getElementsByTagName('pubDate')[0].firstChild.data
            t = time.strptime(dt, '%Y-%m-%dT%H:%M:%S.%fZ')
            video["date"] = t

            video["url"] = videoNode.getElementsByTagName('media:content')[0].attributes["url"].value
            video["url"] = video["url"].replace("/z/", "/i/").replace("manifest.f4m","master.m3u8")
            thumbs = videoNode.getElementsByTagName('media:thumbnail')
            video["thumb"] = ""
            for thumb in thumbs:
                width = thumb.attributes["width"].value
                if width == "298" or width == "367" or width == "480":
                    video["thumb"] = thumb.attributes["url"].value
                    break

            videos.append(video)
            
        return videos
