# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para gigabyteupload
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re

try:
    from core import scrapertools
    from core import logger
    from core import config
    from core import unpackerjs2
except:
    from Code.core import scrapertools
    from Code.core import logger
    from Code.core import config
    from Code.core import unpackerjs2

import os
COOKIEFILE = os.path.join(config.get_data_path() , "cookies.lwp")

def geturl(urlvideo):
    logger.info("[gigabyupload.py] url="+urlvideo)
    # ---------------------------------------
    #  Inicializa la libreria de las cookies
    # ---------------------------------------
    ficherocookies = COOKIEFILE
    try:
        os.remove(ficherocookies)
    except:
        pass
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

    txheaders =  {'User-Agent':'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)'}
    # fake a user agent, some websites (like google) don't like automated exploration
    try:
        req = Request(theurl, txdata, txheaders)
        handle = urlopen(req)
        cj.save(ficherocookies)                     # save the cookies again    

        data=handle.read()
        handle.close()
    except:
        data = ""
        pass
    #print data

    # Lo pide una segunda vez, como si hubieras hecho click en el banner
    patron = 'http\:\/\/www\.gigabyteupload\.com/download\-([^\-]+)\-.*?'
    matches = re.compile(patron,re.DOTALL).findall(url)
    id = matches[0]
    patron  = '<form method="post" action="([^"]+)">[^<]+<input type="hidden" name="security_key" value="([^"]+)" \/>'
    #patron += '<p><input type="submit" name="submit" value="([^"]+)" class="cbutton" \/>'
    
    matches = re.compile(patron,re.DOTALL).findall(data)
    logger.info("[gigabyupload.py] fragmentos de la URL : " + str(len(matches)))
    scrapertools.printMatches(matches)
    
    
    cecid  = ""
    submit = ""
    
    url2      = theurl
    if len(matches)>0:
        url2 = matches[0][0]
        #id = matches[0][5]
        cecid  = matches[0][1]
        submit = "Watch Online"
        #aff = matches[0][3]
        #came_from = matches[0][4]
        
    txdata = "op=download&usr_login=&id="+id+"&security_key="+cecid+"&submit="+submit+"&aff=&came_from=referer=&method_free=Free+Stream"
    logger.info(txdata)
    try:
        req = Request(url2, txdata, txheaders)
        handle = urlopen(req)
        cj.save(ficherocookies)                     # save the cookies again    

        data=handle.read()
        handle.close()
        #print data
    except:
        data = ""
        pass
    
    # Extrae el trozo cifrado
    patron = '<div id="player">[^<]+<script type="text/javascript">(eval.*?)</script>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    data = ""
    if len(matches)>0:
        data = matches[0]
        logger.info("[Gigabyteupload.py] bloque packed="+data)
    else:
        return ""
    
    # Lo descifra
    descifrado = unpackerjs2.unpackjs(data)

    
    # Extrae la URL del vídeo
    logger.info("descifrado="+descifrado)
    # Extrae la URL
    patron = '<param name="src" value="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(descifrado)
    scrapertools.printMatches(matches)
    
    url = ""
    
    if len(matches)>0:
        url = matches[0]

    logger.info("[gigabyteupload.py] url="+url)
    return url
