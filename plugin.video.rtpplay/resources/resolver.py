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
from utilities import *

def rtp_resolver(url):
	try:
		source = abrir_url(url)
	except: source = ''
	if source:
		try:
			if re.search('mms:', source):
				match=re.compile('\"file\": \"(.+?)\",\"streamer\": \"(.+?)\"').findall(source)
				return match[0][1] + match[0][0]
			elif re.search('.mp3',source):
				match=re.compile('"file": "(.+?)","application": "(.+?)","streamer": "(.+?)"').findall(source)
				if match: return 'rtmp://' + match[0][2] +'/' + match[0][1] + ' playpath=mp3:' + match[0][0]
				else:
					match = re.compile("streamer:'(.+?)',application:'(.+?)',file:'(.+?)'").findall(source)
					return 'rtmp://' + match[0][0] +'/' + match[0][1] + ' playpath=mp3:' + match[0][2]
			elif re.search('.flv', source):
				match=re.compile('"file": "(.+?)","image": "(.+?)","application": "(.+?)","streamer": "(.+?)"').findall(source)
				return 'rtmp://' + match[0][3] +'/' + match[0][2] + ' playpath=flv:' + match[0][0]
			elif re.search('.mp4', source):
				match=re.compile('"file": "(.+?)","image": "(.+?)","application": "(.+?)","streamer": "(.+?)"').findall(source)
				if match: return 'rtmp://' + match[0][3] +'/' + match[0][2] + ' playpath=mp4:' + match[0][0]
				else:
					match = re.compile("streamer:'(.+?)',application:'(.+?)',file:'(.+?)'").findall(source)
					return 'rtmp://' + match[0][0] +'/' + match[0][1] + ' playpath=mp4:' + match[0][2]
			else: return ''
		except: return ''
	else:
		msgok(translate(30001),translate(30018))
		sys.exit(0)
