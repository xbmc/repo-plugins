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
        pageUrl = "http://eventi.liveksoft.tv/supertennis.tv/liveadv.php"
        htmlData = urllib2.urlopen(pageUrl).read()
        
        # HD Stream 1280x720px
        match=re.compile("var videoFile = '(.+?)'").findall(htmlData)
        # SD Stream 480x270px
        #match=re.compile("var videoFile5 = '(.+?)'").findall(htmlData)
        url = match[0]
       
        return url
