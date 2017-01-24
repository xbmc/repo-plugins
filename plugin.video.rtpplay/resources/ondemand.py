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

import xbmc,xbmcgui,xbmcaddon,xbmcplugin,xbmcvfs,sys,os,re
from common_variables import *
from directory import *
from webutils import *
from utilities import *
from resolver import *
from rtpplayer import *
from iofile import *

def list_tv_shows(name,url):
	try:
		page_source = abrir_url(url)
	except:
		page_source = ''
		msgok(translate(30001),translate(30018))
	if page_source:
		match=re.compile('<a class="text-white" href="(.+?)" title=".+?">(.+?)</a>').findall(page_source)
		totalit= len(match)
		for urlsbase,titulo in match:
			titulo = title_clean_up(titulo)
			if selfAddon.getSetting('icon_plot') == 'true':
				try:
					html_source = abrir_url(base_url + urlsbase)
				except: html_source = ''
				if html_source:
					try: thumbnail=re.compile('<img class="pull-left" src="(.+?)"').findall(html_source)[0]
					except: thumbnail=''
					sinopse= re.findall('id="promo">.+?\n.+?<p>(.*?)</p>', html_source, re.DOTALL)
					if sinopse: information = { "Title": name,"plot": clean_html(title_clean_up(sinopse[0])) }
					else: information = { "Title": name,"plot":translate(30026) }
				addprograma(titulo,base_url + urlsbase,16,thumbnail,totalit,information)
			else:
				information = { "Title": name,"plot":translate(30026) }
				thumbnail = ''
				addprograma(titulo,base_url + urlsbase,15,thumbnail,totalit,information)
		xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
	else:
		sys.exit(0)
		
def list_episodes(name,url,plot):
	program_name = name.split('|')
	if len(program_name) > 1: titulo = program_name[1].replace('[/COLOR]','').replace('[/B]','')
	else: titulo = name
	prog_id=re.compile('http://www.rtp.pt/play/p(.+?)/').findall(url)
	if not prog_id: prog_id=re.compile('listProgram=(\d+)&').findall(url)
	page_num = re.compile('&page=(\d+)&').findall(url)
	if not page_num: current_page = '1'
	else: current_page = page_num[0]
	if ('recent' not in url) and ('popular' not in url) and ('procura?' not in url):
		url='http://www.rtp.pt/play/bg_l_ep/?listDate=&listQuery=&listProgram='+prog_id[0]+'&listcategory=&listchannel=&listtype=recent&page='+current_page+'&type=all'
	else:pass
	try:
		source = abrir_url(url)
	except: 
		source=''
		msgok(translate(30001),translate(30018))
	if source:
		match_geral = re.findall('<div class="lazy(.*?)</i></span>',source,re.DOTALL)
		if match_geral:
			totalit = len(match_geral)
			for match in match_geral:
				data = re.compile('<span class="small clearfix text-light">(.+?)</span>').findall(match)
				lnk = re.compile('href="(.+?)" ').findall(match)
				titulo_array = re.compile('title="(.+?)" ').findall(match)
				if titulo_array: 
					if 'itemprop' not in titulo_array[0]:
						titulo = title_clean_up(titulo_array[0])
				img = ''
				img_tmp = re.compile('itemprop="thumbnail" src="(.+?)" alt').findall(match)
				if img_tmp:
					img_tmp = re.compile("src=(.+?)&").findall(img_tmp[0])
					if img_tmp:
						img = img_base_url + img_tmp[0]
				if data and lnk:
					information = { "Title": titulo,"plot":plot,"aired":format_data(data[0]) }
					addepisode('[B]' + titulo + '[COLOR blue] (' + title_clean_up(data[0]) +')' + '[/B][/COLOR]',base_url + lnk[0],17,img,totalit,information)
		try:
			next_url = 'http://www.rtp.pt/play/bg_l_ep/?listDate=&listQuery=&listProgram='+prog_id[0]+'&listcategory=&listchannel=&listtype=recent&page='+str(int(current_page)+1)+'&type=all'
			try: source_next = abrir_url(next_url)
			except: source_next = ''
			if source_next:
				if re.findall('itemtype="http://schema.org/VideoObject"',source_next):
					addDir('[B][COLOR blue]'+translate(30028)+'|[/B][/COLOR] '+titulo,next_url,16,os.path.join(artfolder,'next.png'),1,pasta=True,information=information)
		except: pass
	xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
	
