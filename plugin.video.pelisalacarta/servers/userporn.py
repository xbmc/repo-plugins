# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para userporn
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import os,re

try:
    from core import scrapertools
    from core import logger
    from core import config
except:
    from Code.core import scrapertools
    from Code.core import logger
    from Code.core import config

_VALID_URL = r'^((?:http://)?(?:\w+\.)?userporn\.com/(?:(?:(?:e/)|(?:video/))|(?:(?:flash/)|(?:f/)))?)?([0-9A-Za-z_-]+)(?(1).+)?$'


def geturl(url):

    logger.info("[userporn.py] code="+url)

    code = Extract_id(url)
    controluri = "http://userporn.com/player_control/settings.php?v=" + code
    datajson = scrapertools.cachePage(controluri)
    #print datajson
    datajson = datajson.replace("false","False").replace("true","True")
    datajson = datajson.replace("null","None")
    datadict = eval("("+datajson+")")
    formatos = datadict["settings"]["res"]
    longitud = len(formatos)
    uri = formatos[longitud-1]["u"]
    logger.info("Resolucion del video ="+formatos[longitud-1]["l"])
    import base64
    
    devuelve = base64.decodestring(uri)


    logger.info("[userporn.py] code="+devuelve)
    
    return devuelve

def Extract_id(url):
    # Extract video id from URL
    mobj = re.match(_VALID_URL, url)
    if mobj is None:
        print 'ERROR: URL invalida: %s' % url
        
        return ""
    id = mobj.group(2)
    logger.info("[userporn.py] extracted code="+id)
    return id
