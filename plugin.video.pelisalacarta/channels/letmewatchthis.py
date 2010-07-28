# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para letmewatchthis
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
import config
from item import Item
import logger

CHANNELNAME = "letmewatchthis"

# Esto permite su ejecución en modo emulado
try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

# Traza el inicio del canal
logger.info("[letmewatchthis.py] init")

DEBUG = True

def mainlist(params,url,category):
	logger.info("[letmewatchthis.py] mainlist")
	
	itemlist = getmainlist(params,url,category)
	xbmctools.renderItems(itemlist, params, url, category)

def peliculas(params,url,category):
	logger.info("[letmewatchthis.py] peliculas")

	itemlist = getpeliculas(params,url,category)
	xbmctools.renderItems(itemlist, params, url, category)

def series(params,url,category):
	logger.info("[letmewatchthis.py] series")

	itemlist = getpeliculas(params,url,category)
	xbmctools.renderItems(itemlist, params, url, category)

def getmainlist(params,url,category):
	logger.info("[letmewatchthis.py] getmainlist")

	itemlist = []
	itemlist.append( Item(channel=CHANNELNAME, title="Movies" , action="peliculas", url="http://www.letmewatchthis.com/" , folder=True) )
	itemlist.append( Item(channel=CHANNELNAME, title="TV Shows" , action="series"   , url="http://www.letmewatchthis.com/?tv"  , folder=True) )
	
	return itemlist

def getpeliculas(params,url,category):
	logger.info("[letmewatchthis.py] getpeliculas")

	# ------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)

	# ------------------------------------------------------
	# Extrae las entradas
	# ------------------------------------------------------
	'''
	<div class="index_item index_item_ie"><a href="/watch-356059-Here-Come-the-Co-eds" title="Watch Here Come the Co-eds (1945) - 37 views"><img src="http://images.letmewatchthis.com/thumbs/356059_Here_Come_the_Co_eds_1945.jpg" border="0" alt="Watch Here Come the Co-eds"><h2>Here Come the Co-.. (1945)</h2></a><div class="index_ratings">
	<div id="unit_long356059">
	<ul style="width: 100px;" class="unit-rating">
	<li style="width: 60px;" class="current-rating">Current rating.</li> <li class="r1-unit"></li>
	<li class="r2-unit"></li>
	<li class="r3-unit"></li>
	<li class="r4-unit"></li>
	<li class="r5-unit"></li>
	</ul>
	</div>
	</div><div class="item_categories"><a href="/?genre=Comedy">Comedy</a> <a href="/?genre=Musical">Musical</a> </div></div>
	'''
	patronvideos  = '<div class="index_item index_item_ie"><a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"'

	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		# Titulo
		scrapedtitle = match[1]
		scrapedplot = ""
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = match[2]
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Añade al listado de XBMC
		itemlist.append( Item(channel=CHANNELNAME, action="listmirrors", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

	# ------------------------------------------------------
	# Extrae el paginador
	# ------------------------------------------------------
	#<span class=current>1</span> <a href="/index.php?page=2">2</a>
	patronvideos  = '<span class=current>[^<]+</span> <a href="([^"]+)">'
	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	if len(matches)>0:
		scrapedurl = urlparse.urljoin(url,matches[0])
		itemlist.append( Item(channel=CHANNELNAME, action="peliculas", title="!Next page" , url=scrapedurl , folder=True) )

	return itemlist

def listmirrors(params,url,category):
	logger.info("[letmewatchthis.py] listmirrors")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )

	# ------------------------------------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)
	'''
	<td align="left" valign="middle"><span class="movie_version_link">
	<a href="/external.php?title=A Bela e o Paparazzo&url=aHR0cDovL2thcmFtYmF2aWR6LmNvbS9tb2xuMXl3enlyZTE=&domain=karambavidz.com" onClick="return  addHit('1886018108', '1')" rel="nofollow" target="_blank"> Watch Version 1</a>
	[<a href="/external.php?title=A Bela e o Paparazzo&url=aHR0cDovL2thcmFtYmF2aWR6LmNvbS8yMmszeGYyNXdkY2g=&domain=karambavidz.com" onClick="return addHit('1886018108', '2')" rel="nofollow" target="_blank">Part 2</a>]
	</span></td>
	<td align="center" width="115" valign="middle" ><span class="version_host">karambavidz.com</span></td>
	<td width="65" align="center" valign="middle"><span class="version_veiws"> 502 views</span></td>
	'''
	patronvideos  = '<td[^>]+><span class="movie_version_link">[^<]+'
	patronvideos += '<a href="([^"]+)"[^>]+>([^<]+)</a>.*?'
	patronvideos += '</span></td>[^<]+'
	patronvideos += '<td align="center" width="115" valign="middle" ><span class="version_host">([^<]+)</span></td>[^<]+'
	patronvideos += '<td width="65" align="center" valign="middle"><span class="version_veiws">([^<]+)</span></td>'

	matches = re.compile(patronvideos,re.DOTALL).findall(data)
	if DEBUG: scrapertools.printMatches(matches)

	itemlist = []
	for match in matches:
		# Titulo
		scrapedtitle = match[1]+" ("+match[2]+") ("+match[3]+")"
		scrapedplot = ""
		scrapedurl = urlparse.urljoin(url,match[0])
		scrapedthumbnail = thumbnail
		if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
		xbmctools.addnewfolder( CHANNELNAME , "listvideos" , category , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )



def listvideos(params,url,category):
	logger.info("[letmewatchthis.py] listvideos")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = urllib.unquote_plus( params.get("plot") )
	url = url.replace(" ","%20")
	logger.info("url="+url)

	# ------------------------------------------------------------------------------------
	# Descarga la página
	# ------------------------------------------------------------------------------------
	data = scrapertools.cachePage(url)
	#logger.info(data)
	listavideos = servertools.findvideos(data)
	
	for video in listavideos:
		videotitle = video[0]
		scrapedurl = video[1]
		server = video[2]
		xbmctools.addnewvideo( CHANNELNAME , "play" , category , server , title.strip()+" "+videotitle , scrapedurl , thumbnail , plot )

	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def play(params,url,category):
	logger.info("[letmewatchthis.py] play")

	title = urllib.unquote_plus( params.get("title") )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = params["server"]

	xbmctools.playvideo(CHANNELNAME,server,url,category,title,thumbnail,plot)

