'''
gethtml with cookies support  v1
by anarchintosh @ xbmcforums
Copyleft = GNU GPL v3 (2011 onwards)

this function is paired with weblogin.py
and is intended to make it easier for coders wishing
to scrape source of pages, while logged in to that site.

USAGE:
!!!!!First set the compatible_urllist below!!!!!!!!!

import gethtml

to load html without cookies
source = gethtml.get(url)

to load html with cookies
source = gethtml.get(url,'my-path-to-cookiefile')

'''

import urllib,urllib2
import cookielib
import os
import re
import xbmc


#!!!!!!!!!!! Please set the compatible_urllist
#set the list of URLs you want to load with cookies.
#matches bits of url, so that if you want to match www243.megaupload.com/ you can just put '.megaupload.com/' in the list. 
compatible_urllist = ['hockeystreams.com']


def url_for_cookies(url):
    #ascertain if the url contains any of the phrases in the list. return True if a match is found.

    url_is_compatible = False
    for compatible_url in compatible_urllist:
        if re.search(compatible_url,url):    
            url_is_compatible = True
            break
    return url_is_compatible        

def get(url,cookiepath=None, cj=None, debug = False):
    if debug: print 'processing url: ' + url + " - cookiepath " + str(cookiepath)
    # use cookies if cookiepath is set and if the cookiepath exists.
    if cookiepath is not None or cj is not None:
        #only use cookies for urls specified
        if url_for_cookies(url):
            if cj is None:
                #check if user has supplied only a folder path, or a full path
                if debug: print "test cookiepath isfile"
                if not os.path.isfile(cookiepath):
                    print "hockeystreams: cookiepath isnt a file " + cookiepath
                    raise IndexError

                #check that the cookie exists
                if debug: print "test cookiepath exists"
                try:
                    if os.path.exists(cookiepath):
                        cj = cookielib.LWPCookieJar()
                        if debug: print "load cookiepath "
                        cj.load(cookiepath)
                    else:
                        print "hockeystreams: cookiepath doesnt exist " + cookiepath
                        raise IndexError
                except:
                    print "hockeystreams: error loading cookiepath" + cookiepath
                    return None

            if debug:
#                print "cookies " + str(cj._cookies)
                print "cookies " + cj._cookies.keys()[0]
                print "hockeystreams getlogin url " + url
            url2 = url.replace("www.hockeystreams.com", cj._cookies.keys()[0])
            if debug: print "hockeystreams getlogin url2 " + url2

            req = urllib2.Request(url2)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
            response = opener.open(req)

            link=response.read()
            response.close()
            return link
        else:
            if debug: print "no url for cookies "  + url
            return _loadwithoutcookies(url)
    else: return _loadwithoutcookies(url)

def _loadwithoutcookies(url):
    print 'processing2 url: '+url
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    link=response.read()
    response.close()
    return link
