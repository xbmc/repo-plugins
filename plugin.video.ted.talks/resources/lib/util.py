import urllib2
import cookielib
import os.path
import re
import sys

pluginName = sys.modules['__main__'].__plugin__


def getHTML(url, cookiefile = 'special://temp/ted-cookies.lwp', headers = [('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')]):
    """Returns HTML from a given URL"""
    try:
        print '[%s] %s attempting to open %s with data' % (pluginName, __name__, url.get_full_url())
    except:
        print '[%s] %s attempting to open %s' % (pluginName, __name__, url)
    #create cookiejar
    cj = cookielib.LWPCookieJar()
    #load any existing cookies
    if os.path.isfile(cookiefile):
        cj.load(cookiefile)
        #log what cookies were loaded
        for index, cookie in enumerate(cj):
            print '[%s] loaded cookie : %s\nfrom %s' % (pluginName, cookie, cookiefile)
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
        print '[%s] %s error:\n%s\n%s\n%s' % (pluginName, __name__, error.code, error.msg, error.geturl())
    except Exception, error:
        print Exception.__module__
        print dir(error)


def getUrllib2ResponseObject(url):
    return urllib2.urlopen(url)


def cleanHTML(s, noBS=False):
    """(string[, noBS=False])
    The 2nd half of this removes HTML tags.
    The 1st half deals with the fact that BeautifulSoup sometimes spits
    out a list of NavigableString objects instead of a regular string.
    This only happens when there are HTML elements, so it made sense to
    fix both problems in the same function.
    Passing noBS=True bypasses the BeautifulSoup stuff."""
    if not noBS:
        tmp = list()
        for ns in s:
            tmp.append(str(ns))
        s = ''.join(tmp)
    s = re.sub('\s+', ' ', s) #remove extra spaces
    s = re.sub('<.+?>|Image:.+?\r|\r', '', s) #remove htmltags, image captions, & newlines
    s = s.replace('&#39;', '\'') #replace html-encoded single-quotes
    s = s.replace('&quot;', '"') #replace html-encoded double-quotes
    s = s.replace('&nbsp;', ' ') #replace html-encoded nonbreaking space
    s = s.strip()
    return s


def resizeImage(imagePath):
    return imagePath.replace('132x99', '291x218')
