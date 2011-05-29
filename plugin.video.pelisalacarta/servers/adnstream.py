# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para linkbucks
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import re, sys
import urlparse, urllib, urllib2

try:
    from core import scrapertools
    from core import logger
    from core import config
except:
    from Code.core import scrapertools
    from Code.core import logger
    from Code.core import config

DEBUG = True

# Obtiene la URL que hay detrás de un enlace a linkbucks
def geturl(code):

    mediaurl = "http://www.adnstream.tv/get_playlist.php?lista=video&param="+code+"&c=463"
    # Descarga la página de linkbucks
    data = scrapertools.cachePage(mediaurl)

    # Extrae la URL real
    patronvideos   = '<guid>' +code+ '</guid>.*?'
    patronvideos  += 'video/x-flv" url="(.*?)"'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    
    devuelve = "";
    if len(matches)>0:
        devuelve = matches[0]

    return devuelve
