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
import xbmc,xbmcgui,xbmcaddon,os

base_url = 'http://tviplayer.iol.pt/'
img_base_url = 'http://www.iol.pt/multimedia/oratvi/multimedia/imagem/'
player = 'http://p.jwpcdn.com/6/12/jwplayer.flash.swf'
linkpart = ' live=true timeout=15'
addon_id = 'plugin.video.tviplayer'
mensagemok = xbmcgui.Dialog().ok
user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:41.0) Gecko/20100101 Firefox/41.0"
default_flash_Referer = "http://p.jwpcdn.com/6/12/jwplayer.flash.swf"
pesquisa_url="http://tviplayer.iol.pt/pesquisa/"

selfAddon = xbmcaddon.Addon(id=addon_id)
datapath = xbmc.translatePath(selfAddon.getAddonInfo('profile')).decode('utf-8')
addonfolder = xbmc.translatePath(selfAddon.getAddonInfo('path')).decode('utf-8')
artfolder = os.path.join(addonfolder,'resources','img')
cookie_TviFile = os.path.join(datapath,'cookieTvi.db')
msgok = xbmcgui.Dialog().ok
