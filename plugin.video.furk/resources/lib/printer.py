'''
    Furk.net player for XBMC
    Copyright (C) 2010 Gpun Yog 

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
'''

import sys, re, time
import xbmc, xbmcgui, xbmcplugin
import urllib

__settings__ = sys.modules[ "__main__" ].__settings__

def printRecentQueries():
	# search

	recent = __settings__.getSetting('recent_queries').split('|')
	if '' in recent:
		recent.remove('')
	total = len(recent) + 1

	name = '@Search...'
	url = sys.argv[0] + '?action=search&query='
	listitem = xbmcgui.ListItem()
	listitem.setLabel(name)
	xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isFolder=True, totalItems=total)

	for r in recent:
		url = sys.argv[0] + '?action=search&query=' + r

		r = urllib.unquote(r)
		listitem = xbmcgui.ListItem()
		listitem.setLabel(r)
		xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isFolder=True, totalItems=total)


	xbmcplugin.endOfDirectory(int(sys.argv[1]))
	

def printDirs(dirs):
	xbmcplugin.setContent(int(sys.argv[1]), 'videos')
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
	
	total = len(dirs)

	# search
	total = total + 1
	name = '@Search'
	date = '1970-01-01'
	url = sys.argv[0] + '?action=recent_queries&query='
	listitem = xbmcgui.ListItem()
	listitem.setLabel(name)
	listitem.setLabel2(date)
	listitem.setThumbnailImage('http://www.furk.net/img/logo.png')
	listitem.setInfo('video', {'date': date, 'title': name})
	xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isFolder=True, totalItems=total)


	for d in dirs:
		id = d.getElementsByTagName('id').item(0).firstChild.data
		name = d.getElementsByTagName('name').item(0).firstChild.data
		date = d.getElementsByTagName('date').item(0).firstChild.data
		thumb = d.getElementsByTagName('thumb').item(0).firstChild.data

		url = sys.argv[0] + '?action=files&did=' + id
		
		listitem = xbmcgui.ListItem()
		listitem.setLabel(name)
		listitem.setLabel2(date)
		listitem.setThumbnailImage(thumb)
		listitem.setInfo('video', {'date': date, 'title': name})
		xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isFolder=True, totalItems=total)

	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def printFiles(files):
	xbmcplugin.setContent(int(sys.argv[1]), 'videos')
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
	
	total = len(files)
	for f in files:
		id = f.getElementsByTagName('id').item(0).firstChild.data
		name = f.getElementsByTagName('name').item(0).firstChild.data
		play_url = f.getElementsByTagName('url').item(0).firstChild.data

		url = sys.argv[0] + '?action=play&url=' + urllib.quote(play_url)
		
		listitem = xbmcgui.ListItem()
		listitem.setLabel(name)
		listitem.setInfo('video', {'title': name})
		xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isFolder=False, totalItems=total)
		#xbmc.log('f=%s' % name)	

	xbmcplugin.endOfDirectory(int(sys.argv[1]))



def playFile(play_url):
	xbmc.Player().play(urllib.unquote(play_url))
