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
from utilities import *

url_arquivo = 'http://www.rtp.pt/arquivo/colecoes'
url_base = 'http://www.rtp.pt/'

def arquivo_coleccoes(url):
	try: source=abrir_url(url)
	except: source=''; msgok(translate(30001),translate(30018))
	if source:
		match = re.compile('<div class=".+?"><h2><a href="(.+?)" title="(.+?)">').findall(source)
		totalit = len(match)
		for urlsbase,titulo in match:
			addDir(title_clean_up(titulo),(url_arquivo + urlsbase).replace('&amp;','&'),10,os.path.join(artfolder,'arquivo.png'),totalit,pasta=True)
			
def listar_programas_arquivo(url):
	try: source=abrir_url(url)
	except: source=''; msgok(translate(30001),translate(30018))
	if source:
		match = re.compile('href="(.+?)" title="(.+?)".+?itemprop="image" src="(.+?)".+?<p itemprop=\'description\'>(.+?)</p>').findall(source)
		totalit=len(match)
		for urlsbase,titulo,thumbnail,descricao in match:
			thumbnail = re.findall('(.+?)&amp',thumbnail)
			if thumbnail: thumbnail = thumbnail[0]
			else: thumbnail = ''
			titulo = title_clean_up(titulo)
			information = { "Title": titulo,"plot":title_clean_up(descricao) }
			addprograma(titulo,(url_base + urlsbase).replace('&amp;','&'),11,thumbnail,totalit,information)
		xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
		
def listar_episodios_arquivo(url):
	try: source=abrir_url(url)
	except: source=''; msgok(translate(30001),translate(30018))
	if source:
		html_source_trunk = re.findall('<div class="El(.*?)</div>', source, re.DOTALL)
		for trunk in html_source_trunk:
			match = re.compile('href="(.+?)" title="(.+?)" itemprop="url">.+?src="(.+?)"').findall(trunk)
			totalit = len(match)
			if match:
				try:
					ano = re.compile('Ano (\d+)').findall(trunk)
					if ano: ano = ano[0]
					else: ano='n/a'
					sinopse = re.findall('<p>(.*?)</p>', trunk, re.DOTALL)
					information = { "Title": title_clean_up(match[0][1]),"Year":ano,"Aired":(ano+"-01-01"),"Plot":title_clean_up(sinopse[1]) }
					addepisode(title_clean_up(match[0][1]),title_clean_up(match[0][0]).replace('&amp;','&'),17,match[0][2].replace('&amp;','&').replace(';',''),totalit,information)
				except: pass
		xbmcplugin.setContent(int(sys.argv[1]), 'episodes')

