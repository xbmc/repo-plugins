# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal EURONEWS en YouTube
# http://blog.tvalacarta.info/plugin-xbmc/tvalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import scrapertools
import binascii
import xbmctools
import youtube

try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

xbmc.output("[euronews.py] init")

DEBUG = True
CHANNELNAME = "Euronews"
CHANNELCODE = "euronews"

def mainlist(params,url,category):
	xbmc.output("[euronews.py] channel")

	# Anade al listado de XBMC
	addnewfolder( CHANNELCODE , "channel" , CHANNELNAME , "Euronews ES" , "euronewses" , "" , "" , 1 , 13 )
	addnewfolder( CHANNELCODE , "channel" , CHANNELNAME , "Euronews EN" , "euronews" , "" , "" , 1 , 13 )
	addnewfolder( CHANNELCODE , "channel" , CHANNELNAME , "Euronews FR" , "euronewsfr" , "" , "" , 1 , 13 )
	addnewfolder( CHANNELCODE , "channel" , CHANNELNAME , "Euronews DE" , "euronewsde" , "" , "" , 1 , 13 )
	addnewfolder( CHANNELCODE , "channel" , CHANNELNAME , "Euronews IT" , "euronewsit" , "" , "" , 1 , 13 )
	addnewfolder( CHANNELCODE , "channel" , CHANNELNAME , "Euronews PT" , "euronewspt" , "" , "" , 1 , 13 )
	addnewfolder( CHANNELCODE , "channel" , CHANNELNAME , "Euronews RU" , "euronewsru" , "" , "" , 1 , 13 )
	addnewfolder( CHANNELCODE , "channel" , CHANNELNAME , "Euronews AR" , "euronewsar" , "" , "" , 1 , 13 )
	addnewfolder( CHANNELCODE , "channel" , CHANNELNAME , "No Comment" , "nocommenttv" , "" , "" , 1 , 13 )
	addnewfolder( CHANNELCODE , "channel" , CHANNELNAME , "Questions for Europe EN" , "questionsforeurope" , "" , "" , 1 , 13 )
	addnewfolder( CHANNELCODE , "channel" , CHANNELNAME , "Questions for Europe FR" , "questionsforeuropefr" , "" , "" , 1 , 13 )
	addnewfolder( CHANNELCODE , "channel" , CHANNELNAME , "Questions for Europe DE" , "questionsforeuropede" , "" , "" , 1 , 13 )

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def channel(params,url,category):
	xbmc.output("[euronews.py] channel")

	# Parametros
	channelname = url
	startindex = int(params.get("startindex"))
	maxresults = int(params.get("maxresults"))

	# Anade al listado de XBMC
	if startindex==1: 
		addnewfolder( CHANNELCODE , "novedades" , CHANNELNAME , "Novedades" , channelname , "" , "" , 1 , 13 )

	itemlist = youtube.getplaylists(channelname,startindex,maxresults)
	for item in itemlist:
		print item.title
		print item.url
		print item.thumbnail
		print item.plot
		addnewfolder( CHANNELCODE , "playlist" , CHANNELNAME , item.title , item.url , item.thumbnail , item.plot , startindex, maxresults )

	if len(itemlist)>=13:
		addnewfolder( CHANNELCODE , "channel" , CHANNELNAME , "!Siguiente pagina" , channelname , "" , "" , startindex+maxresults, maxresults )		

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def novedades(params,url,category):
	xbmc.output("[euronews.py] novedades")

	# Parametros
	channelname = url
	startindex = int(params.get("startindex"))
	maxresults = int(params.get("maxresults"))

	# Videos
	itemlist = youtube.getuploads(channelname,startindex,maxresults)
	for item in itemlist:
		xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , item.title , item.url , item.thumbnail , item.plot )

	# Paginacion
	if len(itemlist)>=13:
		addnewfolder( CHANNELCODE , "novedades" , CHANNELNAME , "!Siguiente pagina" , channelname , "" , "" , startindex+maxresults, maxresults )		

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def playlist(params,url,category):
	xbmc.output("[euronews.py] playlist")

	# Parametros
	startindex = int(params.get("startindex"))
	maxresults = int(params.get("maxresults"))

	# Videos
	itemlist = youtube.getplaylistvideos(url,startindex,maxresults)
	for item in itemlist:
		xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , item.title , item.url , item.thumbnail , item.plot )

	# Paginacion
	if len(itemlist)>=13:
		addnewfolder( CHANNELCODE , "playlist" , CHANNELNAME , "!Siguiente pagina" , url , "" , "" , startindex+maxresults, maxresults )		

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	xbmc.output("[euronews.py] play")

	# Extrae el ID
	id = youtube.Extract_id(url)
	xbmc.output("[euronews.py] id="+id)
	
	# Descarga la página
	data = scrapertools.cachePage(url)
	
	# Obtiene la URL
	url = youtube.geturls(id,data)
	print url
	
	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = "Directo"

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

def addnewfolder( canal , accion , category , title , url , thumbnail , plot , startindex, maxresults ):
	#xbmc.output("pluginhandle=%d" % pluginhandle)
	try:
		xbmc.output('[xbmctools.py] addnewfolder( "'+canal+'" , "'+accion+'" , "'+category+'" , "'+title+'" , "' + url + '" , "'+thumbnail+'" , "'+plot+'")"')
	except:
		xbmc.output('[xbmctools.py] addnewfolder(<unicode>)')
	listitem = xbmcgui.ListItem( title, iconImage="DefaultFolder.png", thumbnailImage=thumbnail )
	listitem.setInfo( "video", { "Title" : title, "Plot" : plot, "Studio" : canal } )
	itemurl = '%s?channel=%s&action=%s&category=%s&title=%s&url=%s&thumbnail=%s&plot=%s&startindex=%d&maxresults=%d' % ( sys.argv[ 0 ] , canal , accion , urllib.quote_plus( category ) , urllib.quote_plus( title ) , urllib.quote_plus( url ) , urllib.quote_plus( thumbnail ) , urllib.quote_plus( plot ) , startindex , maxresults )
	xbmc.output("[xbmctools.py] itemurl=%s" % itemurl)
	xbmcplugin.addDirectoryItem( handle = pluginhandle, url = itemurl , listitem=listitem, isFolder=True)
