# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para Veoh
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import os
import urlparse,urllib2,urllib,re

try:
    from core import scrapertools
    from core import logger
    from core import config
except:
    from Code.core import scrapertools
    from Code.core import logger
    from Code.core import config

COOKIEFILE = os.path.join(config.get_data_path() , "cookies.lwp")

def geturl(code):
    logger.info("[veoh.py] code="+code)
    url = 'http://www.flashvideodownloader.org/download.php?u=http://www.veoh.com/browse/videos/category/entertainment/watch/'+code
    logger.info("[veoh.py] url="+url)
    data = scrapertools.cachePage(url)
    #logger.info("[veoh.py] data="+data)
    patronvideos  = '<a href="(http://content.veoh.com.*?)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    movielink=""
    if len(matches)>0:
        movielink = matches[0]
    logger.info("[veoh.py] movielink="+movielink)
    
    import httplib
    parsedurl = urlparse.urlparse(movielink)
    #logger.info("[veoh.py] parsedurl="+parsedurl)
    print "parsedurl=",parsedurl

    try:
        logger.info("[veoh.py] 1")
        host = parsedurl.netloc
    except:
        logger.info("[veoh.py] 2")
        host = parsedurl[1]
    logger.info("[veoh.py] host="+host)

    try:
        logger.info("[veoh.py] 1")
        query = parsedurl.path+parsedurl.query
    except:
        logger.info("[veoh.py] 2")
        query = parsedurl[2]+parsedurl[3]
    logger.info("[veoh.py] query = " + query)
    query = urllib.unquote( query )
    logger.info("[veoh.py] query = " + query)

    try:
        logger.info("[veoh.py] 1")
        params = parsedurl.params
    except:
        logger.info("[veoh.py] 2")
        params = parsedurl[4]
    logger.info("[veoh.py] params = " + params)

    import httplib
    conn = httplib.HTTPConnection(host)
    conn.request("GET", query+"?"+params)
    response = conn.getresponse()
    location = response.getheader("location")
    conn.close()

    if location!=None:
        logger.info("[veoh.py] Encontrado header location")
        logger.info("[veoh.py] location="+location)
    else:
        location=""
    
    return location
