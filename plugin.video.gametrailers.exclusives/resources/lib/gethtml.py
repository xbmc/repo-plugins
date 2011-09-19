"""

Module:   gethtml.py
Author:   Anarchintosh @ xbmcforums
          AssChin79 @ xbmcforums (minor format tweaks)
License:  Copyleft (GNU GPL v3) 2011 onwards
Date:     9/13/2011
Summary:  This class is intended to simplify the process of scraping web pages, while logged in. 
          This version is configured for scraping gametrailers.com to retrieve direct video links.
        
          For the full guide please visit: http://forum.xbmc.org/showthread.php?p=772597#post772597
USAGE:
 In your addon default.py put:

 import gethtml

 # Load html without cookies
 source = gethtml.get(url)

 # Load html with cookies
 source = gethtml.get(url,'my-path-to-cookiefile')

"""

import urllib,urllib2
import cookielib
import os
import re

#<summary>
# The list of compatible domains.
#</summary> 
compatible_urllist = ['.gametrailers.com/','http://174.76.224.25/']

#<summary>
# Identify if the url is in the allow list.
#</summary>
#<param name="url">The target address</param>
def url_for_cookies(url):
    
    # ascertain if the url contains any of the phrases in the list. 
    # return True if a match is found.
    for compatible_url in compatible_urllist:
        
        if re.search(compatible_url,url):    
            url_is_compatible = True
            break

        else: url_is_compatible = False
        
    return url_is_compatible        

#<summary>
# Gets the HTML response 
#</summary>
#<param name="url">The url to get</param>
#<param name="cookiePath">The local path to the authentication cookie</param>
def get(url,cookiepath=None):
                 
    # use cookies if cookiepath is set and if the cookiepath exists.
    if cookiepath is not None:

        # only use cookies for urls specified
        if url_for_cookies(url) == True:

                # check if user has supplied only a folder path, or a full path
                if not os.path.isfile(cookiepath):
                    #if the user supplied only a folder path, append on to the end of the path a common filename.
                    cookiepath = os.path.join(cookiepath,'cookies.lwp')

                # check that the cookie exists
                if os.path.exists(cookiepath):
                 
                    cj = cookielib.LWPCookieJar()
                    cj.load(cookiepath)
                    req = urllib2.Request(url)
                    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')   
                    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
                    response = opener.open(req)
                    link=response.read()
                    response.close()
                    return link
               
                else: return _loadwithoutcookies(url)                
        else: return _loadwithoutcookies(url)    
    else: return _loadwithoutcookies(url)

#<summary>
# Gets the HTML response (no cookie)
#</summary>
#<param name="url">The url to get</param>
def _loadwithoutcookies(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')   
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link  
