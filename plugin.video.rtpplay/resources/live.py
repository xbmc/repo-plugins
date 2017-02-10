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
import xbmc,xbmcgui,xbmcplugin,xbmcaddon,sys,os,re,base64
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
		match=re.compile('<a title="(.+?)" href="(.+?)" class="mask-live"><img alt="(.+?)" src="(.*?)"').findall(page_source)
		totaltv = len(match)
		for titulo,url2,prog,img_old in match:
			try:
				titulo = title_clean_up(titulo)
				stream_url = base_url + url2
				if "http" not in img_old: img = "http:" + img_old
				else: img = img_old
				addDir('[B][COLOR blue]' + titulo + '[/COLOR]' +' - ' + title_clean_up(prog)+ '[/B]',stream_url,23,img,totaltv,pasta=False,information={"Title":titulo,"plot":prog})
			except: pass
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
			#Scrape the page source for each type of stream	
			match = re.compile('"stream_wma" : "(.+?)"').findall(page_source)
			if match:
				url2=match[0]
				return url2
			#Grab HLS stream
			smil_ = re.compile('file: "(.+?)",').findall(page_source)
			if smil_:
					if "http" not in smil_[0] : stream = "http:"+smil_[0]
					else: stream = smil_[0] 
					return stream+'|User-Agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36&Referer=http://www.rtp.pt/play/'
			else:
				msgok(translate(30001),translate(30018))
	else:
		return None

def play_live(url,name,iconimage):
	stream_url = grab_live_stream_url(url)
	listitem = xbmcgui.ListItem(path=stream_url,label=name)
	listitem.setArt({"thumb":iconimage})
	listitem.setProperty('IsPlayable', 'true')
	xbmc.Player().play(stream_url,listitem)
		
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
