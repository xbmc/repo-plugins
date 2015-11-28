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

import xbmc,xbmcvfs
from iofile import *
from common_variables import *

def mark_as_watched(url):
	if not os.path.exists(datapath): xbmcvfs.mkdir(datapath)
	if not os.path.exists(watched_folder): xbmcvfs.mkdir(watched_folder)
	if not os.path.exists(watched_database): save(watched_database,'{}')
	database_text = readfile(watched_database)
	database = eval(database_text)
	database[url]=True
	save(watched_database,str(database))
	xbmc.executebuiltin("Notification(%s,%s,%i,%s)" % (translate(30001), translate(30034), 1,os.path.join(addonfolder,"icon.png")))
	xbmc.executebuiltin("XBMC.Container.Refresh")
	
def remove_watched_mark(url):
	database_text = readfile(watched_database)
	database = eval(database_text)
	del database[url]
	save(watched_database,str(database))
	xbmc.executebuiltin("Notification(%s,%s,%i,%s)" % (translate(30001), translate(30035), 1,os.path.join(addonfolder,"icon.png")))
	xbmc.executebuiltin("XBMC.Container.Refresh")
