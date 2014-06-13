import sys
import urllib
import urllib2
import httplib
import re

class SuperTennis:
    __USERAGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0"

    def __init__(self):
        opener = urllib2.build_opener()
        # Use Firefox User-Agent
        opener.addheaders = [('User-Agent', self.__USERAGENT)]
        urllib2.install_opener(opener)

    def getUrl(self):
        pageUrl = "http://www.federtennis.it/supertennis/"
        htmlData = urllib2.urlopen(pageUrl).read()
        
        match=re.compile('file: "sttvroma\?(.+?)"').findall(htmlData)
        uniqueId = match[0]

        url = "rtmp://fml.6F9F.edgecastcdn.net/206F9F/sttv app=206F9F/sttv playpath=sttvroma?%s subscribe=sttvroma?%s tcUrl=rtmp://fml.6F9F.edgecastcdn.net/206F9F/sttv swfUrl=http://www.federtennis.it/supertennis/jwplayer-5.10/player.swf pageUrl=http://www.federtennis.it/supertennis/ live=true timeout=20" % (uniqueId, uniqueId)
       
        return url
