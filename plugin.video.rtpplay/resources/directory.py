#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
 Author: enen92 

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
 
"""
import xbmc,xbmcplugin,xbmcaddon,xbmcgui,sys,os,urllib,xbmcvfs
from utilities import *
from common_variables import *
from iofile import *


#Function to add a Show directory
def addprograma(name,url,mode,iconimage,number_of_items,information):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
	try: u +="&plot="+urllib.quote_plus(information["plot"])
	except: pass
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setProperty('fanart_image', os.path.join(artfolder,'fanart.png'))
	liz.setInfo( type="Video", infoLabels=information)
	contextMenuItems = []
	savepath = programafav
	NewFavFile=os.path.join(programafav,removeNonAscii(name.lower())+'.txt')
	if xbmcvfs.exists(NewFavFile):
		contextMenuItems.append((translate(30019), 'XBMC.RunPlugin(%s?mode=20&name=%s&url=%s&iconimage=%s)' % (sys.argv[0], name, urllib.quote_plus(url), iconimage)))
	else:
		contextMenuItems.append((translate(30020), 'XBMC.RunPlugin(%s?mode=19&name=%s&url=%s&iconimage=%s&plot=%s)' % (sys.argv[0], name, urllib.quote_plus(url), urllib.quote_plus(iconimage), urllib.quote_plus(information["plot"]))))
	liz.addContextMenuItems(contextMenuItems, replaceItems=False)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True,totalItems=number_of_items)
	return ok
	
#Function to add a Episode
def addepisode(name,url,mode,iconimage,number_of_items,information):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
	ok=True
	contextMenuItems = []
	if xbmcvfs.exists(watched_database):
		text_db = readfile(watched_database)
		database = eval(text_db)
		if url in database.keys():
			overlay=7
			playcount=1
			information["overlay"]=overlay
			information["playcount"]=playcount
			contextMenuItems.append((translate(30021), 'XBMC.RunPlugin(%s?mode=22&name=%s&url=%s&iconimage=%s)' % (sys.argv[0], name, urllib.quote_plus(url), iconimage)))
		else: contextMenuItems.append((translate(30022), 'XBMC.RunPlugin(%s?mode=21&name=%s&url=%s&iconimage=%s)' % (sys.argv[0], name, urllib.quote_plus(url), iconimage)))
	else: contextMenuItems.append((translate(30022), 'XBMC.RunPlugin(%s?mode=21&name=%s&url=%s&iconimage=%s)' % (sys.argv[0], name, urllib.quote_plus(url), iconimage)))
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setProperty('fanart_image', os.path.join(artfolder,'fanart.png'))
	liz.setInfo( type="Video", infoLabels=information)
	liz.addContextMenuItems(contextMenuItems, replaceItems=False)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False,totalItems=number_of_items)
	return ok
		
#Function to add a video/audio Link
def addLink(name,url,iconimage,number_of_items):
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setProperty('fanart_image', os.path.join(artfolder,'fanart.png'))
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False,totalItems=number_of_items)
	return ok

#Function to add a regular directory
def addDir(name,url,mode,iconimage,number_of_items,pasta=True,information=None):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	try: u +="&plot="+urllib.quote_plus(information["plot"])
	except: pass
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setProperty('fanart_image', os.path.join(artfolder,'fanart.png'))
	if not information:
		information = { "Title": name }
	liz.setInfo( type="Video", infoLabels=information)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=pasta,totalItems=number_of_items)
	return ok
