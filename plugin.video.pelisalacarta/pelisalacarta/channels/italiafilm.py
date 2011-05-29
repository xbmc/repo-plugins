# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para filmstreaming [it]
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse
import urllib2
import urllib
import re
import os
import sys

from core import scrapertools
from core import logger
from core import config
from core.item import Item
from core import xbmctools
from pelisalacarta import buscador

from servers import servertools
from servers import vk

import xbmc
import xbmcgui
import xbmcplugin

CHANNELNAME = "italiafilm"
EVIDENCE = "   "

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[italiafilm.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[italiafilm.py] mainlist")

	# Añade al listado de XBMC
	xbmctools.addnewfolder( CHANNELNAME , "searchmovie" , category , "Cerca Film","","","")
        xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Novità" , "http://italia-film.com/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Anime" , "http://italia-film.com/anime-e-cartoon/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Telefilm" , "http://italia-film.com/telefilm/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Animazione" , "http://italia-film.com/film-animazione/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Avventura" , "http://italia-film.com/film-avventura/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Azione" , "http://italia-film.com/film-azione/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Comici" , "http://italia-film.com/film-comici/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Commedia" , "http://italia-film.com/film-commedia/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Documentari" , "http://italia-film.com/film-documentari/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Drammatici" , "http://italia-film.com/film-drammatici/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Fantascienza" , "http://italia-film.com/film-fantascienza/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Fantasy" , "http://italia-film.com/film-fantasy/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Gangster" , "http://italia-film.com/film-gangster/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Guerra" , "http://italia-film.com/film-guerra/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Horror" , "http://italia-film.com/film-horror/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Musical" , "http://italia-film.com/film-musical/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Poliziesco" , "http://italia-film.com/film-poliziesco/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Romantici" , "http://italia-film.com/film-romantici/","","") 
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Erotici" , "http://italia-film.com/film-erotici/","","") 
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Storici" , "http://italia-film.com/film-storici/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Thriller" , "http://italia-film.com/film-thriller/","","")
	xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , "Film Western" , "http://italia-film.com/film-western/","","")

	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
	
def searchmovie(params,url,category):
	xbmc.output("[italiafilm.py] searchmovie")

	keyboard = xbmc.Keyboard('')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		tecleado = keyboard.getText()
		if len(tecleado)>0:
			#convert to HTML
			tecleado = tecleado.replace(" ", "+")
			searchUrl = "http://italia-film.com/index.php?story={"+tecleado+"}&do=search&subaction=search"
			peliculas(params,searchUrl,category)

