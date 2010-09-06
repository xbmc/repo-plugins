# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# tvalacarta - XBMC Plugin
# Canal para Argia Multimedia
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

xbmc.output("[argia.py] init")

DEBUG = True
CHANNELNAME = "Argia Multimedia"
CHANNELCODE = "argia"
MAINURL = "http://www.argia.com"
VIDEOURL = "http://www.argia.com/multimedia"

def mainlist(params,url,category):
	xbmc.output("[argia.py] mainlist")
	
	###
	### MAIN MENU
	###
	# Full Video List
	xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "Denak" , "http://www.argia.com/multimedia?p=1" , "" , "" )
	# Recommended
	xbmctools.addnewfolder( CHANNELCODE , "recommended" , CHANNELNAME , "Gomendatuak" , VIDEOURL , "" , "" )
	# Most Viewed (this week)
	xbmctools.addnewfolder( CHANNELCODE , "mostviewed" , CHANNELNAME , "Asteko ikusienak" , VIDEOURL , "" , "" )
	# Videos (sin categoria)
	xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "Bideoak" , "http://www.argia.com/multimedia/bideoak?p=1" , "" , "" )
	# Actos
	xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "Ekitaldiak" , "http://www.argia.com/multimedia/ekitaldiak?p=1" , "" , "" )
	# Cortometrajes
	xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "Film laburrak" , "http://www.argia.com/multimedia/laburrak?p=1" , "" , "" )
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def videolist(params,url,category):
	xbmc.output("[argia.py] videolist")

	# Page downloading
	data = scrapertools.cachePage(url)
	#xbmc.output(data)
	
	# Get #Next url
	'''
<a href="?p=2" title="Hurrengo orria">Hurrengoak»</a>
	'''
	pattern = '<a href="([^"]+)" title="Hurrengo orria">Hurrengoak'	# 0: url
	matches = re.compile(pattern,re.DOTALL).findall(data)
	
	try:
		urlnextpage = url[:-4]+matches[0]
	except:
		urlnextpage = ""
	
	if (DEBUG):
		xbmc.output("urlnextpage="+urlnextpage)
	
	if urlnextpage != "":
		# Add NEXT (as first item)
		xbmctools.addnewfolder( CHANNELCODE , "videolist" , CHANNELNAME , "#Hurrengoak" , urlnextpage , "" , "" )
	
	# Parse first video item
	'''
	<div class="titularplayer"><h1><a href="/multimedia/bideoa/pello-urizar">Pello Urizar</a></h1>
<p>Arrasate, 1968. Gazte Abertzaleak-eko idazkari nagusia izana. Arrasateko Udalean zinegotzia da. Elektronika eta Informatika ingeniari teknikoa. Kooperatibismoaren lan esperientzian zaildua, eta politikaren goi-mailara iritsia. Egun, Eusko Alkartasuneko idazkari nagusia da.</p>

	'''
	pattern =	'''(?x)															# Activate VERBOSE
		<div\ class="titularplayer"><h1>										#
		<a\ href="([^"]+)"														# $0 = video page url
		>([^<]+)</a></h1>.*?													# $1 = title
		<p>([^<]+)<																# $2 = description
				'''
	matches = re.compile(pattern,re.DOTALL).findall(data)
	#scrapertools.printMatches(matches)
	
	if len(matches) > 0:
		scrapedtitle = matches[0][1]+" (BERRIA!)".replace("&#39;","'").strip()
		scrapedurl = MAINURL+matches[0][0].replace("&amp;","&")
		scrapedthumbnail = ""
		scrapedplot = matches[0][2].replace("&#39;","'").strip()
		
		try:
			xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )
		except:
			xbmc.output("[argia.py] videolist: ERROR, i can't found first special video")
	
	# Parse video list
	'''
<div class="infoBideo">
  <p><a href="/multimedia/bideoa/larraulgo-eskola-12-urtera-arte"><img src="/multimedia/docs/bideoak/t_larrauljaurlaritza.jpg" alt="irudia" border="0" height="82" width="136"></a>
  <span class="titularpestaina"><a href="/multimedia/bideoa/larraulgo-eskola-12-urtera-arte">Larraulgo eskola 12 urtera arte</a></span><br> 
  Larraulgo (Gipuzkoa) eskolan Haur Hezkuntza (6 urtera artekoa) ematen da 2008an ireki zenetik. Larraulgo udalaren eta guraso elkartearen eskaria beti izan da Lehen Hezkuntza osoa (12 urtera artekoa)...</p>
</div>

<div class="infoBideo">
  <p><a href="/multimedia/laburra/raskaana"><img src="/multimedia/docs/bideoak/t_raskaana.jpg" alt="irudia" width="136" height="82" border="0" /></a>

  <span class="titularpestaina" ><a href="/multimedia/laburra/raskaana">Raskaana</a></span><br /> 
  Egilea: Oier U. (<a href="http://anpulubila.tximinia.net" title="Ireki esteka leiho berri batean" target="_blank">anpulubila.tximinia.net</a>)</p>
</div>

	'''
	
	pattern =	'''(?x)															# Activate VERBOSE
		<div\ class="info.*?">.*?												#
		<p><a\ href="([^"]+)">													# $0 = video page url
		<img\ src="([^"]+)".*?													# $1 = thumbnail url
		<span\ class="titular.*?".*?><.*?										#
		>([^<]+)</a><.*?><.*?													# $2 = title
		>([^<]+)<																# $3 = description
				'''
	matches = re.compile(pattern,re.DOTALL).findall(data)
	#scrapertools.printMatches(matches)

	for match in matches:
		# Is it a video? Suuure?
		if match[0].split('/')[2] != 'galeria' and match[0].split('/')[2] != 'diaporama':
			scrapedtitle = match[2].replace("&#39;","'").strip()
			scrapedurl = MAINURL+match[0].replace("&amp;","&")
			scrapedthumbnail = MAINURL+match[1].replace("&amp;","&")
			scrapedplot = match[3].replace("&#39;","'").strip()
			if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"], description=["+scrapedplot+"]")
			# Add item
			xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def recommended(params,url,category):
	xbmc.output("[argia.py] recommended")
	# Page downloading
	data = scrapertools.cachePage(url)
	
	# Parse data
	'''
	<div class="itemtxuri">
					<p><a href="/multimedia/diaporama/zabor-mendietako-bizitzak"><img src="/multimedia/docs/diaporamak/t_zaborraZabalza.jpg" alt="irudia" width="135" height="82" border="0" /></a>
					<a href="/multimedia/diaporama/zabor-mendietako-bizitzak"><span class="titularpestaina">Zabor mendietako bizitzak</span></a><br /> 
					  Zakarra azkenaldiko eztabaidagai nagusi bilakatzeak ondorio garbi bat dakar: baztertu, estali eta...</p>
				  </div>

	'''
	
	pattern =	'''(?x)															# Activate VERBOSE
		<div\ class="item.*?">.*?												#
		<p><a\ href="([^"]+)">													# $0 = video page url
		<img\ src="([^"]+)".*?													# $1 = thumbnail url
		<span\ class="titular.*?"												#
		>([^<]+)</span></a><.*?													# $2 = title
		>([^<]+)</p>															# $3 = description
				'''
	matches = re.compile(pattern,re.DOTALL).findall(data)
	#scrapertools.printMatches(matches)
	
	matchid = 0
	for match in matches:
		# Only first 15 elements are "Recommended"
		if matchid < 15:
			# Is it a video? Suuure?
			##xbmc.output("[argia.py] recommended: Split"+match[0].split('/')[2])
			if match[0].split('/')[2] != 'galeria' and match[0].split('/')[2] != 'diaporama':
				scrapedtitle = match[2].replace("&#39;","'").strip()
				scrapedurl = MAINURL+match[0].replace("&amp;","&")
				scrapedthumbnail = MAINURL+match[1].replace("&amp;","&")
				scrapedplot = match[3].replace("&#39;","'").strip()
				#if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"], description=["+scrapedplot+"]")
				# Add item
				xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )
		matchid = matchid+1
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )



