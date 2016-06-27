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

import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmc,xbmcaddon,xbmcvfs
import os,sys
from resources.common_variables import *
from resources.utilities import *
from resources.directory import *
from resources.webutils import *
from resources.ondemand import *
from resources.live import *
from resources.arquivo import *
from resources.resolver import *
from resources.favourites import *

if not os.path.isdir(datapath):
	os.makedirs(datapath)

def main_menu():
	addDir('[COLOR blue][B]'+ translate(30002) +'[/B][/COLOR]','http://www.rtp.pt/play/direto',1,os.path.join(artfolder,'tvradio_icon.png'),1)
	addDir('[COLOR blue][B]'+translate(30004)+'[/B][/COLOR]','rtp.pt/play',24, os.path.join(artfolder,'broadcast.png'),1)
	addDir('[COLOR blue][B]'+translate(30009)+'[/B][/COLOR]','rtp.pt/play',25, os.path.join(artfolder,'tvshow.png'),1)
	addDir('[COLOR blue][B]'+translate(30012)+'[/B][/COLOR]','http://www.rtp.pt/arquivo/colecoes',9, os.path.join(artfolder,'archive.png'),1)

def boadcasts_menu():
	addDir('[B]'+translate(30005)+'[/B]','http://www.rtp.pt/play/ondemand',2, os.path.join(artfolder,'maisrecentes.png'),1)
	addDir('[B]'+translate(30006)+'[/B]','http://www.rtp.pt/play/bg_l_pg/?listDate=&listQuery=&listProgram=&listcategory=&listchannel=&listtype=popular&page=1&type=all',3,os.path.join(artfolder,'maispopulares.png'),11)
	addDir('[B]'+translate(30008)+'[/B]','http://www.rtp.pt/play/ondemand',5,os.path.join(artfolder,'pesquisa.png'),1)

def shows_menu():
	addDir('[B]'+translate(30010)+'[/B]','http://www.rtp.pt/play/ondemand',6,os.path.join(artfolder,'favourite.png'),1)
	addDir('[B]'+translate(30011)+'[/B]','http://www.rtp.pt/play/ondemand',7,os.path.join(artfolder,'az.png'),1)
	addDir('[B]'+translate(30008)+'[/B]','rtpplay',8,os.path.join(artfolder,'pesquisa.png'),1)

def radio_tv_menu(name):
	if ('R' in name) or ('r' in name):
		mode = 3
	elif 'A-Z' in name:
		mode = 13
	addDir('[B]'+translate(30014)+'[/B]','http://www.rtp.pt/play/bg_l_pg/?listDate=&listQuery=&listProgram=&listcategory=&listchannel=&listtype=recent&page=1&type=tv',mode,os.path.join(artfolder,'tv.png'),2)
	addDir('[B]'+translate(30015)+'[/B]','http://www.rtp.pt/play/bg_l_pg/?listDate=&listQuery=&listProgram=&listcategory=&listchannel=&listtype=recent&page=1&type=radio',mode, os.path.join(artfolder,'radio.png'),2)
	
def az_menu(name):
	alphabet = ['0-9','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
	if 'tv' in title_clean_up(name.lower()):
		tipo = 'tv'
	elif 'dio' in title_clean_up(name.lower()):
		tipo = 'radio'
	else: sys.exit(0)
	for letter in alphabet:
		addDir('[B]'+ letter +'[/B]','http://www.rtp.pt/play/programas/'+tipo+'/'+letter,15,os.path.join(artfolder,'az.png'),len(alphabet))
		
def emissao_lista(name,url):
	try:
		page_source = abrir_url(url)
	except:
		page_source = ''
		msgok(translate(30001),translate(30018))
	if page_source:
		if 'c' in url:
			regex = '<a href="/play/procura\?p_c=(.+?)" title=".+?">(.+?)</a>'
			link_part = '/play/procura?p_c='
		elif 't' in url:
			regex = '<a href="/play/procura\?p_t=(.+?)" title=".+?">(.+?)</a>'
			link_part = '/play/procura?p_t='
		match=re.compile(regex).findall(page_source)
		for canal,titulo in match:
			titulo = title_clean_up(titulo)
			addDir('[B]' + titulo + '[/B]',base_url + link_part + canal,14,os.path.join(artfolder,'tree.png'),len(match))
	else:
		sys.exit(0)
		

"""

Addon navigation is below
 
"""	
			
            
def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param


params=get_params()
url=None
name=None
mode=None
iconimage=None
plot=None

try: url=urllib.unquote_plus(params["url"])
except: pass
try: name=urllib.unquote_plus(params["name"])
except: pass
try: mode=int(params["mode"])
except:
	try: 
		mode=params["mode"]
	except: pass
try: iconimage=urllib.unquote_plus(params["iconimage"])
except: pass
try: plot=urllib.unquote_plus(params["plot"])
except: pass

print ("Mode: "+str(mode))
print ("URL: "+str(url))
print ("Name: "+str(name))
print ("iconimage: "+str(iconimage))


if mode==None: main_menu()
elif mode==1: radiotv_channels(url)
elif mode==2: radio_tv_menu(name)
elif mode==3: list_episodes(name,url,plot)
elif mode==5: pesquisa_emissoes()
elif mode==6: list_favourites()
elif mode==7: radio_tv_menu(name)
elif mode==8: pesquisa_programas()
elif mode==9: arquivo_coleccoes(url)
elif mode==10: listar_programas_arquivo(url)
elif mode==11: listar_episodios_arquivo(url)
elif mode==12: emissao_lista(name,url)
elif mode==13: az_menu(name)
elif mode==14: list_emissoes(url)
elif mode==15: list_tv_shows(name,url)
elif mode==16: list_episodes(name,url,plot)
elif mode==17: get_show_episode_parts(name,url,iconimage)
elif mode==19: add_favourite(name,url,iconimage,plot)
elif mode==20: remove_favourite(name)
elif mode==21: mark_as_watched(url)
elif mode==22: remove_watched_mark(url)
elif mode==23: play_live(url,name,iconimage)
elif mode==24: boadcasts_menu()
elif mode==25: shows_menu()
elif mode == "resolve_and_play": play_from_outside(name)

if (mode != 12) and (mode != 8) and (mode !=5) and (mode !=19) and (mode !=20) and (mode !=21) and (mode !=22) and (mode != "resolve_and_play"):
	try:	xbmcvfs.delete(os.path.join(datapath,'searchprog.txt'))
	except: pass
	try: xbmcvfs.delete(os.path.join(datapath,'searchemiss.txt'))	
	except: pass
	


xbmcplugin.endOfDirectory(int(sys.argv[1]))
