import xbmcplugin
import xbmcgui
import re
import sys
import feedparser
import simplejson
import time
import urllib

from caching import Caching
from item_list import __version__
from settings import *

__settings__ = sys.modules[ "__main__" ].__settings__

class RSSParser:
    def __init__(self):
        self.settings = {}
        self.settings[ "cache_time" ] = int(__settings__.getSetting( "cache_time" ))*60
        self.settings[ "cache_rss" ] = __settings__.getSetting( "cache_rss" ) == "true"
        self.settings['username_newzbin'] = __settings__.getSetting('username_newzbin')
        self.settings['password_newzbin'] = __settings__.getSetting('password_newzbin')
        self.settings[ "imdb_info_fetch" ] = __settings__.getSetting( "imdb_info_fetch" ) == "true"
        self.settings[ "imdb_poster_fetch" ] = __settings__.getSetting( "imdb_poster_fetch" ) == "true"
        self.settings[ "tvdb_info_fetch" ] = __settings__.getSetting( "tvdb_info_fetch" ) == "true"
        self.settings[ "tvdb_poster_fetch" ] = __settings__.getSetting( "tvdb_poster_fetch" ) == "true"
        self.settings[ "tvdb_fanart_fetch" ] = __settings__.getSetting( "tvdb_fanart_fetch" ) == "true"
      
    def _parse(self, uri, cat='default'):
        d = self._parse_rss(uri)
        if d:
            return self._get_items(d, uri, cat)
        else:
            return {}
        
    def _parse_rss( self, uri ):
        '''
        Use the feedparser module to parse the requested url. Cookies will be added for newzbin RSS feeds
        '''
        try:
            d = ''
            if self.settings['cache_rss']:
                Cache = Caching(uri, self.settings[ "cache_time" ])
                d = Cache._fetch()
            if not d:
                print 'sabnzbd-xbmc parsing: %s' % uri
                feedparser.USER_AGENT = "SABnzbdXBMCPlugin/%s +http://sabnzbd.org/" % __version__
                    
                print 'sabnzbd-xbmc parsing uri'
                d = feedparser.parse(uri)
                if not d or 'bozo_exception' in d:
                    print 'sabnzbd-xbmc failed to parse the feed:', uri
                    msg = 'Failed to parse the rss feed: %s' % uri
                    xbmcgui.Dialog().ok('SABnzbd-XBMC-Plugin', msg)
                    return {}
                if not d['entries']:
                    msg = 'Feed is empty'
                    xbmcgui.Dialog().ok('SABnzbd-XBMC-Plugin', msg)
                    return {}
                
                #cache the rss feed locally
                if self.settings['cache_rss']:
                    Cache._save(d)
                print 'sabnzbd-xbmc parsed feed'
                
            return d
                
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return {}
        
    def _get_items(self, d, uri, cat):
        ''' build up a list of the nzb names and their url's '''
        try:
            entries = d['entries'] 
            print 'sabnzbd-xbmc building up list'
            items = []
            size = 0
            for entry in entries:
                imdb = None
                tvdb = None
                link = self._get_link(uri, entry)

                if entry.description:

                    mbre = re.compile(r'([0-9]+\.[0-9]+ [A-z]+)', re.I)
                    mbmatch = re.search(mbre, entry.description.lower())
                    if mbmatch:
                        size = mbmatch.group(1)

                        if cat == 'movies' and (self.settings['imdb_info_fetch'] or self.settings['imdb_poster_fetch']):
                            print 'looking for imdb link'
                            movie_title = unicode(entry.title.lower()).encode('utf-8')
                            movie_title = re.sub(r'(?:\[.*\]|.1080p|.720p|.dd5\.1|.dts|.vc1|.wmv|.hddvd|.internal|.subbed|.bluray|.dvdrip|.brrip|.limited|.ws|.scr|.dvdscr|.unrated|.proper|.dvdr|.dvd5|.dvd9|ova.*|\ -.*|..complete.|.br25|.br50|.ntsc|.2disc|.xvid|.[0-9]{3}.*|.divx|.hdtv|.x264|.h264|([\-A-z0-9]*$))', "", movie_title)
                            movie_title = movie_title.replace("."," ")
                            query = urllib.urlencode({'q' : movie_title+' site:imdb.com'})
                            url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s' \
                            % (query)
                            #print 'search string: %s' % movie_title
                            search_results = urllib.urlopen(url)
                            json = simplejson.loads(search_results.read())
                            results = json['responseData']['results']
                            if results:
                                imdb_url = results[0]['url']
                                imdb_match = re.compile(r'(/tt.*/)', re.I)

                                match = re.search(imdb_match, imdb_url)

                                if match:
                                    imdb = match.group(1)
                                    imdb = imdb.strip('/')
                                    print 'found imdb link: %s' % imdb

                        elif cat == 'tv' and (self.settings['tvdb_info_fetch'] or self.settings['tvdb_poster_fetch'] or self.settings['tvdb_fanart_fetch']):
                            show_title = entry.title.lower()
                            show_title = re.sub(r'(s[0-9]+e?[0-9].*|\-.*|.?hdtv.*|.season.*|.?[0-9]{4}.*|.?[0-9]{4}.[0-9]{2}.[0-9]{2}.*|.?[0-9x]{4}.*|.hddvd.*|.internal.*|.subbed.*|.bluray.*|.dvdrip.*|.brrip.*|.dvdscr.*|.uncensored.*|.proper.*|.dvdr.*|.dvd5.*|.dvd9.*|.1080p.*|.720p.*|.mkv.*|.avi.*|.wmv.*|.mp4.*)', "", show_title)
                            show_title = show_title.replace("."," ")
                            
                            tvdb = show_title

                        elif cat == 'anime' and (self.settings['tvdb_info_fetch'] or self.settings['tvdb_poster_fetch'] or self.settings['tvdb_fanart_fetch']):
                            anime_title = entry.title.lower()
                            anime_title = re.sub(r'(s[0-9]+e?[0-9].*|.season.*|\-.*|\[.*\]|[0-9s]{3}.*|.?[0-9]{4}.[0-9]{2}.[0-9]{2}.*|.?[0-9x]{4}.*|.?\(.*\)|s[0-9\-]{1,5}.*|ep[0-9]{1,3}.*|.?ova..*|.hddvd.*|.internal.*|.subbed.*|.bluray.*|.dvdrip.*|.brrip.*|.dvdscr.*|.uncensored.*|.proper.*|.dvdr.*|.dvd5.*|.dvd9.*|.1080p.*|.720p.*|.mkv.*|.avi.*|.wmv.*|.mp4.*)', "", anime_title)
                            anime_title = anime_title.replace("."," ")

                            tvdb = anime_title
                            #print 'tvdb: '+tvdb
                                    

                item = {}
                title = entry.title
                if size:
                    title += ' (%s)' % size
                item['name'] = title
                url = urllib.quote_plus(link)
                item['url'] = url
                item['type'] = 'nzb_dl'
                item['id'] = ''
                if imdb:
                    item['imdb'] = imdb
                if tvdb:
                	item['tvdb'] = tvdb
                item['category'] = cat
                items.append(item)

                


            result = { "status": "fail", 'folder':'false'}
            result[ "items" ] = {"assets": items, 'folder':False }
            result[ "status" ] = "ok"
            print 'sabnzbd-xbmc parsed successfully'
            return result
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return {}
        
    def _get_link(self, uri, entry):
        """ Retrieve the post link from this entry """
        uri = uri.lower()
        # Special handling for nzbindex.nl 
        if 'nzbindex.nl' in uri or "newzbin" in uri:
            try:
                link = entry.enclosures[0]['href']
            except:
                link = None
        else:
            # Try standard link first
            link = entry.link
            if not link:
                link = entry.links[0].href

        if link and 'http' in link.lower():
            return link
        else:
            print 'sabnzbd-xbmc failed to find a link to an nzb'
            return None

    def is_nzbs(self, uri):
        if 'nzbs' in uri or 'nzbsxxx' in uri:
            return True
        else:
            return False
