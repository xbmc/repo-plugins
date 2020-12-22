import urllib
import urllib2
import ssl

from urlparse import urlparse

class Resource(object):

    def __init__(self, url, accept):
        self.url = url
        self.accept = accept
        self.responseLocation = None
        
    def parse(self):
        log = None
        if hasattr(self, 'log'):
            log = self.log
        if log is not None:
            log.info("[{}] - Timer - loading url='{}' ...", type(self).__name__, self.url)
            start = log.start()
        self.content = self._getUrl();
        if log is not None:
            log.info("[{}] - Timer - loading url='{}' ... done. [{} ms]", type(self).__name__, self.url, log.stop(start))

    def _getBaseUrl(self):
        parts = urlparse(self.url)
        baseUrl = parts.scheme + "://" + parts.hostname
        return baseUrl
        
    def _getUrl(self):
        #print "_getUrl: " + self.url
        request = self._createRequest()
        # check, if ssl has certificate verification by default and turn it off
        if '_create_unverified_context' in dir(ssl):
            response = urllib2.urlopen(request, context=ssl._create_unverified_context())
        else:
            response = urllib2.urlopen(request)
        
        if response.url is not None:    
            self.responseLocation = response.url
            
        content = response.read()
        response.close()
        return content
                
    def _createRequest(self):
        request = urllib2.Request(self.url)
        request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:22.0) Gecko/20100101 Firefox/22.0')        
        request.add_header('Accept', self.accept)
        return request
    
    
    def _getAbsoluteUrl(self, baseUrl, url):
        if url.find("://") != -1:
            return url
       
        parts = urlparse(baseUrl)        
        if url.startswith("/"):
            return parts.scheme + "://" + parts.hostname + url
        
        i = baseUrl.rfind("/")
        if i != -1:
            baseUrl = baseUrl[:i]
        return baseUrl + "/" + url