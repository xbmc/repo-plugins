"""
newzbin+sabnzbd newsgroup downloading plugin
by switch

derived from xbmc-addons installer plugin by Nuka1195
and partial RSS code from sabnzbd
"""

__version__ = '1.4'

# main imports
import sys
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import time

from threading import Timer
from settings import *
from imdbAPI import IMDbClient
from tvdbAPI import thetvdb
from misc import _get_path, check_attribute, check_dict_key
from cookie_fetcher import CookieFetcher
from rss_parser import RSSParser
from sabnzbd_actions import SABnzbdActions

__settings__ = sys.modules[ "__main__" ].__settings__

HIGH_QUALITY_POSTERS = True
POSTER_SOURCE = 'imdb'

class _Info:
    def __init__( self, *args, **kwargs ):
        self.__dict__.update( kwargs )


class Main:

    def __init__( self ):

        # initiate imdb parser
        self.IMDbFetcher = IMDbClient.IMDbFetcher()
        self.tvdbFetcher = thetvdb.tvdbFetcher()
        self.parser = RSSParser()
        self.sabnzbd = SABnzbdActions()
        
        #fetch settings from settings.xml
        self._get_settings()
        
        self._parse_argv()
        # get the list
        if hasattr(self.args,'download_nzb'):
            url, title, id, cat = self.args.download_nzb.split('!?!')
            # get the list
            self.sabnzbd._download_nzb(url, title=title, category=cat)
        elif hasattr(self.args,'sabnzbd_action'):
            url, title, id, cat = self.args.sabnzbd_action.split('!?!')
            # get the list
            self.sabnzbd._sabnzbd_action(id)
        else:
            '''title = self.args.rss_url.split('!?!')
            trueFalse = __settings__.getSetting( "enableRefresh")

            try:
                if (title[1] != "SABnzbd - Queue"):
                    print "YOU ARE _NOT_ IN THE QUEUE"
                    __settings__.setSetting( "enableRefresh", "True" )
                else:
                    print "YOU _ARE_ IN THE QUEUE"
                    if (not trueFalse or trueFalse == "True"):
                        __settings__.setSetting( "enableRefresh", "False" )
            except IndexError:
                print "YOU ARE IN THE MAIN LISTING"
                __settings__.setSetting( "enableRefresh", "True" )
                print __settings__.getSetting( "enableRefresh" )'''

            ok = self._show_categories()
            # send notification we're finished, successfully or unsuccessfully
            xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok )
            
    def _get_settings( self ):
        self.settings = {}
        self.settings[ "newzbin_show" ] = __settings__.getSetting( "newzbin_show" ) == "true"
        self.settings[ "imdb_info_fetch" ] = __settings__.getSetting( "imdb_info_fetch" ) == "true"
        self.settings[ "imdb_poster_fetch" ] = __settings__.getSetting( "imdb_poster_fetch" ) == "true"
        self.settings[ "poster_size" ] = ( "128", "256", "512", )[ int( __settings__.getSetting( "poster_size" ) ) ]
        self.settings[ "tvdb_info_fetch" ] = __settings__.getSetting( "tvdb_info_fetch" ) == "true"
        self.settings[ "tvdb_poster_fetch" ] = __settings__.getSetting( "tvdb_poster_fetch" ) == "true"
        self.settings[ "tvdb_fanart_fetch" ] = __settings__.getSetting( "tvdb_fanart_fetch" ) == "true"
        
    def _parse_argv( self ):
        # call _Info() with our formatted argv to create the self.args object
        if ( sys.argv[ 2 ] ):
            exec "self.args = _Info(%s)" % ( sys.argv[ 2 ][ 1 : ].replace( "\\u0027", "'" ).replace( "\\u0022", '"' ).replace( "\\u0026", "&" ), )
        else:
            self.args = _Info( rss_url='', cookie='' )

    def _show_categories( self ):
        '''
        Main handler
        '''
        ok = False
        # fetch the items and return them in a dictionary
        items = self._get_items()
        # if the request was successful
        if ( items and items[ "status" ] == "ok" ):
            # if there are assets, we have categories
            ok = self._fill_list( items[ "items" ] )
        return ok

    def _fill_list( self, items ):
        '''
        Generate and show listitems for xbmc from generated the dictionary
        '''
        try:
            ok = False
            useFanart = False
            print 'sabnzbd-xbmc Filling the list'
            # enumerate through the list of categories and add the item to the media list
            print 'sabnzbd-xbmc total items found: %s' % len(items["assets"])
            for item in items[ "assets" ]:
                info = {}
                #if the expected output are folders (does not support a mixed folder/file view)
                if items['folder']:
                    heading = "rss_url"
                    thumbnail = ""
                    isFolder = True
                    item['id'] = ''
                elif item['type'] == 'nzb_dl':
                    heading = "download_nzb"
                    thumbnail = _get_path('sabc_64.png')
                    isFolder = False
                else:
                    heading = "sabnzbd_action"
                    isFolder = False
                    thumbnail = ''
                    
                if 'sabnzbd' in item["name"].lower():
                    icon = thumbnail = _get_path('default.tbn')
                    
                elif item.has_key('imdb') and item['imdb'] and \
                     (self.settings[ "imdb_info_fetch" ] or self.settings[ "imdb_poster_fetch" ]):
                    imdb = 'http://akas.imdb.com/title/%s/' % item['imdb']
                    info = self.IMDbFetcher.fetch_info( imdb, self.settings[ "poster_size" ] , fetch_poster=False)
                    if info and info.poster_url and self.settings[ "imdb_poster_fetch" ]:
                        icon = thumbnail = info.poster_url
                        print 'icon and thumnail set to: %s' % info.poster_url
                    else:
                        print 'no poster, using sabc_64.png'
                        icon = thumbnail = ''
                        
                    if self.settings[ "imdb_poster_fetch" ] and not self.settings[ "imdb_info_fetch" ]:
                        info = {}
                      
                elif item.has_key('tvdb') and item['tvdb'] and (self.settings['tvdb_info_fetch'] or self.settings['tvdb_poster_fetch'] or self.settings['tvdb_fanart_fetch']):
                    info = self.tvdbFetcher.fetch_info(item['tvdb'])
                    if info and info.poster and self.settings['tvdb_poster_fetch']:
                        icon = thumbnail = info.poster
                    else:
                        print 'no poster, using sabc_64.png'
                        icon = thumbnail = ''
                    if info and info.fanart and self.settings["tvdb_fanart_fetch"]:
                        useFanart == True

                elif item["name"].lower().startswith('newzbin'):
                    icon = thumbnail = _get_path('newzbin.png')
                elif isFolder == False:
                    icon = thumbnail = _get_path('sabc_64.png')
                else:
                    icon = "DefaultFolder.png"
                    thumbnail =  ""
                    
                cookie = check_attribute(self.args, 'cookie', 'default')
                cat = check_dict_key(item, 'category', 'default')
                
                try:
                    print u'%s - %s - %s' % (item["name"], thumbnail, cat)
                except:
                    pass
                    
                url = '%s?%s="""%s!?!%s!?!%s!?!%s""",cookie="""%s""",old_handle="%s"' % ( sys.argv[ 0 ], heading, item["url"], item["name"], item["id"], cat, cookie, sys.argv[ 1 ] )
                # set the default icon
                #icon = "DefaultFolder.png"
                title = item['name'].replace("%20"," ")
                title = title.replace('\'S','\'s').replace('Iii','III').replace('Ii','II')
                listitem = xbmcgui.ListItem( title, label2='hi', iconImage=icon, thumbnailImage=thumbnail )
                if not info:
                    icon = "DefaultFolder.png"
                    listitem.setInfo( type="Video", infoLabels={ "Title": title} )
                else:
                    #listitem.setThumbnailImage(info.poster)
                    listitem.setInfo( type="Video", infoLabels={ "Title": title,  "Plot": info.plot, "Rating": info.user_rating, "Duration": info.duration, "Genre": info.genre, "Year": info.year } )
                    if info.fanart:
                        print 'Setting property fanart_image to: '+info.fanart
                        listitem.setProperty('fanart_image', info.fanart)

                # add the item to the media list
                ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), url=url, listitem=listitem, isFolder=isFolder, totalItems=len( items[ "assets" ] ) )
                # if user cancels, call raise to exit loop
                if ( not ok ): raise
        except:
            # user cancelled dialog or an error occurred
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            ok = False
        if ( ok ):
            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
        return ok

    def _get_items( self ):
        try:
            if not self.args.rss_url:
                cats = {"status": "ok", 'items':{'assets':rss_dict, 'folder':True}}
                return cats
            # parse source and return a dictionary
            url, title, id, cat = self.args.rss_url.split('!?!')

            if url == 'enter your rss feed here':
                msg = 'Please enter your RSS feed for this feed in settings.py'
                xbmcgui.Dialog().ok('SABnzbd', msg)
                return {}

            if title == 'SABnzbd - Queue':
                '''queue_time = 2, 5, 10, 15, 30
                queue_setting = __settings__.getSetting( "refresh_queue" )
                print "QUEUE REFRESH: "+str(queue_time[int(queue_setting)])

                def refresh():
                    print "*** CURRENTLY SET TO: "+__settings__.getSetting( "enableRefresh" )
                    if(__settings__.getSetting( "enableRefresh" ) == "False"):
                        xbmc.executebuiltin("Container.Refresh")

                t = Timer(queue_time[int(queue_setting)], refresh)
                t.start()'''

                return self.sabnzbd._sabnzbd_queue()

            #a "searching" rss feed will allow keyboard entry for a search term
            if '%s' in url:
                url = self._show_search(url)
            return self.parser._parse(url, cat)
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return {}

    def _show_search(self, url):
        #keyboard stuff goes here

        kb = xbmc.Keyboard('', 'Enter your search', False)
        kb.doModal()
        if (kb.isConfirmed()):
            text = kb.getText()
            url = url % urllib.quote_plus(text)
        return url