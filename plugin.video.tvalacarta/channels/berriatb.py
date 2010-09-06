# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para Berria Telebista
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

try:
	pluginhandle = int( sys.argv[ 1 ] )
except:
	pluginhandle = ""

xbmc.output("[berriatb.py] init")

DEBUG = True
CHANNELNAME = "berriatb"
CHANNELCODE = "berriatb"

def mainlist(params,url,category):
	xbmc.output("[berriatb.py] mainlist")
	
	###
	### MAIN MENU
	###
	# Full Video List
	xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "Zerrenda" , "http://www.berria.info/berriatb/zerrenda/" , "" , "" )
	# Interviews
	xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "Esan Ahala (Elkarrizketak)" , "http://www.berria.info/berriatb/esanahala/" , "" , "" )
	# Most Viewed (disabled)
	#xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "Ikusienak" , "http://www.berria.info/berriatb/ikusienak/" , "" , "" )
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def videolist(params,url,category):
	xbmc.output("[berriatb.py] videolist")

	# Page downloading
	data = scrapertools.cachePage(url)
	#xbmc.output(data)
	
	# Get #Next url
	'''
<span class="gehiago"><a class="hurrengoa" href="http://berria.info/berriatb/esanahala/zerrenda/6/">Hurrengoak &raquo;</a></span>
	'''
	pattern = '<a class="hurrengoa" href="([^"]+)">Hurrengoak' # 0: url
	matches = re.compile(pattern,re.DOTALL).findall(data)
	
	try:
		urlnextpage = matches[0]
	except:
		urlnextpage = url
	
	if (DEBUG):
		xbmc.output("urlnextpage="+urlnextpage)
	
	# Add NEXT (as first item)
	xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "#Hurrengoa" , urlnextpage , "" , "" )
	
	# Parse video list
	'''
<div class="garbitzailea"></div>
    <div class="bideotxikiak">
    <p><a href="http://berria.info/berriatb/esanahala/5/" title="" class="thickbox"><img src="http://208.79.203.90/berria/bideoak/bideoa653.jpg" width="158" alt="Aintzane Ezenarro" /></a></p>
    <p class="titularra"><a href="http://berria.info/berriatb/esanahala/5/" title="Aintzane Ezenarro">Aintzane Ezenarro</a></p>

	<div class="garbitzailea"></div>
    <p><span class="sinadura_data">2009-09-20</span></p>
  </div>
	'''
	pattern  = '<div class="bideotxikiak">.*?<p><a href="([^"]+)" title.*?'		# 0: url
	pattern += '<img src="([^"]+)".*?' 											# 1: thumbnail
	pattern += '<p class="titularra">.*?title="([^"]+)".*?'						# 2: title
	#pattern += 'sinadura_data">(.*?)<.*?'										# 3: date
	matches = re.compile(pattern,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)

	for match in matches:
		#scrapedtitle = match[2].strip()+" ("+match[3]+")"
		scrapedtitle = match[2].replace("&#39;","'").strip()
		scrapedurl = match[0].replace("&amp;","&")
		scrapedthumbnail = match[1].replace("&amp;","&")
		scrapedplot = scrapedtitle # Same as title
		if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

		# Add item
		xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def play(params,url,category):
	xbmc.output("[berriatb.py] play")
	
	# Page downloading
	data = scrapertools.cachePage(url)
	
	##
	## PARSE VIDEO DATA
	##
	'''
Option1:

s1.addParam("flashvars","file=http://208.79.203.90/berria/bideoak/bideoa821.mp4&image=http://208.79.203.90/berria/bideoak/bideoa821.jpg&logo=http://208.79.203.90/berria/logo2_tv.png&stretching=fill&fullscreen=true&autostart=false&duration=17");
    			s1.write('player');
Option2:

"file":"http://208.79.203.90/berria/bideoak/bideoa786.mp4",
                        "scaling": 'fit',
                        "duration":"00:22:29"

	'''
	pattern = 'file.*?http://(.*?).mp4'
	matches = re.compile(pattern,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	
	try:
		url = "http://"+matches[0]+".mp4"
	except:
		url = ""
	
	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = "Directo"

	xbmctools.playvideo(CHANNELCODE,server,url,category,title,thumbnail,plot)
