# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para Movshare
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re

try:
    from core import scrapertools
    from core import logger
    from core import config
except:
    from Code.core import scrapertools
    from Code.core import logger
    from Code.core import config

import os
COOKIEFILE = os.path.join(config.get_data_path() , "cookies.lwp")

def geturl(urlpagina):
    # ---------------------------------------
    #  Inicializa la libreria de las cookies
    # ---------------------------------------
    ficherocookies = COOKIEFILE
    try:
        os.remove(ficherocookies)
    except:
        pass
    logger.info("ficherocookies %s" % ficherocookies)
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
    url=urlpagina
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
                  'Referer':'http://www.movshare.net/'}
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

    patronvideos  = '<embed type="video/divx" src="([^"]+)"'

    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)== 0:
        patronvideos  = '"file","([^"]+)"'
        matches = re.compile(patronvideos,re.DOTALL).findall(data)
        if     len(matches)== 0:
            patronvideos  = '<embed src="([^"]+)"'
            matches = re.compile(patronvideos,re.DOTALL).findall(data)
            if len(matches)== 0:
                return ""
            
    return matches[0]
