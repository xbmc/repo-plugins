# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para nomegavideo
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
# El logo del canal es una foto de flickr
# http://www.flickr.com/photos/stevendepolo/3015116374/ para el poster
# http://www.flickr.com/photos/arcticpuppy/3324587240/ para el banner
# Con licencia CC
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import scrapertools
import megavideo
import servertools
import binascii
import xbmctools
import config
import logger

CHANNELNAME = "nomegavideo"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[nomegavideo.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[nomegavideo.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( "capitancinema" , "novedades"  , category , "Películas - Novedades [ES] [Capitan Cinema]"     ,"http://www.capitancinema.com/peliculas-online-novedades.htm","","")
	xbmctools.addnewfolder( "peliculasid"   , "listvideos" , category , "Ultimas Películas Subidas [VOS] [Peliculasid]"   ,"http://www.peliculasid.com/","","")
	xbmctools.addnewfolder( "cinegratis24h" , "listvideos" , category , "Ultimas Películas Subidas [VOS] [Cinegratis24h]" ,"http://www.cinegratis24h.com/","","")
	xbmctools.addnewfolder( "delatv"        , "novedades"  , category , "Novedades [ES] [DelaTV]"                         ,"http://delatv.com/","","")
	xbmctools.addnewfolder( "cinegratis"    , "listvideos" , category , "Películas - Alojadas en Veoh [ES] [Cinegratis]"  ,"http://www.cinegratis.net/index.php?module=servers&varserver=veoh","","")
	xbmctools.addnewfolder( "cine15"        , "listvideos" , category , "Películas - Novedades [ES] [Cine15]"             ,"http://www.cine15.com/","","")

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
