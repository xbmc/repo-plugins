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
import os
import xbmc
import xbmcaddon
import xbmcgui

base_url = 'http://tviplayer.iol.pt/'
img_base_url = 'http://www.iol.pt/multimedia/oratvi/multimedia/imagem/'
player = 'http://p.jwpcdn.com/6/12/jwplayer.flash.swf'
linkpart = ' live=true timeout=15'
addon_id = 'plugin.video.tviplayer'
mensagemok = xbmcgui.Dialog().ok
user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:41.0) Gecko/20100101 Firefox/41.0"
default_flash_Referer = "http://p.jwpcdn.com/6/12/jwplayer.flash.swf"
pesquisa_url = "http://tviplayer.iol.pt/pesquisa/"
direto_url = "http://tviplayer.iol.pt/direto/"  # TODO:
headers = {"Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": "http://tviplayer.iol.pt/direto",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu "
            "Chromium/62.0.3202.94 "
            "Chrome/62.0.3202.94 Safari/537.366"}

selfAddon = xbmcaddon.Addon(id=addon_id)
datapath = xbmc.translatePath(selfAddon.getAddonInfo('profile')).decode('utf-8')
addonfolder = xbmc.translatePath(selfAddon.getAddonInfo('path')).decode('utf-8')
artfolder = os.path.join(addonfolder, 'resources', 'img')
cookie_TviFile = os.path.join(datapath, 'cookieTvi.db')
msgok = xbmcgui.Dialog().ok