def mostviewed(params,url,category):
	xbmc.output("[argia.py] mostviewed")
	# Page downloading
	data = scrapertools.cachePage(url)
	
	# Parse data
	'''
	<div class="itemtxuri">
					<p><a href="/multimedia/diaporama/zabor-mendietako-bizitzak"><img src="/multimedia/docs/diaporamak/t_zaborraZabalza.jpg" alt="irudia" width="135" height="82" border="0" /></a>
					<a href="/multimedia/diaporama/zabor-mendietako-bizitzak"><span class="titularpestaina">Zabor mendietako bizitzak</span></a><br /> 
					  Zakarra azkenaldiko eztabaidagai nagusi bilakatzeak ondorio garbi bat dakar: baztertu, estali eta...</p>
				  </div>

	'''
	
	pattern =	'''(?x)															# Activate VERBOSE
		<div\ class="item.*?">.*?												#
		<p><a\ href="([^"]+)">													# $0 = video page url
		<img\ src="([^"]+)".*?													# $1 = thumbnail url
		<span\ class="titular.*?"												#
		>([^<]+)</span></a><.*?													# $2 = title
		>([^<]+)</p>															# $3 = description
				'''
	matches = re.compile(pattern,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	
	matchid = 0
	for match in matches:
		# First 15 elements are "Recommended"
		if matchid > 14:
			# Is it a video? Suuure?
			##xbmc.output("[argia.py] recommended: Split"+match[0].split('/')[2])
			if match[0].split('/')[2] != 'galeria' and match[0].split('/')[2] != 'diaporama':
				scrapedtitle = match[2].replace("&#39;","'").strip()
				scrapedurl = MAINURL+match[0].replace("&amp;","&")
				scrapedthumbnail = MAINURL+match[1].replace("&amp;","&")
				scrapedplot = match[3].replace("&#39;","'").strip()
				#if (DEBUG): xbmc.output("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"], description=["+scrapedplot+"]")
				# Add item
				xbmctools.addnewvideo( CHANNELCODE , "play" , category , "Directo" , scrapedtitle , scrapedurl , scrapedthumbnail , scrapedplot )
		matchid = matchid+1
	
	# Label (top-right)...
	xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=category )
	# Disable sorting...
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
	# End of directory...
	xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

def play(params,url,category):
	xbmc.output("[argia.py] play")
	
	# Page downloading
	data = scrapertools.cachePage(url)
	
	##
	## PARSE VIDEO DATA
	##
	'''
s1.addVariable('file','/multimedia/docs/bideoak/dantzaTradizioa.flv');
	'''
	#pattern = 'file=(.*?).flv'
	pattern = "s1\.addVariable\('file','([^']+)'\)"
	matches = re.compile(pattern,re.DOTALL).findall(data)
	scrapertools.printMatches(matches)
	
	try:
		url = MAINURL+matches[0]
	except:
		url = ""
	
	title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
	thumbnail = urllib.unquote_plus( params.get("thumbnail") )
	plot = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
	server = "Directo"

	xbmctools.playvideo(CHANNELCODE,server,url,category,title,thumbnail,plot)
