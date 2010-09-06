# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para yotix
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
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
import downloadtools
import config
import logger

CHANNELNAME = "configuracion"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

logger.info("[configuracion.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[configuracion.py] mainlist")
	
	# Verifica ruta de descargas
	downloadpath = downloadtools.getDownloadPath()
	downloadlistpath = downloadtools.getDownloadListPath()

	config.openSettings( )
