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

CHANNELNAME = "cineblog01"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
xbmc.output("[cineblog01.py] init")

DEBUG = True

import re, htmlentitydefs

##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
	def fixup(m):
		text = m.group(0)
		if text[:2] == "&#":
			# character reference
			try:
				if text[:3] == "&#x":
					return unichr(int(text[3:-1], 16))
				else:
					return unichr(int(text[2:-1]))
			except ValueError:
				pass
		else:
			# named entity
			try:
				text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
			except KeyError:
				pass
		return text # leave as is
	return re.sub("&#?\w+;", fixup, text)

def mainlist(params,url,category):
	xbmc.output("[cineblog01.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "listvideos"  , category , "Film - Novità"              ,"http://cineblog01.com/film/","","")
	xbmctools.addnewfolder( CHANNELNAME , "pelisalfa"   , category , "Film - Per Lettera"    ,"","","")
	xbmctools.addnewfolder( CHANNELNAME , "searchmovie" , category , "   Cerca Film"                           ,"","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos"  , category , "Serie"   ,"http://cineblog01.com/serietv/","","")
	xbmctools.addnewfolder( CHANNELNAME , "listvideos"  , category , "Anime"   ,"http://cineblog01.com/anime/","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def pelisalfa(params, url, category):

	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "0-9","http://cineblog01.com/film/category/numero","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "A","http://cineblog01.com/film/category/a","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "B","http://cineblog01.com/film/category/b","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "C","http://cineblog01.com/film/category/c","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "D","http://cineblog01.com/film/category/d","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "E","http://cineblog01.com/film/category/e","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "F","http://cineblog01.com/film/category/f","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "G","http://cineblog01.com/film/category/g","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "H","http://cineblog01.com/film/category/h","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "I","http://cineblog01.com/film/category/i","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "J","http://cineblog01.com/film/category/j","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "K","http://cineblog01.com/film/category/k","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "L","http://cineblog01.com/film/category/l","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "M","http://cineblog01.com/film/category/m","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "N","http://cineblog01.com/film/category/n","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "O","http://cineblog01.com/film/category/o","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "P","http://cineblog01.com/film/category/p","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Q","http://cineblog01.com/film/category/q","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "R","http://cineblog01.com/film/category/r","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "S","http://cineblog01.com/film/category/s","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "T","http://cineblog01.com/film/category/t","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "U","http://cineblog01.com/film/category/u","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "V","http://cineblog01.com/film/category/v","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "W","http://cineblog01.com/film/category/w","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "X","http://cineblog01.com/film/category/x","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Y","http://cineblog01.com/film/category/y","","")
	xbmctools.addnewfolder( CHANNELNAME ,"listcat", category , "Z","http://cineblog01.com/film/category/z","","")

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

	########################################

def searchmovie(params,url,category):
	xbmc.output("[cineblog01.py] searchmovie")

	keyboard = xbmc.Keyboard('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = "http://cineblog01.com/film/?s="+tecleado
			listvideos(params,searchUrl,category)

def performsearch(texto):
	xbmc.output("[cineblog01.py] performsearch")
	url = "http://cineblog01.com/film/?s="+texto

	# Descarga la página
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<div id="covershot".*?<a.*?<img src="(.*?)".*?'
	patronvideos += '<div id="post-title"><a href="(.*?)".*?'
	patronvideos += '<h3>(.*?)</h3>.*?&#160;'
	patronvideos += '&#160;(.*?)</p>'
	#patronvideos += '<div id="description"><p>(.?*)</div>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		UnicodeDecodedTitle = match[2].decode("utf-8")
		unescapedTitle = unescape (UnicodeDecodedTitle)
		scrapedtitle = unescapedTitle.encode("latin1","ignore") 
		# URL
		scrapedurl = urlparse.urljoin(url,match[1])
		# Thumbnail
		scrapedthumbnail = urlparse.urljoin(url,match[0])
		# Argumento
		UnicodeDecodedTitle = match[3].decode("utf-8")
		unescapedTitle = unescape (UnicodeDecodedTitle)
		scrapedplot = unescapedTitle.encode("latin1","ignore") 
		#scrapedplot = match[3]
		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)
#			xbmc.output("scrapeddescription="+scrapeddescription)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Remove the next page mark
	patronvideos = '<a href="(http://cineblog01.com/film/page/[0-9]+)">Avanti >'
	matches = re.compile (patronvideos, re.DOTALL). findall (data)
	scrapertools.printMatches (matches)

	if len(matches)>0:
		scrapedtitle = "Pagina seguente"
		scrapedurl = matches[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )
	
	return resultados

def listcat(params,url,category):
	xbmc.output("[cineblog01.py] mainlist")
	if url =="":
		url = "http://cineblog01.com/film/"
		
	# Descarga la página
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<div id="covershot".*?<a.*?<img src="(.*?)".*?'
	patronvideos += '<div id="post-title"><a href="(.*?)".*?'
	patronvideos += '<h3>(.*?)</h3>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		UnicodeDecodedTitle = match[2].decode("utf-8")
		unescapedTitle = unescape (UnicodeDecodedTitle)
		scrapedtitle = unescapedTitle.encode("latin1","ignore") 
		# URL
		scrapedurl = urlparse.urljoin(url,match[1])
		# Thumbnail
		scrapedthumbnail = urlparse.urljoin(url,match[0])
		# Argumento

		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)

		# Añade al listado de XBMC
		xbmctools.addthumbnailfolder( CHANNELNAME , scrapedtitle , scrapedurl , scrapedthumbnail, "detail" )
	# Remove the next page mark
	patronvideos = '<a href="(http://cineblog01.com/film/category/numero/page/[0-9]+)">Avanti >'
	matches = re.compile (patronvideos, re.DOTALL). findall (data)
	scrapertools.printMatches (matches)

	if len(matches)>0:
		scrapedtitle = "Pagina seguente"
		scrapedurl = matches[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)
		xbmctools.addnewfolder( CHANNELNAME , "listcat" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )

	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def listvideos(params,url,category):
	xbmc.output("[cineblog01.py] mainlist")

	if url =="":
		url = "http://cineblog01.com/film/"

	# Descarga la página
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# Extrae las entradas (carpetas)
	patronvideos  = '<div id="covershot".*?<a.*?<img src="(.*?)".*?'
	patronvideos += '<div id="post-title"><a href="(.*?)".*?'
	patronvideos += '<h3>(.*?)</h3>.*?&#160;'
	patronvideos += '&#160;(.*?)</p>'
	#patronvideos += '<div id="description"><p>(.?*)</div>'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Titulo
		UnicodeDecodedTitle = match[2].decode("utf-8")
		unescapedTitle = unescape (UnicodeDecodedTitle)
		scrapedtitle = unescapedTitle.encode("latin1","ignore") 
		# URL
		scrapedurl = urlparse.urljoin(url,match[1])
		# Thumbnail
		scrapedthumbnail = urlparse.urljoin(url,match[0])
		# Argumento
		UnicodeDecodedTitle = match[3].decode("utf-8")
		unescapedTitle = unescape (UnicodeDecodedTitle)
		scrapedplot = unescapedTitle.encode("latin1","ignore") 
		#scrapedplot = match[3]
		# Depuracion
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)
#			xbmc.output("scrapeddescription="+scrapeddescription)

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detail" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Remove the next page mark
	patronvideos = '<a href="(http://cineblog01.com/film/page/[0-9]+)">Avanti >'
	matches = re.compile (patronvideos, re.DOTALL). findall (data)
	scrapertools.printMatches (matches)

	if len(matches)>0:
		scrapedtitle = "Pagina seguente"
		scrapedurl = matches[0]
		scrapedthumbnail = ""
		scrapedplot = ""
		if (DEBUG):
			xbmc.output("scrapedtitle="+scrapedtitle)
			xbmc.output("scrapedurl="+scrapedurl)
			xbmc.output("scrapedthumbnail="+scrapedthumbnail)
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def detail(params,url,category):
	xbmc.output("[cineblog01.py] detail")

	title = params.get("title")
	thumbnail = params.get("thumbnail")
	xbmc.output("[cineblog01.py] title="+title)
	xbmc.output("[cineblog01.py] thumbnail="+thumbnail)

	# Descarga la página
	data = scrapertools.cachePage(url)
	#xbmc.output(data)

	# ------------------------------------------------------------------------------------
	# Busca los enlaces a los videos
	# ------------------------------------------------------------------------------------
	listavideos = servertools.findvideos(data)

	for video in listavideos:
		xbmctools.addvideo( CHANNELNAME , "Megavideo - "+video[0] , video[1] , category , video[2] )
	# ------------------------------------------------------------------------------------

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
		
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )

	# End of directory...
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def play(params,url,category):
	xbmc.output("[cineblog01.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	xbmc.output("[cineblog01.py] thumbnail="+thumbnail)
	xbmc.output("[cineblog01.py] server="+server)
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

#mainlist(None,"","mainlist")
#detail(None,"http://impresionante.tv/ponyo.html","play")
