# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Lista de vídeos descargados
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

CHANNELNAME = "descargados"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[descargados.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[descargados.py] mainlist")

	# Verifica ruta de descargas
	downloadpath = downloadtools.getDownloadPath()

	xbmctools.addnewfolder( "descargadoslist" , "mainlist"  , category , "Descargas pendientes","","","")
	xbmctools.addnewfolder( "descargadoslist" , "errorlist"  , category , "Descargas con error","","","")

	# Añade al listado de XBMC
	try:
		ficheros = os.listdir(downloadpath)
		for fichero in ficheros:
			if fichero!="lista" and fichero!="error" and not fichero.endswith(".nfo") and not fichero.endswith(".tbn"):
				url = os.path.join( downloadpath , fichero )
				listitem = xbmcgui.ListItem( fichero, iconImage="DefaultVideo.png" )
				xbmcplugin.addDirectoryItem( handle = pluginhandle, url = url, listitem=listitem, isFolder=False)
	except:
		pass
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
