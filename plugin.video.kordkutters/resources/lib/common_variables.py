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
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import xbmcvfs
import os
import sys

####### Specific youtube, youtube channel or addon configuration variables ###########
#youtube
channel_id = "UCtp9s4L-kxIRy221VVtgjXg"
youtube_api_key = "AIzaSyAxaHJTQ5zgh86wk7geOwm-y0YyNMcEkSc" #If you fork this addon please register another api key (https://developers.google.com/youtube/android/player/register)
#youtube channel
cast = ['Nathan Betzen','Ned Scott'] #Team members / Cast of the channel. [] if none
tvshowtitle = 'KordKutters' #Name of the show
status = 'Continuing' #Status of the show
episode_playlists = ['PL5BrgZd5yMYgty7363LhlkR8iPJ73-fCZ'] #List of playlists to consider every integer as the episode number

#addon config
show_live_category = True #hides Live directory if set to False
show_channel_playlists = True #hides channel playlists from main menu if set to False
######################################################################################

addon_id = xbmcaddon.Addon().getAddonInfo('id')
selfAddon = xbmcaddon.Addon(id=addon_id)
datapath = xbmc.translatePath(selfAddon.getAddonInfo('profile')).decode('utf-8')
addonfolder = xbmc.translatePath(selfAddon.getAddonInfo('path')).decode('utf-8')
artfolder = os.path.join(addonfolder,'resources','img')
watchedfolder = os.path.join(datapath,'watched')
msgok = xbmcgui.Dialog().ok
show_uploads_playlist = bool(selfAddon.getSetting('show_uploads_playlist') == 'true')

def makefolders():
	if not os.path.exists(datapath): xbmcvfs.mkdir(datapath)
	if not os.path.exists(watchedfolder):xbmcvfs.mkdir(watchedfolder)
	return

def translate(text):
	return selfAddon.getLocalizedString(text).encode('utf-8')
	
def add_sort_methods():
	sort_methods = [xbmcplugin.SORT_METHOD_UNSORTED,xbmcplugin.SORT_METHOD_LABEL,xbmcplugin.SORT_METHOD_DATE,xbmcplugin.SORT_METHOD_DURATION,xbmcplugin.SORT_METHOD_EPISODE]
	for method in sort_methods:
		xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod=method)
	return
