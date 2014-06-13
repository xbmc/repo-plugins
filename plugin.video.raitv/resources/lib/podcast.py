import urllib2
import email.utils
import time
from xml.dom import minidom
from xml.parsers import expat

class Podcast:
    def getItems(self, url):
        # RSS 2.0 only
        print "Podcast URL: %s" % url
        xmldata = urllib2.urlopen(url).read()
        dom = minidom.parseString(xmldata)
        
        podThumbnail = ""
        podImageNode = dom.getElementsByTagName('itunes:image')
        if podImageNode.length == 1:
            podThumbnail = podImageNode[0].attributes["href"].value
        

        items = []
        for itemNode in dom.getElementsByTagName("item"):
            title = itemNode.getElementsByTagName('title')[0].firstChild.data
            
            # description can be missing
            descriptionNode = itemNode.getElementsByTagName('description')
            if descriptionNode.length >= 1:
                description = descriptionNode[0].firstChild.data
            else:
                description =  ""
            
            pubDate = itemNode.getElementsByTagName('pubDate')[0].firstChild.data
            pubDate = email.utils.mktime_tz(email.utils.parsedate_tz(pubDate))
            
            # itunes:duration can be missing
            durationNode = itemNode.getElementsByTagName('itunes:duration')
            if durationNode >= 1:
                length = durationNode[0].firstChild.data
            else:
                length = ""

            mediaNode = itemNode.getElementsByTagName('media:content')
            if mediaNode.length >= 1:
                url = mediaNode[0].attributes["url"].value
            else:
                enclosure = itemNode.getElementsByTagName('enclosure')
                url = enclosure[0].attributes["url"].value
        
            thumbNode = itemNode.getElementsByTagName('media:thumbnail')
            if thumbNode.length == 1:
                thumbnail = thumbNode[0].attributes["url"].value
            elif podThumbnail != "":
                thumbnail = podThumbnail
            
            items.append({
                'title': title,
                'description': description, 
                'length' : length,
                'thumbnail': thumbnail,
                'date': time.strftime("%d.%m.%Y", time.localtime(pubDate)),
                'url': url
            })

        return items