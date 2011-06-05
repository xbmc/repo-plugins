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

import sys, urllib
import xbmc, xbmcaddon, xbmcgui

# Plugin constants
__plugin__ = 'Furk.net'
__author__ = 'Gpun Yog'
__url__ = 'http://www.furk.net/t/xbmc'
__version__ = '1.0.6'
__settings__ = xbmcaddon.Addon(id='plugin.video.furk')

print "[PLUGIN] '%s: version %s' initialized!" % (__plugin__, __version__)

def parse_qs(u):
	params = '?' in u and dict(p.split('=') for p in u[u.index('?') + 1:].split('&')) or {}
	
	return params;

if __name__ == "__main__":
	from resources.lib import getter, printer

	
	xbmc.log('params_str=%s' % sys.argv[2])	
	params = parse_qs(sys.argv[2])
	if not params:
		params['action'] = 'dirs'
	xbmc.log('_params=%s' % params)	

	if __settings__.getSetting('login') == '' or __settings__.getSetting('password') == '':
		resp = xbmcgui.Dialog().yesno("No username/password set!","Furk.net requires you to be logged in to view", \
			"videos.  Would you like to log-in now?")
		if resp:
			__settings__.openSettings()

	elif(params['action'] == 'files'):
		# Enter a directory | open torrent and list files
		files = getter.getFiles(params['did'])
		printer.printFiles(files)

	elif(params['action'] == 'play'):
		# Play a file
		printer.playFile(params['url'])

	elif(params['action'] == 'recent_queries'):
		# Show previous searches
		printer.printRecentQueries()

	elif(params['action'] == 'search_test'):
		# Search
		dirs = getter.searchDirs('xxx')
		printer.printDirs(dirs)

	elif(params['action'] == 'search'):
		# Search
		keyboard = xbmc.Keyboard(urllib.unquote(params['query']), 'Search')
		keyboard.doModal()
        
		if keyboard.isConfirmed():
			query = keyboard.getText()
			dirs = getter.searchDirs(query)
			printer.printDirs(dirs)

	else:
		# torrents a root Directories 
		xbmc.log('argv=%s' % sys.argv)
		dirs = getter.getDirs()
		printer.printDirs(dirs)

sys.modules.clear()
