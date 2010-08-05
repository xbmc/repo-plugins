"""
TheTVDB Scraper

--maruchan
"""

import sys
import os
import urllib
import urllib2
import StringIO
import gzip
from elementtree import ElementTree as ET
import xbmc
import re

__settings__ = sys.modules[ "__main__" ].__settings__

BASE_URL = "http://thetvdb.com/banners/"

class _Info:
	def __init__(self, *args, **kwargs):
		self.__dict__.update(kwargs)
		
class _tvdbParser:
	def __init__(self):
		self.info = _Info()

	def _grab_xml( self, show_id ):
		usock = urllib.urlopen('http://www.thetvdb.com/data/series/'+show_id+'/')
		xml = usock.read()
		usock.close
		doc = ET.fromstring(xml)
		root = doc.find('.//Series')
		item = {}

		for child in root:
			item[child.tag] = child.text

		# Series Name
		self.info.title = ''
		if item['SeriesName']:
			self.info.title = unicode(item['SeriesName']).encode('utf-8')

		# Rating	
		self.info.user_rating = 0.0
		if item['Rating']:
			self.info.user_rating = float(item['Rating'])

		# Plot
		self.info.plot = ''
		if item['Overview']:
			self.info.plot = unicode(item['Overview']).encode('utf-8')

		# Poster
		self.info.poster = ''
		if item['poster']:
			self.info.poster = BASE_URL + item['poster']
		elif item['banner'] and not item['poster']:
			self.info.poster = BASE_URL + item['banner']
		
		# Duration
		self.info.duration = ''
		if item['Runtime']:
			self.info.duration = item['Runtime']
			
		# Fanart
		self.info.fanart = ''
		if item['fanart']:
			self.info.fanart = BASE_URL + item['fanart']
			
		# Genre
		self.info.genre = ''
		if item['Genre']:
			genre_match = re.search(r'[\|](.*)[\|]', item['Genre'])
			if (genre_match):
				genre_temp = genre_match.group(1).split("|")
				self.info.genre = ", ".join(genre_temp)
		
		# Year
		self.info.year = 0
		if item['FirstAired']:
			year_temp = item['FirstAired'].split("-")
			self.info.year = int(year_temp[0])
			print "Release Year: "+year_temp[0]
			
		#self.info.cast = []
			
class tvdbFetcher:
    def __init__( self ):
        # create the cache folder if it does not exist
        self.base_cache_path = self._create_base_cache_path()
        self._get_settings()

    def _get_settings( self ):
        self.settings = {}
        self.settings[ "tvdb_info_fetch" ] = __settings__.getSetting( "tvdb_info_fetch" ) == "true"
        self.settings[ "tvdb_poster_fetch" ] = __settings__.getSetting( "tvdb_poster_fetch" ) == "true"
        self.settings[ "tvdb_fanart_fetch" ] = __settings__.getSetting( "tvdb_fanart_fetch" ) == "true"

    def _create_base_cache_path( self ):
        """ creates the base cache folder """
        # split our path into folders, we replace / with \ for compatability
        base_cache_path = os.getcwd().replace( ";", "" )
        base_cache_path = os.path.join(base_cache_path, 'cache')
        return base_cache_path

    def fetch_info( self, title, fetch_poster=True ):
	    try:
			opener = urllib2.build_opener()
			opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.2.4) Gecko/20100527 Firefox/3.6.4'),("Accept-encoding", "gzip")]
			request = urllib.quote(title)
			usock = opener.open('http://www.thetvdb.com/api/GetSeries.php?seriesname='+request)
			xml = usock.read()
			if usock.headers.get('content-encoding', None) == 'gzip':
				xml = gzip.GzipFile(fileobj=StringIO.StringIO(xml)).read()
			usock.close
			doc = ET.fromstring(xml)
			id = doc.findtext('.//seriesid', default=None)
			self.parser = _tvdbParser()
			if id:
				# Parse source code for information
				file_path = self._get_cache_name(id)
				self.parser._grab_xml(id)
				self.parser.info.poster_url = self.parser.info.poster
				if self.settings['tvdb_poster_fetch']:
					self._fetch_poster(self.parser.info.poster, file_path)
				else:
					self.parser.info.poster = ''
				if self.settings['tvdb_fanart_fetch'] and self.parser.info.fanart != "":
					self._fetch_fanart(self.parser.info.fanart, file_path)
				else:
					self.parser.info.fanart = ''
				print 'I\'m returning info.poster_url as: %s' % self.parser.info.poster
				return self.parser.info
			else:
				#print 'Couldn\'t find TV show named '+title
				return None
				
	    except:
            # oops print error message
			print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
			return None

    def _fetch_poster( self, url, file_path ):
        # create the cache filename
        file_path += ".jpg"
        try:
            if ( url ):
                # Retrieve poster if it's not cached
                #if ( not os.path.exists( file_path ) and url != "" ):
                #    urllib.urlretrieve( url, file_path )
                self.parser.info.poster = url
        except:
            urllib.urlcleanup()
            remove_tries = 3
            while remove_tries and os.path.isfile( file_path ):
                try:
                    os.remove( file_path )
                except:
                    remove_tries -= 1
                    xbmc.sleep( 1000 )

    def _fetch_fanart( self, url, file_path ):
        # create the cache filename
        file_path += "_fanart.jpg"
        try:
            if ( url ):
                # Retrieve poster if it's not cached
                #if ( not os.path.exists( file_path ) and url != "" ):
                #    urllib.urlretrieve( url, file_path )
                self.parser.info.fanart = url
        except:
            urllib.urlcleanup()
            remove_tries = 3
            while remove_tries and os.path.isfile( file_path ):
                try:
                    os.remove( file_path )
                except:
                    remove_tries -= 1
                    xbmc.sleep( 1000 )

    def _get_cache_name( self, url ):
        # get the imdb title code
        title = url
        print 'cache title is '+title
        # append imdb title code to cache path
        file_path = os.path.join( self.base_cache_path, title )
        # return our complete file path
        if ( __name__ != "__main__" ):
            return xbmc.translatePath( file_path )
        else:
            return file_path

if ( __name__ == "__main__" ):
	series = "Breaking Bad"
	
	info = tvdbFetcher().fetch_info(series)
	if info:
		print info.plot
		print "---------------\n"
