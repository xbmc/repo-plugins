# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para Vreel
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os.path
import sys
import xbmc
import os
import config

COOKIEFILE = os.path.join (config.DATA_PATH , "cookies.lwp")

def Vreel(urlvideo):
    # ---------------------------------------
    #  Inicializa la libreria de las cookies
    # ---------------------------------------
    ficherocookies = COOKIEFILE
    try:
        os.remove(ficherocookies)
    except:
        pass
    xbmc.output("ficherocookies %s", ficherocookies)
    # the path and filename to save your cookies in

    cj = None
    ClientCookie = None
    cookielib = None

    # Let's see if cookielib is available
    try:
        import cookielib
    except ImportError:
        # If importing cookielib fails
        # let's try ClientCookie
        try:
            import ClientCookie
        except ImportError:
            # ClientCookie isn't available either
            urlopen = urllib2.urlopen
            Request = urllib2.Request
        else:
            # imported ClientCookie
            urlopen = ClientCookie.urlopen
            Request = ClientCookie.Request
            cj = ClientCookie.LWPCookieJar()

    else:
        # importing cookielib worked
        urlopen = urllib2.urlopen
        Request = urllib2.Request
        cj = cookielib.LWPCookieJar()
        # This is a subclass of FileCookieJar
        # that has useful load and save methods

    # ---------------------------------
    # Instala las cookies
    # ---------------------------------

    if cj is not None:
    # we successfully imported
    # one of the two cookie handling modules

        if os.path.isfile(ficherocookies):
            # if we have a cookie file already saved
            # then load the cookies into the Cookie Jar
            cj.load(ficherocookies)

        # Now we need to get our Cookie Jar
        # installed in the opener;
        # for fetching URLs
        if cookielib is not None:
            # if we use cookielib
            # then we get the HTTPCookieProcessor
            # and install the opener in urllib2
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
            urllib2.install_opener(opener)

        else:
            # if we use ClientCookie
            # then we get the HTTPCookieProcessor
            # and install the opener in ClientCookie
            opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cj))
            ClientCookie.install_opener(opener)

    #print "-------------------------------------------------------"
    url=urlvideo
    #print url
    #print "-------------------------------------------------------"
    theurl = url
    # an example url that sets a cookie,
    # try different urls here and see the cookie collection you can make !

    txdata = None
    # if we were making a POST type request,
    # we could encode a dictionary of values here,
    # using urllib.urlencode(somedict)

    txheaders =  {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3',
                  'Referer':'http://beta.vreel.net/'}
    # fake a user agent, some websites (like google) don't like automated exploration

    req = Request(theurl, txdata, txheaders)
    handle = urlopen(req)
    cj.save(ficherocookies)                     # save the cookies again    

    data=handle.read()
    handle.close()
    #print data

    # Lo pide una segunda vez, como si hubieras hecho click en el banner
    req = Request(theurl, txdata, txheaders)
    handle = urlopen(req)
    cj.save(ficherocookies)                     # save the cookies again    

    data=handle.read()
    handle.close()
    #print data

    patronvideos  = '"(http\://ne.edgecastcdn.net[^"]+)"'

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    return matches[0]

'''
print "-------------------------------------------------------"
print " El video es "
print "http://beta.vreel.net/watch_15051.html"
print " La url del video es "
print Vreel('http://beta.vreel.net/watch_15051.html')
'''

'''
url = "http://ne.edgecastcdn.net/00054B/vreel/15000/15211meteorosubm-xvid.avi?173434eab7e184e3abbf13fd0e1f857c29ef763819ee4ecc7ef54d1b20a030a5dce050326652905ddb01ad83851b962eb3f2a0f90b3516fb/.divx?ec_rate=200"

print url
print "-------------------------------------------------------"
req = urllib2.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
req.add_header('Referer','http://beta.vreel.net/watch_15051.html')
response = urllib2.urlopen(req)
data=response.read()
response.close()
print data

'''
