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
import xbmc,xbmcgui,xbmcplugin,xbmcaddon,sys,os,re
from webutils import *
from common_variables import *
from directory import *

channel_db = {"rtp1": ["RTP 1","http://img0.rtp.pt/play/images/logo_rtp1.jpg"],"rtp2": ["RTP 2","http://img0.rtp.pt/play/images/logo_rtp2.jpg"], "rtpinformacao": ["RTP Informação","http://img0.rtp.pt/play/images/logo_rtpinformacao.jpg"],"rtpinternacional": ["RTP Internacional","http://img0.rtp.pt/play/images/logo_rtpinternacional.jpg"],"rtpmemoria": ["RTP Memória","http://img0.rtp.pt/play/images/logo_rtpmemoria.jpg"],"rtpmadeira": ["RTP Madeira","http://img0.rtp.pt/play/images/logo_rtpmadeira.jpg"],"rtpacores": ["RTP Açores","http://img0.rtp.pt/play/images/logo_rtpacores.jpg"],"rtpafrica": ["RTP África","http://img0.rtp.pt/play/images/logo_rtpafrica.jpg"]}


def radiotv_channels(url):
	try:
		page_source = abrir_url(url)
	except:
		page_source = ''
		msgok(translate(30001),translate(30018))
	if page_source:
		match=re.compile('<a title="(.+?)" href="(.+?)" class="mask-live"><img alt="(.+?)" src=".+?src=(.+?)&.+?" c').findall(page_source)
		totaltv = len(match)
		for titulo,url2,prog,img_old in match:
			titulo = title_clean_up(titulo)
			stream_url = grab_live_stream_url(base_url + url2)
			img = img_base_url + img_old
			addLink('[B][COLOR blue]' + titulo + '[/COLOR]' +' - ' + title_clean_up(prog)+ '[/B]',stream_url,img,totaltv)
		xbmc.executebuiltin("Container.SetViewMode(500)")
	else:
		sys.exit(0)


def grab_live_stream_url(url):
	try:
		page_source = abrir_url(url)
	except:
		page_source = ''
		msgok(translate(30001),translate(30018))
	if page_source:
		if re.search('mms:', page_source):
        		match=re.compile('\"file\": \"(.+?)\",\"streamer\": \"(.+?)\"').findall(page_source)
        		try:
        			url2 = match[0][1] + match[0][0]
        			return url2
        		except: pass
    		else:	
    			#Heuristic rules to automatically find the best stream type for each platform    		
			type_stream=selfAddon.getSetting('tipostr')		
			if type_stream == '0':
				if xbmc.getCondVisibility('system.platform.OSX'): versao = 'rtmp'
				elif xbmc.getCondVisibility('system.platform.IOS'): versao = 'm3u8'
				elif xbmc.getCondVisibility('system.platform.ATV2'): versao = 'm3u8'		
				elif xbmc.getCondVisibility('system.platform.Windows'): versao = 'rtmp'
				elif xbmc.getCondVisibility('system.platform.Android'): versao = 'm3u8'
				elif xbmc.getCondVisibility('system.platform.linux'):
					if 'armv6' in os.uname()[4]: versao = 'm3u8'
					else: versao = 'rtmp'
			elif type_stream == '1': versao = 'rtmp'
			elif type_stream == '2': versao = 'm3u8'
			#Scrape the page source for each type of stream	
			if versao == 'rtmp':
				match=re.compile('"file": "(.+?)",.+?\n.+?"application": "(.+?)",.+?\n.+?"streamer": "(.+?)",').findall(page_source)
        			url2 = 'rtmp://' + match[0][2] +'/' + match[0][1] + '/' + match[0][0] + ' swfUrl=' + player + linkpart
        			return url2
        		else:
				match=re.compile('\"smil\":(.+?)\"').findall(page_source)
				if not match:
					match=re.compile('\"d\":(.+?)\"').findall(page_source)
        			url2 = match[0].replace('"','')
        			return url2
	else:
		return None
		
def play_from_outside(name):
	url = 'http://www.rtp.pt/play/direto/' + name
	stream_url = grab_live_stream_url(url)
	if stream_url:
		if name in channel_db.keys():
			labelname = channel_db[name][0]
			thumbnail = channel_db[name][1]
		else:
			labelname = name
			thumbnail = "http://img0.rtp.pt/play/images/logo_" + name + ".jpg"
		listitem = xbmcgui.ListItem(labelname, iconImage=thumbnail, thumbnailImage=thumbnail)
		listitem.setLabel(labelname)
		listitem.setInfo("Video", {"Title":labelname})
		listitem.setProperty('mimetype', 'video/x-msvideo')
		listitem.setProperty('IsPlayable', 'true')
		listitem.setPath(path=stream_url)
		xbmcplugin.setResolvedUrl(int(sys.argv[1]),True,listitem)
	
