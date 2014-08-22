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
		match=re.compile('href="(.+?)" title=".+?"><h3>(.+?)</h3>').findall(page_source)
		totalit= len(match)
		for urlsbase,titulo in match:
			titulo = title_clean_up(titulo)
			if selfAddon.getSetting('icon_plot') == 'true':
				try:
					html_source = abrir_url(base_url + urlsbase)
				except: html_source = ''
				if html_source:
					try: thumbnail=img_base_url + re.compile('src=(.+?)&amp').findall(html_source)[0]
					except: thumbnail=''
					sinopse=re.compile('<p class="Sinopse">(.+?)</span></p>').findall(html_source)
					if sinopse: information = { "Title": name,"plot": clean_html(title_clean_up(sinopse[0])) }
					else: information = { "Title": name,"plot":translate(30026) }
				addprograma(titulo,base_url + urlsbase,16,thumbnail,totalit,information)
			else:
				information = { "Title": name,"plot":translate(30026) }
				thumbnail = ''
				addprograma(titulo,base_url + urlsbase,15,thumbnail,totalit,information)
		xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
		setview('show-view')
	else:
		sys.exit(0)
		
def list_episodes(url,plot):
	prog_id=re.compile('http://www.rtp.pt/play/p(.+?)/').findall(url)
	if not prog_id: prog_id=re.compile('http://www.rtp.pt/play/browseprog/(.+?)/.+?/true').findall(url)
	page_num = re.compile('.+?/(\d+)/true').findall(url)
	if not page_num: current_page = '1'
	else: current_page = page_num[0]
	if ('recent.php' not in url) and ('type=popular' not in url) and ('procura?' not in url): url='http://www.rtp.pt/play/browseprog/' + prog_id[0] + '/' + current_page + '/true'
	else: pass
	try:
		source = abrir_url(url)
	except: source=''; msgok(translate(30001),translate(30018))
	if source:
		match=re.compile('href="(.+?)"><img alt="(.+?)" src="(.+?)".+?<i class="date"><b>(.+?)</b>').findall(source)
		totalit = len(match)
		for urlsbase,titulo,thumbtmp,data in match:
			try:thumbnail=img_base_url + re.compile('src=(.+?)&amp').findall(thumbtmp)[0]
			except: thumbnail=''
			if not plot: plot = translate(30026)
			information = { "Title": title_clean_up(titulo),"plot":plot,"aired":format_data(data) }
			addepisode('[B]' + title_clean_up(titulo) + '[COLOR blue] (' + data +')' + '[/B][/COLOR]',base_url + urlsbase,17,thumbnail,totalit,information)
		pag_num_total=re.compile('.*page:(.+?)}\)\">Fim &raquo').findall(source)
		if pag_num_total:
			try:
				if int(current_page) == int(pag_num_total[0]): pass
				else: 
					url_next='http://www.rtp.pt/play/browseprog/' + prog_id[0] + '/' + str(int(current_page)+1) + '/true'
					addDir('[B][COLOR blue]'+translate(30027)+' ('+current_page+'/'+pag_num_total[0]+')[/B][/COLOR] | ' + translate(30028),url_next,16,os.path.join(artfolder,'next.png'),1,pasta=True)
			except: pass
	xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
	setview('episodes-view')
	
