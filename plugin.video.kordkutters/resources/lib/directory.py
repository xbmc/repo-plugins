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
from common_variables import *
from iofile import *
from kkplayer import *

#Function to build and return an episode item | tupple (url,listitem,isFolder)
def build_episode_item(name,url,mode,iconimage,page,info,video_info,audio_info):
	videoid = url
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&page="+str(page)
	ok=True
	liz=xbmcgui.ListItem(name)
	cm = []
	cm.append((translate(30005), 'XBMC.Action(Info)'))
	if info["playcount"] == 1: cm.append((translate(30007), 'XBMC.RunPlugin(%s?mode=7&url=%s)' % (sys.argv[0],videoid)))
	else: cm.append((translate(30006), 'XBMC.RunPlugin(%s?mode=6&url=%s)' % (sys.argv[0],videoid)))
	liz.setArt({ 'thumb': iconimage, 'banner' : os.path.join(artfolder,'banner.png'), 'fanart': os.path.join(addonfolder,'fanart.jpg') })
	liz.setPath(u)
	liz.setInfo( type="Video", infoLabels=info)
	liz.addStreamInfo('video', video_info)
	liz.addStreamInfo('audio', audio_info)
	liz.addContextMenuItems(cm, replaceItems=False)
	return (u,liz,False)


#Function to add a regular directory
def addDir(name,url,mode,iconimage,page,number_of_items,token,pasta=True):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&page="+str(page)+"&token="+urllib.quote_plus(token)
	ok=True
	liz=xbmcgui.ListItem(name)
	liz.setInfo( type="Video", infoLabels={ "Title": name })
	liz.setArt({ 'thumb': iconimage, 'banner' : os.path.join(artfolder,'banner.png'), 'fanart': os.path.join(addonfolder,'fanart.jpg') })
	liz.setPath(u)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=pasta,totalItems=number_of_items)
	return ok
