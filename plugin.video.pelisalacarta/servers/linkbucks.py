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
def geturl(url):

    # Descarga la página de linkbucks
    data = scrapertools.cachePage(url)

    # Extrae la URL real
    patronvideos  = "linkDestUrl \= '([^']+)'"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    
    devuelve = "";
    if len(matches)>0:
        devuelve = matches[0]

    return devuelve
