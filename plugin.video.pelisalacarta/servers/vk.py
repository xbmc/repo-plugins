# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para VK Server
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os

try:
    from core import scrapertools
    from core import logger
    from core import config
    from core import unpackerjs
except:
    from Code.core import scrapertools
    from Code.core import logger
    from Code.core import config
    from Code.core import unpackerjs

COOKIEFILE = os.path.join(config.get_data_path() , "cookies.lwp")

def geturl(urlvideo):
    logger.info("[vk.py] url="+urlvideo)
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
    url=urlvideo.replace("amp;","")
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

    req = Request(theurl, txdata, txheaders)
    handle = urlopen(req)
    cj.save(ficherocookies)                     # save the cookies again    

    data=handle.read()
    handle.close()
    #print data
    
    # Extrae la URL

    #print data
    videourl = ""
    quality = config.get_setting("quality_flv")
    regexp =re.compile(r'vkid=([^\&]+)\&')
    match = regexp.search(data)
    vkid = ""
    print 'match %s'%str(match)
    if match is not None:
        vkid = match.group(1)
    else:
        print "no encontro vkid"
        
    patron  = "var video_host = '([^']+)'.*?"
    patron += "var video_uid = '([^']+)'.*?"
    patron += "var video_vtag = '([^']+)'.*?"
    patron += "var video_no_flv = ([^;]+);.*?"
    patron += "var video_max_hd = '([^']+)'"
    matches = re.compile(patron,re.DOTALL).findall(data)
    if len(matches)>0:    
        for match in matches:
            if match[3].strip() == "0" and match[1] != "0":
                tipo = "flv"
                if "http://" in match[0]:
                    videourl = "%s/u%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
                else:
                    videourl = "http://%s/u%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
                
            elif match[1]== "0" and vkid != "":     #http://447.gt3.vkadre.ru/assets/videos/2638f17ddd39-75081019.vk.flv 
                tipo = "flv"
                if "http://" in match[0]:
                    videourl = "%s/assets/videos/%s%s.vk.%s" % (match[0],match[2],vkid,tipo)
                else:
                    videourl = "http://%s/assets/videos/%s%s.vk.%s" % (match[0],match[2],vkid,tipo)
                
            else:                                   #http://cs12385.vkontakte.ru/u88260894/video/d09802a95b.360.mp4
                #Si la calidad elegida en el setting es HD se reproducira a 480 o 720, caso contrario solo 360, este control es por la xbox
                if   match[4]=="0":
                    tipo = "240.mp4"
                elif match[4]=="1":
                    tipo = "360.mp4"
                elif match[4]== "2" and quality == "1":
                    tipo = "480.mp4"
                elif match[4]=="3" and quality == "1":
                    tipo = "720.mp4"
                else:
                    tipo = "360.mp4"
                if match[0].endswith("/"):
                    videourl = "%su%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
                else:
                    videourl = "%s/u%s/video/%s.%s" % (match[0],match[1],match[2],tipo)
                
                
    return videourl