def list_emissoes(urltmp):
	#Block of code to detect current page number
	page_num = re.compile('&page=(\d+)').findall(urltmp)
	if not page_num: page_num = str(1)
	else: page_num=page_num[0]
	url= urltmp + '&page=' + page_num
	try:
		page_source = abrir_url(url)
	except:
		page_source = ''	
		msgok(translate(30001),translate(30018))
	if page_source:
		pag_num_total=re.compile('.*page=(.+?)">Fim &raquo').findall(page_source)
		html_source_trunk = re.findall('<div class="item">(.*?)<p class=', page_source, re.DOTALL)
		if html_source_trunk:
			for trunk in html_source_trunk:
				match=re.compile('<a href="(.+?)" title="(.+?), Ep.+? de (.+?)">\s*<img alt=".+?" src="(.+?)"').findall(trunk)
				totalit = len(match)
 				for urlsbase,titulo,data,thumbtmp in match:
 					try:
						thumbtmp2=re.compile('src=(.+?)&amp').findall(thumbtmp)
						thumbnail=img_base_url + thumbtmp2[0]
						titulo = title_clean_up(titulo)
						plot = re.compile('<p>(.+?)</p').findall(trunk)
						if plot: plot = title_clean_up(plot[0])
						else: plot = translate(30026)
						data = format_data(data)
						information = { "Title": titulo,"Plot":plot,"aired":data }
						addepisode('[B]' + titulo + '[COLOR blue] (' + data +')' + '[/B][/COLOR]',base_url + urlsbase,17,thumbnail,totalit,information)
					except: pass
			if pag_num_total:
				page_next = int(page_num)+1
				match = re.compile('&page=(\d+)').findall(urltmp)
				if match: urltmp = urltmp.replace('&page='+match[0],'')
				url=urltmp + '&page=' + str(page_next)
				addDir('[B]'+translate(30027)+ page_num + '/' + pag_num_total[0] + '[/B][B][COLOR blue] | '+translate(30029)+'[/B][/COLOR]',url,14,os.path.join(artfolder,'next.png'),1)
			else: pass
			xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
			setview('episodes-view')
		else: msgok(translate(30001),translate(30030));sys.exit(0)
	else:
		sys.exit(0)
		
def pesquisa_emissoes():
	if not xbmcvfs.exists(os.path.join(datapath,'searchemiss.txt')):
		keyb = xbmc.Keyboard('', translate(30031))
		keyb.doModal()
		if (keyb.isConfirmed()):
			search = keyb.getText()
			encode=urllib.quote(search)
			urltmp = base_url + '/play/procura?p_az=&p_c=&p_t=&p_d=&p_n=' + encode + '&pesquisar=OK'
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
			urltmp = base_url + '/play/procura?p_az=&p_c=&p_t=&p_d=&p_n=' + encode + '&pesquisar=OK'
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
		match = re.compile('<a href="(.+?)" title=".+?"><h3>(.+?)</h3>').findall(page_source)
		if match:
			totalit = len(match)
			for urlsbase,titulo in match:
				if selfAddon.getSetting('icon_plot') == 'true':
					try:
						source = abrir_url(base_url + urlsbase)
						sinopse=re.compile('<p class="Sinopse">(.+?)</span></p>').findall(source)
						if sinopse: plot = clean_html(title_clean_up(sinopse[0]))
						information={ "Title": title_clean_up(titulo),"plot":plot }
						try: thumbnail=img_base_url + re.compile('src=(.+?)&amp').findall(source)[0]
						except: thumbnail=''
					except: information={ "Title": title_clean_up(titulo),"plot":translate(30026) };thumbnail=''
				else: information={ "Title": title_clean_up(titulo),"plot":translate(30026) };thumbnail=''
				addprograma(title_clean_up(titulo),base_url + urlsbase,16,thumbnail,totalit,information)
			xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
			setview('show-view')
		else: msgok(translate(30001),translate(30032));sys.exit(0)
		
def get_show_episode_parts(name,url,iconimage):
	try:
		source = abrir_url(url)
	except: source = ''
	if source:
		url_video_list = []
		video_list = []
		
		match = re.compile("<a.+?href='(.+?)'><b>Parte</b>(.+?)</a>").findall(source)
		if not match: url_video_list.append(url)
		else:
			for urlsbase,parte in match:
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

		xbmcPlayer = xbmc.Player()
		xbmcPlayer.play(playlist)
		player = RTPPlayer(videoarray=video_list,mainurl=url)
		player.play(playlist)
		while player._playbackLock:
			player._trackPosition()
			xbmc.sleep(1000)
	else:msgok(translate(30001),translate(30018));sys.exit(0)
