# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para linkbucks
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import re, sys, os
import urlparse, urllib, urllib2
import os.path
import sys
import scrapertools
import config
import downloadtools
import logger

DEBUG = True
CHANNELNAME = "xmltoplaylist"
PLAYLIST_XML_FILENAME_TEMP = "video_playlist.xml.temp.pls"
FULL_FILENAME_PATH_XML = os.path.join( downloadtools.getDownloadPath(), PLAYLIST_XML_FILENAME_TEMP )
PLAYLIST_FILENAME_TEMP = "video_playlist.temp.pls"
FULL_FILENAME_PATH = os.path.join( downloadtools.getDownloadPath(), PLAYLIST_FILENAME_TEMP )

def geturl(xmlurl,title="default"):
	logger.info("[xmltoplaylist.py] geturl")
	
	return MakePlaylistFromXML(xmlurl)
	
def MakePlaylistFromXML(xmlurl,title="default"):
	logger.info("[%s.py] MakePlaylistFromXML" %CHANNELNAME)
	
	if title== ("default" or ""):
		nombrefichero = FULL_FILENAME_PATH_XML
	else:
		nombrefichero = os.path.join( downloadtools.getDownloadPath(),title + ".pls")
	xmldata = scrapertools.cachePage(xmlurl)
	patron = '<title>([^<]+)</title>.*?<location>([^<]+)</location>'
	matches = re.compile(patron,re.DOTALL).findall(xmldata)
	if len(matches)>0:
		playlistFile = open(nombrefichero,"w")
		playlistFile.write("[playlist]\n")
		playlistFile.write("\n")
		c = 0		
		for match in matches:
			c += 1
			playlistFile.write("File%d=%s\n"  %(c,match[1]))
			playlistFile.write("Title%d=%s\n" %(c,match[0]))
			playlistFile.write("\n")
			
		playlistFile.write("NumberOfEntries=%d\n" %c)
		playlistFile.write("Version=2\n")
		playlistFile.flush();
		playlistFile.close()	
		return nombrefichero
	else:
		return ""

def MakePlaylistFromList(Listdata,title="default"):
	logger.info("[%s.py] MakePlaylistFromList" %CHANNELNAME)
	
	if title== ("default" or ""):
		nombrefichero = FULL_FILENAME_PATH
	else:
		nombrefichero = os.path.join( downloadtools.getDownloadPath(),title + ".pls")
	
	if len(Listdata)>0:
		playlistFile = open(nombrefichero,"w")
		playlistFile.write("[playlist]\n")
		playlistFile.write("\n")
		c = 0		
		for match in Listdata:
			c += 1
			playlistFile.write("File%d=%s\n"  %(c,match[1]))
			playlistFile.write("Title%d=%s\n" %(c,match[0]))
			playlistFile.write("\n")
			
		playlistFile.write("NumberOfEntries=%d\n" %c)
		playlistFile.write("Version=2\n")
		playlistFile.flush();
		playlistFile.close()	
		return nombrefichero
	else:
		return ""