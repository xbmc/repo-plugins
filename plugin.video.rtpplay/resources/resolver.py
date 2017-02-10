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
			match = re.compile('"hls_url": "(.+?)"').findall(source)
			if match:
				return match[0]
			else:
				match = re.compile('file: "(.+?)",').findall(source)
				if match:
					if "http" not in match[0]: return "http:"+match[0]
					return match[0]
				else:
					return ''
		except: return ''
	else:
		msgok(translate(30001),translate(30018))
		sys.exit(0)
