import urllib2
import re

class Relinker:
    # Rai.tv android app
    __USERAGENT = "Apache-HttpClient/UNAVAILABLE (java 1.4)"
    # Firefox 29 on Android
    # __USERAGENT = "Mozilla/5.0 (Android; Mobile; rv:29.0) Gecko/29.0 Firefox/29.0"
    # Firefox 29 on Windows 7
    # __USERAGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20100101 Firefox/29.0"
    # Firefox 29 on Linux
    # __USERAGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:29.0) Gecko/20100101 Firefox/29.0"
    

    def __init__(self):
        opener = urllib2.build_opener()
        # Set User-Agent
        opener.addheaders = [('User-Agent', self.__USERAGENT)]
        urllib2.install_opener(opener)

    def getURL(self, url):
        # output=20 url in body
        # output=23 HTTP 302 redirect
        # output=25 url and other parameters in body, space separated
        # output=44 XML (not well formatted) in body
        # pl=native,flash,silverlight
        # A stream will be returned depending on the UA (and pl parameter?)
        url = url + "&output=20"
        print "Relinker URL: %s" % url
        response = urllib2.urlopen(url)
        mediaUrl = response.read().strip()
        return mediaUrl
        