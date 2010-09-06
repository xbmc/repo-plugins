# -*- coding: iso-8859-1 -*-

import urllib
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import parametrizacion
import logger
import config

logger.info("[channelselector.py] init")

DEBUG = True
IMAGES_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources' , 'images' ) )

#57=DVD Thumbs
#xbmc.executebuiltin("Container.SetViewMode(57)")
#50=full list
#xbmc.executebuiltin("Container.SetViewMode(50)")
#51=list
#xbmc.executebuiltin("Container.SetViewMode(51)")
#53=icons
#xbmc.executebuiltin("Container.SetViewMode(53)")
#54=wide icons
#xbmc.executebuiltin("Container.SetViewMode(54)")

def listchannels(params,url,category):
	logger.info("[channelselector.py] listchannels")

	# Verifica actualizaciones solo en el primer nivel
	try:
		import updater
	except ImportError:
		logger.info("[channelselector.py] No disponible modulo actualizaciones")
	else:
		if config.getSetting("updatecheck2") == "true":
			logger.info("[channelselector.py] Verificar actualizaciones activado")
			updater.checkforupdates()
		else:
			logger.info("[channelselector.py] Verificar actualizaciones desactivado")

	addfolder("Antena3","a3","mainlist")
	addfolder("ADNStream","adnstream","mainlist")
	addfolder("Barcelona TV","barcelonatv","mainlist")
	addfolder("Clan TV","clantv","mainlist")
	addfolder("El cine de las 3 mellizas","tresmellizas","mainlist")
	addfolder("Boing","boing","mainlist")
	#addfolder("Totlol","totlol","mainlist")
	addfolder("EITB","eitb","mainlist")
	addfolder("Extremadura TV","extremaduratv","mainlist")
	addfolder("Hogarutil","hogarutil","mainlist")
	addfolder("Plus TV","plus","mainlist")
	addfolder("Andalucia TV","rtva","mainlist")
	addfolder("TVE","rtve","mainlist")
	addfolder("TVE Programas","rtveprogramas","mainlist")
	addfolder("TVE Mediateca","rtvemediateca","mainlist")
	#addfolder("TV Azteca","tva","mainlist")
	addfolder("Berria TB","berriatb","mainlist")
	addfolder("Earth TV","earthtv","mainlist")
	addfolder("Euronews","euronews","mainlist")
	addfolder("Comunidad Valenciana","rtvv","mainlist")
	#addfolder("Terra TV","terratv","mainlist")
	addfolder("Turbonick","turbonick","mainlist")
	addfolder("TV3","tv3","mainlist")
	addfolder("TVG","tvg","mainlist")
	addfolder("Mallorca TV","tvmallorca","mainlist")
	addfolder("Meristation","meristation","mainlist")
	addfolder("7rm","sieterm","mainlist")
	addfolder("Televisión Canaria","rtvc","mainlist")
	addfolder("Internautas TV","internautastv","mainlist")
	addfolder("Publico.tv","publicotv","mainlist")
	
	cadena = config.getLocalizedString(30100)
	logger.info("cadena="+cadena)
	addfolder(cadena,"configuracion","mainlist") # Configuracion
	if (parametrizacion.DOWNLOAD_ENABLED):
		addfolder(config.getLocalizedString(30101),"descargados","mainlist")   # Descargas
	addfolder(config.getLocalizedString(30102),"favoritos","mainlist")     # Favoritos

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category="Canales" )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def addfolder(nombre,channelname,accion):
	listitem = xbmcgui.ListItem( nombre , iconImage="DefaultFolder.png", thumbnailImage=os.path.join(IMAGES_PATH, channelname+".png"))
	itemurl = '%s?channel=%s&action=%s&category=%s' % ( sys.argv[ 0 ] , channelname , accion , urllib.quote_plus(nombre) )
	xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)
