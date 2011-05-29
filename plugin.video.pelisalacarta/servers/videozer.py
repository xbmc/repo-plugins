# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para videozer.com
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

_VALID_URL = r'^((?:http://)?(?:\w+\.)?videozer\.com/(?:(?:e/|video/)|(?:(?:flash/|f/)))?)?([0-9A-Za-z_-]+)(?(1).+)?$'


def geturl(url):

    logger.info("[videozer.py] url="+url)
    # El formato de la URL de la página es
    # http://videozer.com/video/Tnfs1OI
    # El formato de la URL del vídeo es
    # http://video33.videozer.com:80/video?v=Tnfs1OI&t=1303649554&u=&c=c6bffc4fa689297273cf2a04658ca435&r=1
    code = Extract_id(url)

    
    controluri = "http://videozer.com/player_control/settings.php?v=%s&fv=v1.1.03"  %code
    datajson = scrapertools.cachePage(controluri)
    print datajson
    datajson = datajson.replace("false","False").replace("true","True")
    datajson = datajson.replace("null","None")
    datadict = eval("("+datajson+")")
    formatos = datadict["cfg"]["quality"]
    longitud = len(formatos)
    uri = formatos[longitud-1]["u"]
    logger.info("Resolucion del video ="+formatos[longitud-1]["l"])
    import base64
    
    devuelve = base64.decodestring(uri)

    logger.info("[videozer.py] url="+devuelve)
    
    return devuelve

def Extract_id(url):
    # Extract video id from URL
    mobj = re.match(_VALID_URL, url)
    if mobj is None:
        print 'ERROR: URL invalida: %s' % url
        
        return ""
    id = mobj.group(2)
    return id