def peliculas(params,url,category):
	logger.info("[italiafilm.py] peliculas")

	# Descarga la página
	data = scrapertools.cachePage(url)

	# Extrae las entradas (carpetas)
	patronvideos  = '<div class="notes">.*?<a href="([^"]+).*?<img.*?src="([^"]+)".*?title=\'([^\']+)'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	
	for match in matches:
		# Atributos
		scrapedtitle = match[2]
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = urlparse.urljoin(url,match[1])
		scrapedplot = ""
		
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "detalle" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Extrae las entradas (carpetas)
	patronvideos  = '<a href="([^"]+)">Avanti&nbsp;&#8594;'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		# Atributos
		scrapedtitle = "Pagina seguente"
		scrapedurl = urlparse.urljoin(url,match)
		scrapedthumbnail = ""
		scrapedplot = ""

		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		xbmctools.addnewfolder( CHANNELNAME , "peliculas" , category , scrapedtitle , scrapedurl , scrapedthumbnail, scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def detalle(params,url,category):
	logger.info("[italiafilm.py] detalle")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	title = to_ita(title)
	title = title.title()
	title = title.replace('Serie Tv', '', 1)
	title = title.replace('Streaming', '', 1)
	title = title.replace('Megavideo', '', 1)

	# Descarga la página
	data = scrapertools.cachePage(url)
	data_next = ""
	sep_data = '<br /><br />'

	# Delimits the links area
	i_data = data.find('<td class="news">')
	data = data[i_data:]
	f_data = data.find('</td>')
	data = data[:f_data]
	data = to_ita(data)
	
	# Extract the plot
	# [BUG] if plot have br inside - the text after br is omitted
	patronvideos  = '<td class="news">.*?<div id=[^>]+>([^<]+)'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	if (matches): plot = matches[0]
	
	# Delimits link area
	# [BUG] in 'due fantagenitori' page, the title 'Prima stagione' is omitted
	i_data = data.find(sep_data)
	if (i_data > -1): data = data[i_data:]

	# ------------------------------------------------------------------------------------
	# looking for seasons
	# ------------------------------------------------------------------------------------
	patronseason  = '>([^<]+)' + sep_data
	matches_season = re.compile(patronseason,re.DOTALL).findall(data)
	scrapertools.printMatches(matches_season)

	if (matches_season):
		logger.info("[italiafilm.py] season list match ok")
		
		seasontitle = matches_season[0]
		f_season = data.find(seasontitle+sep_data)
		data_next = data[f_season:]
		data = data[:f_season]
		
		loadvideo(params,data,category,title,thumbnail,plot)

		data = data_next
		data_next = ""
		
		i = 0 #counter for while
		while i < len(matches_season)-1:
			seasontitle = matches_season[i]
			seasontitle_next = matches_season[i+1]
			seasonlabel = xbmcgui.ListItem(EVIDENCE+seasontitle)
			seasonlabel.setInfo( type="Video", infoLabels={ "Title": EVIDENCE+seasontitle } )
			xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url="",listitem=seasonlabel,isFolder=False)
			i_season = data.find(seasontitle+sep_data) + len(seasontitle)+len(sep_data)
			data = data[i_season:]
			f_season = data.find(seasontitle_next+sep_data)
			data_next = data[f_season:]
			data = data[:f_season]
			
			loadvideo(params,data,category,title,thumbnail,plot)

			data = data_next
			data_next = ""
			i = i + 1
			#end while
		
		if (matches_season[i]):
			seasontitle = matches_season[i]
			seasonlabel = xbmcgui.ListItem(EVIDENCE+seasontitle)
			seasonlabel.setInfo( type="Video", infoLabels={ "Title": EVIDENCE+seasontitle } )
			xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url="",listitem=seasonlabel,isFolder=False)
			i_season = data.find(seasontitle+sep_data) + len(seasontitle)+len(sep_data)
			data = data[i_season:]
			
	#end if matches_season
	# ------------------------------------------------------------------------------------
		
	loadvideo(params,data,category,title,thumbnail,plot)
		
	# Cierra el directorio
	xbmcplugin.setPluginCategory( handle=pluginhandle, category=category )
	xbmcplugin.addSortMethod( handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=pluginhandle, succeeded=True )

def loadvideo(params,data,category,title,thumbnail,plot):
	# ----------------------------------------------------------
	# the loading of series with a lot of seasons is very slow
	# this system prevents freeze everytime in loading screen
	# ----------------------------------------------------------
	logger.info("[italiafilm.py] loadvideo")
	max_len = 3000
	if (len(title) > 50): title = title[:50]+"..."
	while (len(data) > max_len): 
		data_all = data
		data_trunc = data[:max_len].rfind('<a ')
		if(data_trunc <= 0):
			data = data = data_all[max_len:]
		else:
			data = data[:data_trunc]
			listavideos = servertools.findvideos(data)
			for video in listavideos:
				videotitle = video[0]
				url = video[1]
				server = video[2]
				patronvideos  = url+'[^>]+>([^<]+)'
				matches = re.compile(patronvideos,re.DOTALL).findall(data)
				scrapertools.printMatches(matches)
				if (matches): videotitle = matches[0]
				xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip() + " - " + videotitle + " ["+server+"]" , url , thumbnail , plot )
			data = data_all[data_trunc:]
	#end while
	listavideos = servertools.findvideos(data)
	for video in listavideos:
		videotitle = video[0]
		url = video[1]
		server = video[2]
		patronvideos  = url+'[^>]+>([^<]+)'
		matches = re.compile(patronvideos,re.DOTALL).findall(data)
		scrapertools.printMatches(matches)
		if (matches): videotitle = matches[0]
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip() + " - " + videotitle + " ["+server+"]" , url , thumbnail , plot )

def play(params,url,category):
	logger.info("[italiafilm.py] play")

	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]
	
	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)
	
def to_ita(text):
	text = text.replace('&amp;', '&')
	text = text.replace('&#224;', 'a\'')
	text = text.replace('&#232;', 'e\'')
	text = text.replace('&#233;', 'e\'')
	text = text.replace('&#236;', 'i\'')
	text = text.replace('&#242;', 'o\'')
	text = text.replace('&#249;', 'u\'')
	text = text.replace('&#215;', 'x')
	text = text.replace('&#039;', '\'')
	return text
