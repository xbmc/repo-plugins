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

import sys, os, time, urllib, urllib2, codecs, xml.dom.minidom
import md5
import xbmc, xbmcplugin, xbmcgui

__settings__ = sys.modules[ "__main__" ].__settings__

__mc_url = 'https://www.furk.net/mc/'

def searchDirs(query):
	recent = __settings__.getSetting('recent_queries').split('|')
	recent = [ urllib.unquote(r) for r in recent ]
	if query in recent:
		recent.remove(query)
	recent.insert(0, query)
	recent = [ urllib.quote(r) for r in recent ]
	__settings__.setSetting(id='recent_queries', value='|'.join(recent))

	xbmc.log('recent=%s' % recent)
	
	list_xml = fetch('search', { 'q': urllib.quote(query), 'filter': 'instant', 'sort': 'relevance' })
	dirs = list_xml.getElementsByTagName('dir')

	return(dirs)

def getDirs():
	list_xml = fetch('dirs', {})
	dirs = list_xml.getElementsByTagName('dir')

	return(dirs)

def getFiles(did):
	list_xml = fetch('files', { 'did': did })
	files = list_xml.getElementsByTagName('file')

	return(files)



def fetch(action, params):
	params['login'] =  urllib.quote(__settings__.getSetting("login"))
	params['password'] = md5.new(__settings__.getSetting("password")).hexdigest()
	
	query_string = '&'.join([k+'='+v for (k,v) in params.items()])
	url = __mc_url + action + '?' + query_string

	xbmc.log('params=%s; url=%s' % (params, url))	

	req = urllib2.Request(url)
	req.add_header('User-Agent', "%s %s" % (sys.modules[ "__main__" ].__plugin__, sys.modules[ "__main__" ].__version__))

	try:
		response = urllib2.urlopen(req)
	except urllib2.HTTPError, e:
		xbmcgui.Dialog().ok('Error', 'Error: %s' % e.read())
		raise
	except urllib2.URLError, e:
		xbmcgui.Dialog().ok('Error', 'Error: %s' % e.reason)
		raise
		
	page = response.read()
	response.close()
	#xbmc.log('page=%s' % page)

	resp_xml = xml.dom.minidom.parseString(page)

	msg = resp_xml.getElementsByTagName("message").item(0)
	if msg:
		xbmc.log('msg=%s' % msg.firstChild.data)
		xbmcgui.Dialog().ok("Message from server", "%s" % msg.firstChild.data)

	return resp_xml;


