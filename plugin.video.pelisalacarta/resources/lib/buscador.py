# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cinegratis
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

import cinegratis
import peliculasyonkis
import cine15
import seriesyonkis
import yotix
import peliculas21
import sesionvip
import documaniatv
import discoverymx
import stagevusite
import tutvsite
import tumejortv
import config
import cinetube
import logger
from item import Item

CHANNELNAME = "buscador"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

logger.info("[buscador.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[buscador.py] mainlist")

	listar_busquedas(params,url,category)

def searchresults(params,url,category):
	salvar_busquedas(params,url,category)
	tecleado = url
	tecleado = tecleado.replace(" ", "+")
	
	# Lanza las búsquedas
	
	# Cinegratis
	matches = []
	itemlist = []
	try:
		itemlist.extend( cinetube.getsearchresults(params,tecleado,category) )
	except:
		pass
	try:
		matches.extend( cinegratis.performsearch(tecleado) )
	except:
		pass
	try:
		matches.extend( peliculasyonkis.performsearch(tecleado) )
	except:
		pass
	try:
		matches.extend( tumejortv.performsearch(tecleado) )
	except:
		pass
	try:
		matches.extend( cine15.performsearch(tecleado) )
	except:
		pass
	try:
		matches.extend( peliculas21.performsearch(tecleado) )
	except:
		pass
	#matches.extend( sesionvip.performsearch(tecleado) )
	try:
		matches.extend( seriesyonkis.performsearch(tecleado) )
	except:
		pass
	try:
		matches.extend( documaniatv.performsearch(tecleado) )
	except:
		pass
	try:
		matches.extend( discoverymx.performsearch(tecleado) )
	except:
		pass
	try:
		matches.extend( yotix.performsearch(tecleado) )
	except:
		pass
	try:
		matches.extend( stagevusite.performsearch(tecleado) )
	except:
		pass
	try:
		matches.extend( tutvsite.performsearch(tecleado) )
	except:
		pass
	
	for item in itemlist:
		targetchannel = item.channel
		action = item.action
		category = category
		scrapedtitle = item.title+" ["+item.channel+"]"
		scrapedurl = item.url
		scrapedthumbnail = item.thumbnail
		scrapedplot = item.plot
		
		xbmctools.addnewfolder( targetchannel , action , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )
	
	# Construye los resultados
	for match in matches:
		targetchannel = match[0]
		action = match[1]
		category = match[2]
		scrapedtitle = match[3]+" ["+targetchannel+"]"
		scrapedurl = match[4]
		scrapedthumbnail = match[5]
		scrapedplot = match[6]
		
		xbmctools.addnewfolder( targetchannel , action , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_TITLE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )


def salvar_busquedas(params,url,category):
	channel = params.get("channel")
	limite_busquedas = ( 10, 20, 30, 40, )[ int( config.getSetting( "limite_busquedas" ) ) ]
	matches = []
	try:
		presets = config.getSetting("presets_buscados")
		if "|" in presets:
			presets = matches = presets.split("|")			
			for count, preset in enumerate( presets ):
				if url in preset:
					del presets[ count ]
					break
		
		if len( presets ) >= limite_busquedas:
			presets = presets[ : limite_busquedas - 1 ]
	except:
		presets = ""
	presets2 = ""
	if len(matches)>0:
		for preset in presets:
			presets2 = presets2 + "|" + preset 
		presets = url + presets2
	elif presets != "":
		presets = url + "|" + presets
	else:
		presets = url
	config.setSetting("presets_buscados",presets)
    # refresh container so items is changed
	xbmc.executebuiltin( "Container.Refresh" )
		
def listar_busquedas(params,url,category):
	print "listar_busquedas()"
	channel2 = ""
	# Despliega las busquedas anteriormente guardadas
	try:
		presets = config.getSetting("presets_buscados")
		channel_preset  = params.get("channel")
		if channel_preset != CHANNELNAME:
			channel2 = channel_preset
		print "channel_preset :%s" %channel_preset
		accion = params.get("action")
		matches = ""
		if "|" in presets:
			matches = presets.split("|")
			addfolder( "buscador"   , "Buscar..." , matches[0] , "por_teclado", channel2 )
		else:
			addfolder( "buscador"   , "Buscar..." , "" , "por_teclado", channel2 )
		if len(matches)>0:	
			for match in matches:
				
				title=scrapedurl = match
		
				addfolder( channel_preset , title , scrapedurl , "searchresults" )
		elif presets != "":
		
			title = scrapedurl = presets
			addfolder( channel_preset , title , scrapedurl , "searchresults" )
	except:
		addfolder( "buscador"   , "Buscar..." , "" , "por_teclado" , channel2 )
		
	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
	
def borrar_busqueda(params,url,category):
	channel = params.get("channel")
	matches = []
	try:
		presets = config.getSetting("presets_buscados")
		if "|" in presets:
			presets = matches = presets.split("|")
			for count, preset in enumerate( presets ):
				if url in preset:
					del presets[ count ]
					break
		elif presets == url:
			presets = ""
			
	except:
		presets = ""
	if len(matches)>1:
		presets2 = ""
		c = 0
		barra = ""
		for preset in presets:
			if c>0:
				barra = "|"
			presets2 =  presets2 + barra + preset 
			c +=1
		presets = presets2
	elif len(matches) == 1:
		presets = presets[0]
	config.setSetting("presets_buscados",presets)
    # refresh container so item is removed
	xbmc.executebuiltin( "Container.Refresh" )


def teclado(default="", heading="", hidden=False):
	tecleado = ""
	keyboard = xbmc.Keyboard(default)
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)<=0:
			return
	
	return tecleado
	
def por_teclado(params,url,category):
	channel2 = params.get("channel2")
	tecleado = teclado(url)
	if len(tecleado)<=0:
		return
	#borrar_busqueda(params,tecleado,category)
	#salvar_busquedas(params,tecleado,category)
	#tecleado = tecleado.replace(" ", "+")
	url = tecleado
	if channel2 == "":
		exec "import "+params.get("channel")+" as plugin"
	else:
		exec "import "+channel2+" as plugin"
	exec "plugin.searchresults(params, url, category)"

def addfolder( canal , nombre , url , accion , channel2 = "" ):
	logger.info('[buscador.py] addfolder( "'+nombre+'" , "' + url + '" , "'+accion+'")"')
	listitem = xbmcgui.ListItem( nombre , iconImage="DefaultFolder.png")
	itemurl = '%s?channel=%s&action=%s&category=%s&url=%s&channel2=%s' % ( sys.argv[ 0 ] , canal , accion , urllib.quote_plus(nombre) , urllib.quote_plus(url),channel2 )
	
	
	if accion != "por_teclado":
		contextCommands = []
		DeleteCommand = "XBMC.RunPlugin(%s?channel=buscador&action=borrar_busqueda&title=%s&url=%s)" % ( sys.argv[ 0 ]  ,  urllib.quote_plus( nombre ) , urllib.quote_plus( url ) )
		contextCommands.append((config.getLocalizedString( 30300 ),DeleteCommand))
		listitem.addContextMenuItems ( contextCommands, replaceItems=False)
		
	xbmcplugin.addDirectoryItem( handle = pluginhandle, url = itemurl , listitem=listitem, isFolder=True)
	
	
