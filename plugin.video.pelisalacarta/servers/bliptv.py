# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para blip.tv
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import re
import urllib

try:
    from core import scrapertools
    from core import logger
except:
    from Code.core import scrapertools
    from Code.core import logger

# Resuelve los videos de blip.tv que se usan en el embed
# 
def geturl(bliptv_url,recurse=True):
    logger.info("[bliptv.py] bliptv_url="+bliptv_url)

    devuelve = ""

    if bliptv_url.startswith("http://blip.tv/play"):    
        redirect = scrapertools.getLocationHeaderFromResponse(bliptv_url)
        logger.info("[bliptv.py] redirect="+redirect)
        
        patron='file\=(.*?)$'
        matches = re.compile(patron).findall(redirect)
        logger.info("[bliptv.py] matches1=%d" % len(matches))
        
        if len(matches)==0:
            patron='file\=([^\&]+)\&'
            matches = re.compile(patron).findall(redirect)
            logger.info("[bliptv.py] matches2=%d" % len(matches))
        
        if len(matches)>0:
            url = matches[0]
            logger.info("[bliptv.py] url="+url)
            url = urllib.unquote(url)
            logger.info("[bliptv.py] url="+url)

            data = scrapertools.cache_page(url)
            logger.info(data)
            patron = '<media\:content url\="([^"]+)" blip\:role="([^"]+)".*?type="([^"]+)"[^>]+>'
            matches = re.compile(patron).findall(data)
            scrapertools.printMatches(matches)

            for match in matches:
                logger.info("url="+str(match[0]))
                devuelve = match[0]

    return devuelve