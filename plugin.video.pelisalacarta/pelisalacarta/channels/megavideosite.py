# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para ver una peli en Megavideo conociendo el codigo
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin

from core import scrapertools
from core import config
from core import logger
from core import xbmctools
from core.item import Item
from servers import servertools

from pelisalacarta import buscador

CHANNELNAME = "megavideosite"

# Esto permite su ejecución en modo emulado
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

logger.info("[megavideosite.py] init")

DEBUG = True

def mainlist(params,url,category):
    logger.info("[megavideosite.py] mainlist")

    # Añade al listado de XBMC
    xbmctools.addnewfolder( CHANNELNAME , "search" , CHANNELNAME , "Introduce el código del vídeo" , "" , "", "" )

    # Cierra el directorio
    xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def search(params,url,category):
    logger.info("[megavideosite.py] list")

    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        tecleado = keyboard.getText()
        if len(tecleado)>0:
            #convert to HTML
            tecleado = tecleado.replace(" ", "+")
            list(params,tecleado,category)

def list(params,url,category):
    logger.info("[megavideosite.py] list")

    xbmctools.addnewvideo( CHANNELNAME , "play" , category , "Megavideo" , "Ver el vídeo [Megavídeo]" , url , "" , "" )

    # Asigna el título, desactiva la ordenación, y cierra el directorio
    xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
    xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
    logger.info("[megavideosite.py] list")

    title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
    thumbnail = urllib.unquote_plus( params.get("thumbnail") )
    plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    server = params["server"]
    
    xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
