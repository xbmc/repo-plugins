import urllib2
import cookielib
import os.path

class Fetcher:

    def __init__(self, logger, getTranslatedPath):
        self.logger = logger
        self.getTranslatedPath = getTranslatedPath

    def getHTML(self, url, headers = [('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')]):
        """
        url Might be a real URL object or a String-like thing.
        """
        try:
            url_string = url.get_full_url()
        except AttributeError:
            url_string = url
        self.logger('%s attempting to open %s with data' % (__name__, url_string))

        #create cookiejar
        cj = cookielib.LWPCookieJar()
        cookiefile = self.getTranslatedPath('special://temp/ted-cookies.lwp')
        #load any existing cookies
        if os.path.isfile(cookiefile):
            cj.load(cookiefile)
            #log what cookies were loaded
            for index, cookie in enumerate(cj):
                self.logger('loaded cookie : %s\nfrom %s' % (cookie, cookiefile))

        #build opener with automagic cookie handling abilities.
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = headers
        try:
            usock = opener.open(url)
            response = usock.read()
            usock.close()
            cj.save(cookiefile)
            return response
        except urllib2.HTTPError, error:
            self.logger('%s error:\n%s\n%s\n%s' % (__name__, error.code, error.msg, error.geturl()))
        except Exception, error:
            print Exception.__module__
            print dir(error)
