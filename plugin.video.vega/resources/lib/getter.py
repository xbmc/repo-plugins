'''
    VEGA concerts player for XBMC
    Copyright (C) 2010 Jeppe Toustrup

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

import os, time, urllib2, codecs, xml.dom.minidom
import xbmc, xbmcplugin


def getConcerts():
	__listurl__ = 'http://www.vega-tdc-player.dk/concerts.jsp'
	__listcache__ = xbmc.translatePath('special://temp/vega-list-cache.xml')

	if(fileOutdated(__listcache__)):
		xbmc.log('Concert listing cache is outdated or missing.', xbmc.LOGNOTICE)
		listRaw = download(__listurl__)
		cacheFile(__listcache__, listRaw) # TODO: If download fails, we should use the cache and not overwrite the file
	else:
		xbmc.log('Using cached concert listing.', xbmc.LOGNOTICE)
	
	listXml = xml.dom.minidom.parse(__listcache__)
	return(listXml.getElementsByTagName('concert'))


def getConcertInfo(concertid):
	__concerturl__ = 'http://www.vega-tdc-player.dk/concert.jsp?id=' + concertid
	__concertcache__ = xbmc.translatePath('special://temp/vega-concert-') + concertid + '-cache.xml'

	if(fileOutdated(__concertcache__)):
		xbmc.log('Concert informations are outdated or missing.', xbmc.LOGNOTICE)
		concertRaw = download(__concerturl__)
		cacheFile(__concertcache__, concertRaw)
	else:
		xbmc.log('Using cached concert informations.', xbmc.LOGNOTICE)
	
	concertXml = xml.dom.minidom.parse(__concertcache__)
	return({'info': concertXml.getElementsByTagName('concert').item(0), 'tracks': concertXml.getElementsByTagName('tracks')})


def download(url):
	# TODO: Make some error handling - http://www.voidspace.org.uk/python/articles/urllib2.shtml#wrapping-it-up
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	page = response.read()
	response.close()
	return(page.replace('<?xml version="1.0" encoding="iso-8859-1"?>', '<?xml version="1.0" encoding="utf-8"?>')) # The XML files are really served in UTF-8, even though their header says otherwise, we have to correct this for non unicode characters to work


def cacheFile(filepath, content):
	try:
		f = open(filepath, 'w')
		f.write(content)
		xbmc.log('Updated cache file at %s.' % filepath, xbmc.LOGNOTICE)
	except OSError:
		xbmc.log('Could not write cache file to %s.' % filepath, xbmc.LOGERROR)


def getCacheSeconds():
	import sys
	cache_time = xbmcplugin.getSetting(int(sys.argv[1]), 'cache_time')
	if(cache_time == '0'):
		# 12 hours
		return(43200)
	elif(cache_time == '1'):
		# 1 day
		return(86400)
	elif(cache_time == '2'):
		# 2 days
		return(172800)
	elif(cache_time == '3'):
		# 1 week
		return(604800)


def fileOutdated(filepath):
	try:
		mtime = os.path.getmtime(filepath)
		if(int(time.time()) - mtime < getCacheSeconds()):
			# File is not outdated
			return(False)
		else:
			# File is outdated
			return(True)
	except OSError:
		# File does not exist
		return(True)
