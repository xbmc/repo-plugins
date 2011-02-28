import urllib2
import cookielib
import os.path
import re
import sys
import xbmc

pluginName = sys.modules['__main__'].__plugin__


def getHTML(url, cookiefile = xbmc.translatePath('special://temp/asi-cookies.lwp'), headers = [('User-Agent', 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10')]):
    """Return HTML from a given URL"""
    try:
        print '[%s] %s attempting to open %s with data' % (pluginName, __name__, url.get_full_url())
    except:
        print '[%s] %s attempting to open %s' % (pluginName, __name__, url)
    # create cookiejar
    cj = cookielib.LWPCookieJar()
    # load any existing cookies
    if os.path.isfile(cookiefile):
        cj.load(cookiefile)
        # log what cookies were loaded
        for index, cookie in enumerate(cj):
            print '[%s] loaded cookie : %s\nfrom %s' % (pluginName, cookie, cookiefile)
    # build opener with automagic cookie handling abilities.
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

def cleanHTML(html):
    """Return a clean HTML to help beautifulsoup and the parsing"""
    # Remove the double double quotes in title
    # (otherwise beautifulsoup just get an empty string)
    html = re.sub('title=""(.+)"">', 'title="\\1">', html)
    # Replace html-encoded nonbreaking space
    html = html.replace('&nbsp;', ' ')
    return html

