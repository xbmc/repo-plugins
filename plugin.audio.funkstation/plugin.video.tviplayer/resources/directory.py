#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
 Author: darksky83

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



#Function to add a Show directory
def addprograma(name,url,mode,iconimage,number_of_items,information,fanart_image=''):
    if (fanart_image==''):
        if iconimage:
            fanart_image= iconimage
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(fanart_image)
    try: u +="&plot="+urllib.quote_plus(information["plot"])
    except: pass
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if fanart_image=='':
        liz.setProperty('fanart_image', os.path.join(artfolder,'fanart.png'))
    else:
        liz.setProperty('fanart_image', fanart_image)
    liz.setInfo( type="Video", infoLabels=information)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True,totalItems=number_of_items)
    return ok

#Function to add a Episode
def addepisode(name,url,mode,iconimage, number_of_items,information,fanart_image):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if fanart_image=='':
        liz.setProperty('fanart_image', os.path.join(artfolder,'fanart.png'))
    else:
        liz.setProperty('fanart_image', fanart_image)

    liz.setInfo( type="Video", infoLabels=information)
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
def addDir(name,url,mode,iconimage,number_of_items,pasta=True,informacion=None):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    try: u +="&plot="+urllib.quote_plus(informacion["plot"])
    except: pass
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setProperty('fanart_image', os.path.join(artfolder,'fanart.png'))
    liz.setInfo( type="Video", infoLabels={ "Title": name })
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=pasta,totalItems=number_of_items)
    return ok
