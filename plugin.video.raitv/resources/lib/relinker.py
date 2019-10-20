# -*- coding: utf-8 -*-
import urllib
try:
  import urllib.request as urllib2
except ImportError:
    import urllib2
try:
  import urllib.parse as urlparse
except ImportError:
    import urlparse
try:
    from urllib.parse import urlencode
except:
    from urllib import urlencode

class Relinker:
    # Firefox 52 on Android
    # UserAgent = "Mozilla/5.0 (Android; Mobile; rv:52.0) Gecko/52.0 Firefox/52.0"
    # Firefox 52 ESR on Windows 7
    # UserAgent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0"
    # Firefox 52 ESR on Linux
    # UserAgent = "Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0"
    # Chrome 64 on Windows 10
    # UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282 Safari/537.36"
    # Raiplay android app
    UserAgent = "Android 4.2.2 (smart) / RaiPlay 2.1.3 / WiFi"
    
    def __init__(self):
        opener = urllib2.build_opener()
        # Set User-Agent
        opener.addheaders = [('User-Agent', self.UserAgent)]
        urllib2.install_opener(opener)

    def getURL(self, url):
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)
        qs = urlparse.parse_qs(query)
    
        # output=20 url in body
        # output=23 HTTP 302 redirect
        # output=25 url and other parameters in body, space separated
        # output=44 XML (not well formatted) in body
        # output=47 json in body
        # pl=native,flash,silverlight
        # A stream will be returned depending on the UA (and pl parameter?)
        
        if "output" in qs:
            del(qs['output'])
        qs['output'] = "20"
        
        query = urlencode(qs, True)
        url = urlparse.urlunparse((scheme, netloc, path, params, query, fragment))
                
        response = urllib2.urlopen(url)
        mediaUrl = response.read().strip()
        
        # Workaround to normalize URL if the relinker doesn't
        try: mediaUrl = urllib.quote(mediaUrl, safe="%/:=&?~#+!$,;'@()*[]")
        except: mediaUrl = urllib.parse.quote(mediaUrl, safe="%/:=&?~#+!$,;'@()*[]")
        return mediaUrl