def list_emissoes(urltmp):
	try:
		page_source = abrir_url(urltmp)
	except:
		page_source = ''	
		msgok(translate(30001),translate(30018))
	if page_source:
		program_list=re.findall('<section>(.+?)</section>',page_source,re.DOTALL)
		if program_list:
			match = re.findall('href="(.+?)".*?itemprop="name">(.+?)</b',program_list[1],re.DOTALL)
			if match:
				totalit = len(match)
				for urlsbase,titulo in match:
					if selfAddon.getSetting('icon_plot') == 'true':
						try:
							source = abrir_url(base_url + urlsbase)
							sinopse=re.findall('id="promo">.+?\n.+?<p>(.*?)</p>', source, re.DOTALL)
							if sinopse: plot = clean_html(title_clean_up(sinopse[0]))
							information={ "Title": title_clean_up(titulo),"plot":plot }
							try: thumbnail = re.compile('itemprop="thumbnail" src="(.+?)\?.+?"').findall(source)[0]
							except: thumbnail=''
						except: information={ "Title": title_clean_up(titulo),"plot":translate(30026) };thumbnail=''
					else: information={ "Title": title_clean_up(titulo),"plot":translate(30026) };thumbnail=''
					addepisode(title_clean_up(titulo),base_url + urlsbase,17,thumbnail,totalit,information)
				xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
		else: msgok(translate(30001),translate(30032));sys.exit(0)
		
def pesquisa_emissoes():
	if not xbmcvfs.exists(os.path.join(datapath,'searchemiss.txt')):
		keyb = xbmc.Keyboard('', translate(30031))
		keyb.doModal()
		if (keyb.isConfirmed()):
			search = keyb.getText()
			encode=urllib.quote(search)
			urltmp = base_url + '/play/pesquisa?c_t=&q=' + encode
			save(os.path.join(datapath,'searchemiss.txt'),urltmp)
			list_emissoes(urltmp)
	else:
		text = readfile(os.path.join(datapath,'searchemiss.txt'))
		list_emissoes(text)
		
def pesquisa_programas():
	if not xbmcvfs.exists(os.path.join(datapath,'searchprog.txt')):
		keyb = xbmc.Keyboard('', translate(30031))
		keyb.doModal()
		if (keyb.isConfirmed()):
			search = keyb.getText()
			encode=urllib.quote(search)
			urltmp = base_url + '/play/pesquisa?c_t=&q=' + encode
			save(os.path.join(datapath,'searchprog.txt'),urltmp)
			list_show_search(urltmp)
	else:
		text = readfile(os.path.join(datapath,'searchprog.txt'))
		list_show_search(text)
		
def list_show_search(url):
	try:
		page_source = abrir_url(url)
	except:
		page_source = ''	
		msgok(translate(30001),translate(30018))
	if page_source:
		program_list=re.findall('<section>(.+?)</section>',page_source,re.DOTALL)
		if program_list:
			match = re.findall('href="(.+?)".*?itemprop="name">(.+?)</b',program_list[0],re.DOTALL)
			if match:
				totalit = len(match)
				for urlsbase,titulo in match:
					if selfAddon.getSetting('icon_plot') == 'true':
						try:
							source = abrir_url(base_url + urlsbase)
							sinopse=re.findall('id="promo">.+?\n.+?<p>(.*?)</p>', source, re.DOTALL)
							if sinopse: plot = clean_html(title_clean_up(sinopse[0]))
							information={ "Title": title_clean_up(titulo),"plot":plot }
							try: thumbnail = re.compile('<link itemprop="thumbnail" href="(.+?)\?.+?">').findall(source)[0]
							except: thumbnail=''
						except: information={ "Title": title_clean_up(titulo),"plot":translate(30026) };thumbnail=''
					else: information={ "Title": title_clean_up(titulo),"plot":translate(30026) };thumbnail=''
					addprograma(title_clean_up(titulo),base_url + urlsbase,16,thumbnail,totalit,information)
				xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
		else: msgok(translate(30001),translate(30032));sys.exit(0)
		
def get_show_episode_parts(name,url,iconimage):
	try:
		source = abrir_url(url)
	except: source = ''
	if source:
		url_video_list = []
		video_list = []
		match = re.compile('href="(.+?)" title="Parte.+?" rel="nofollow"').findall(source)
		if not match: url_video_list.append(url)
		else:
			for urlsbase in match:
				url_video_list.append(base_url + urlsbase)			
		number_of_parts = len(url_video_list)
		dp = xbmcgui.DialogProgress()
		dp.create(translate(30001),translate(30033))
		dp.update(0)
		i=0
		for part in url_video_list:
			if dp.iscanceled(): dp.close()
			i += 1
			video_url = rtp_resolver(part)
			if video_url: video_list.append(video_url)
			else:pass
			dp.update(int((float(i)/number_of_parts)*100), translate(30033))
		try:
			dp.update(100, translate(30033))
			dp.close()
		except: pass
		playlist = xbmc.PlayList(1)
		playlist.clear()
		for video in video_list:
			liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
			liz.setInfo('Video', {})
			liz.setProperty('mimetype', 'video')
			playlist.add(video, liz)

		player = RTPPlayer(videoarray=video_list,mainurl=url)
		player.play(playlist)
		while player._playbackLock:
			player._trackPosition()
			xbmc.sleep(1000)
	else:msgok(translate(30001),translate(30018));sys.exit(0)
