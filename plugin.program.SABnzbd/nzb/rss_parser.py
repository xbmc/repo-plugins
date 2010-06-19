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
                if self.is_newzbin(uri):
                    if self.settings['username_newzbin'] and self.settings['password_newzbin'] and 'fauth' not in uri:
                        # Newzbin now seems to always require authentication, so add username and password if fauth not present
                        uri = uri.replace('http://', 'http://%s:%s@' % (self.settings['username_newzbin'], self.settings['password_newzbin']))
                        uri = uri.replace('https://', 'https://%s:%s@' % (self.settings['username_newzbin'], self.settings['password_newzbin']))
                    elif 'fauth' not in uri:
                        print 'sabnzbd-xbmc missing newzbin authentication:', uri
                        msg = 'Missing newzbin user/pass, please enter in the plugin settings.'
                        xbmcgui.Dialog().ok('SABnzbd-XBMC-Plugin', msg)
                        return {}
                    
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
                link = self._get_link(uri, entry)
                if self.is_newzbin(uri) and entry.description:
                    mbre = re.compile(r'size:(.+)mb', re.I)
                    match = re.search(mbre, entry.description.lower())
                    if match:
                        size = match.group(1)
                        size_prefix = 'MB'
                        size = float(size.replace(',',''))
                        if (size >= 1000):
                            size_prefix = 'GB'
                            size = size/1000.0
                        if size_prefix == 'GB':
                            size = '%.1f%s' % (size, size_prefix)
                        if size_prefix == 'MB':
                            size = '%.0f%s' % (size, size_prefix)
                    print 'looking for imdb link'
                    imdb_match = re.compile(r'<a href="http://www.imdb.com/title/(.*)">More Info</a>', re.I)
                    match = re.search(imdb_match, entry.description.lower())
                    if match:
                        imdb = match.group(1)
                        imdb = imdb.strip('/')
                        print 'found imdb link: %s' % imdb
                item = {}
                title = entry.title

		if self.is_nzbs(uri) and entry.description:
                   
                    print 'looking for imdb link'
                    imdb_match = re.compile(r'<a href="http://www.imdb.com/title/(.*)">[0123456789]{7}</a>', re.I)
                    match = re.search(imdb_match, entry.description.lower())
                    if match:
                        imdb = match.group(1)
                        imdb = imdb.strip('/')
                        print 'found imdb link: %s' % imdb
                item = {}
                title = entry.title
                if size:
                    title += ' (%s)' % size
                item['name'] = title
                url = urllib.quote_plus(link)
                item['url'] = url
                item['type'] = 'nzb_dl'
                item['id'] = ''
                item['imdb'] = imdb
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
        # Special handling for newzbin
        if self.is_newzbin(uri):
            try:
                link = entry.link
            except:
                link = None
            if not (link and '/post/' in link.lower()):
                # Use alternative link
                try:
                    link = entry.links[0].href
                except:
                    link = None
        # Special handling for nzbindex.nl 
        elif 'nzbindex.nl' in uri:
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
        
    def is_newzbin(self, uri):
        if 'newzbin' in uri or 'newzxxx' in uri:
            return True
        else:
            return False

    def is_nzbs(self, uri):
        if 'nzbs' in uri or 'nzbsxxx' in uri:
            return True
        else:
            return False
