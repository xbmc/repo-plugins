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
import xbmc,xbmcgui,xbmcaddon,os

base_url = 'http://www.rtp.pt'
img_base_url = 'http://img0.rtp.pt'
player = 'http://programas.rtp.pt/play/player.swf?v3'
linkpart = ' live=true timeout=15'
addon_id = 'plugin.video.rtpplay'

selfAddon = xbmcaddon.Addon(addon_id)
datapath = xbmc.translatePath(selfAddon.getAddonInfo('profile')).decode('utf-8')
addonfolder = xbmc.translatePath(selfAddon.getAddonInfo('path')).decode('utf-8')
artfolder = os.path.join(addonfolder,'resources','img')
programafav = os.path.join(datapath,'favoritos')
watched_folder = os.path.join(datapath,'watched')
watched_database = os.path.join(datapath,'watched','watched.db')
msgok = xbmcgui.Dialog().ok

def translate(text):
      return selfAddon.getLocalizedString(text).encode('utf-8')
