"""
    Plugin for watching Apple Movie Trailers
"""

# main imports
import sys
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

import time
import re
import urllib
import datetime
from xml.sax.saxutils import unescape

from utils import LOG, get_legal_filepath
from MediaWindow import MediaWindow, DirectoryItem


class _urlopener( urllib.FancyURLopener ):
    version = sys.modules[ "__main__" ].__useragent__
# set for user agent
urllib._urlopener = _urlopener()


class _Parser:
    Addon = xbmcaddon.Addon( id=os.path.basename( os.getcwd() ) )
    
    def __init__( self, settings, MediaWindow ):
        self.success = True
        self.settings = settings
        self.MediaWindow = MediaWindow
        # get our regions format
        self.date_format = xbmc.getRegion( "datelong" ).replace( "DDDD,", "" ).replace( "MMMM", "%B" ).replace( "D", "%d" ).replace( "YYYY", "%Y" ).strip()
        # get the list

    def parse_source( self, xmlSource, category ):
        # if category is genres, studios, directors or actors. we handle these as virtual folders
        if ( category in ( u"genres", u"studios", u"directors", u"actors", ) ):
            self._parse_categories( xmlSource, category )
        else:
            self._parse_trailers( xmlSource, category )

    def _parse_categories( self, xmlSource, category ):
        try:
            # encoding
            encoding = re.findall( "<\?xml version=\"[^\"]*\" encoding=\"([^\"]*)\"\?>", xmlSource[ 0 ] )[ 0 ]
            # gather all trailer records <movieinfo>
            trailers = re.findall( "<movieinfo id=\".+?\"><info>.+?<studio>(.*?)</studio>.+?<director>(.*?)</director>.+?(?:<cast>(.+?)</cast>)?<genre>(.+?)</genre>.+?</movieinfo>", xmlSource[ 0 + ( 2 * ( self.settings[ "trailer_quality" ] > 1 and self.settings[ "trailer_hd_only" ] ) ) ] )
            # use dictionary method to filter out duplicates; set our item list
            dupes = {}
            # enumerate thru the trailers list and create our category list
            for studio, directors, actors, genres in trailers:
                # genres category
                if ( category == "genres" ):
                    # parse genres 
                    genres = re.findall( "<name>(.+?)</name>", genres )
                    # filter out duplicates
                    for x in genres:
                        dupes[ x ] = ( x, "DefaultGenre.png", None, )
                elif ( category == "studios" ):
                    # filter out duplicates
                    dupes[ studio ] = ( studio, "DefaultStudios.png", None, )
                elif ( category == "directors" ):
                    # parse directors 
                    directors = directors.split( ", " )
                    # filter out duplicates
                    for x in directors:
                        dupes[ x ] = ( x, "DefaultDirector.png", None, )
                elif ( category == "actors" ):
                    # parse actors 
                    actors = re.findall( "<name>(.+?)</name>", actors )
                    # filter out duplicates
                    for x in actors:
                        dupes[ x ] = ( x, "DefaultActor.png", "special://profile/Thumbnails/Video/%s/%s" % ( xbmc.getCacheThumbName( "actor" + x )[ 0 ], xbmc.getCacheThumbName( "actor" + x ) ,), )
            # grap the categories
            categories = dupes.values()
            # sort our list
            categories.sort()
            # get our media item
            dirItem = DirectoryItem()
            # set total items
            dirItem.totalItems = len( categories )
            # set as folder since these our virtual folders to filtered lists
            dirItem.isFolder = True
            # add settings menu item
            dirItem.addContextMenuItem( "", "DUMMY TO CLEAR CONTEXT MENU" )
            # enumerate thru and add our items
            for title, icon, thumb in categories:
                # check for cached thumb (only actors)
                if ( thumb is None or not os.path.isfile( thumb ) ):
                    thumb = icon
                # create our listitem
                dirItem.listitem = xbmcgui.ListItem( title, iconImage=icon, thumbnailImage=thumb )
                # set the url
                dirItem.url = "%s?category=%s" % ( sys.argv[ 0 ], urllib.quote_plus( repr( "%s: %s" % ( category, unicode( title, "utf-8" ), ) ) ), )
                # add item
                self.MediaWindow.add( dirItem )
        except Exception, e:
            # oops, notify user what error occurred
            LOG( str( e ), xbmc.LOGERROR )

    def _parse_trailers( self, xmlSource, category ):
        try:
            # set our post dates for the recently added list
            old_postdate_min = new_postdate_min = self.Addon.getSetting( "postdate_min" )
            old_postdate_max = new_postdate_max = self.Addon.getSetting( "postdate_max" )
            # set our ratings
            mpaa_ratings = { "G": 0, "PG": 1, "PG-13": 2, "R": 3, "NC-17": 4, None: 5 }
            # encoding
            encoding = re.findall( "<\?xml version=\"[^\"]*\" encoding=\"([^\"]*)\"\?>", xmlSource[ 0 ] )[ 0 ]
            # split category
            if ( category is not None ):
                category, category_value = category.split( ": " )
            # gather all trailer records <movieinfo>
            trailers = re.findall( "<movieinfo id=\"(.+?)\"><info><title>(.+?)</title><runtime>(.*?)</runtime><rating>(.*?)</rating><studio>(.*?)</studio><postdate>(.*?)</postdate><releasedate>(.*?)</releasedate><copyright>(.*?)</copyright><director>(.*?)</director><description>(.*?)</description></info>(?:<cast>(.+?)</cast>)?(?:<genre>(.+?)</genre>)?<poster><location>(.*?)</location>(?:</poster><poster>)?<xlarge>(.*?)</xlarge></poster><preview><large filesize=\"(.+?)\">(.+?)</large></preview></movieinfo>", xmlSource[ 0 + ( 2 * ( self.settings[ "trailer_quality" ] > 1 and self.settings[ "trailer_hd_only" ] ) ) ] )
            trailers_480p = dict( re.findall( "<movieinfo id=\"(.+?)\">.+?<preview><large filesize=\"(.+?\">.+?)</large></preview></movieinfo>", xmlSource[ 1 ] ) )
            trailers_720p = dict( re.findall( "<movieinfo id=\"(.+?)\">.+?<preview><large filesize=\"(.+?\">.+?)</large></preview></movieinfo>", xmlSource[ 2 ] ) )
            # enumerate thru the movies list and gather info
            for trailer in trailers:
                # encode/clean title
                title = unicode( unescape( trailer[ 1 ] ), encoding, "replace" )
                # format post date, we do this here so filtered lists won't affect the actual results
                postdate = trailer[ 5 ]
                # check if this is a new trailer
                if ( postdate > old_postdate_max ):
                    if ( not new_postdate_min or postdate < new_postdate_min or new_postdate_min == old_postdate_min ):
                        new_postdate_min = postdate
                    if ( postdate > new_postdate_max ):
                        new_postdate_max = postdate
                if ( category == "recent" and postdate < old_postdate_min ):
                    LOG( "* Skipping *: %s   Preferred: %s, Trailer: %s [RECENT]" % ( repr( title ).ljust( 50 ), old_postdate_min, postdate, ) )
                    continue
                # check for valid mpaa rating
                if ( self.settings[ "rating" ] < mpaa_ratings.get( trailer[ 3 ], self.settings[ "not_rated_rating" ] ) ):
                    LOG( "* Skipping *: %s   Preferred: %s, Trailer: %s" % ( repr( title ).ljust( 50 ), ( "G", "PG", "PG-13", "R", "NC-17", "--", )[ self.settings[ "rating" ] ], ( "%s (%s)" % ( ( "G", "PG", "PG-13", "R", "NC-17", "--", )[ self.settings[ "not_rated_rating" ] ], trailer[ 3 ], ), trailer[ 3 ], )[ trailer[ 3 ] != "Not yet rated" ] , ) )
                    continue
                mpaa = ( trailer[ 3 ], "Rated %s" % ( trailer[ 3 ], ), )[ trailer[ 3 ] != "" and trailer[ 3 ] != "Not yet rated" ]
                # parse genres 
                genres = re.findall( "<name>(.+?)</name>", trailer[ 11 ] )
                # if a genre based category, check it
                if ( category == "genres" and category_value not in genres ):
                    LOG( "* Skipping *: %s   Preferred: %s, Trailer: %s [GENRE]" % ( repr( title ).ljust( 50 ), category_value, " / ".join( genres ), ) )
                    continue
                # encode/clean studio
                studio = unicode( unescape( trailer[ 4 ] ), encoding, "replace" )
                # if a studio based category, check it
                if ( category == "studios" and studio != category_value ):
                    LOG( "* Skipping *: %s   Preferred: %s, Trailer: %s [STUDIO]" % ( repr( title ).ljust( 50 ), repr( category_value ), repr( studio ), ) )
                    continue
                # encode/clean director
                director = unicode( unescape( trailer[ 8 ].replace( ", ", " | " ) ), encoding, "replace" )
                # if a director based category, check it
                if ( category == "directors" and category_value not in director ):
                    LOG( "* Skipping *: %s   Preferred: %s, Trailer: %s [DIRECTOR]" % ( repr( title ).ljust( 50 ), repr( category_value ), repr( director ), ) )
                    continue
                # parse actors 
                actors = unicode( unescape( " / ".join( re.findall( "<name>(.+?)</name>", trailer[ 10 ] ) ) ), encoding, "replace" ).split( " / " )
                # if a actor based category, check it
                if ( category == "actors" and category_value not in " / ".join( actors ) ):
                    LOG( "* Skipping *: %s   Preferred: %s, Trailer: %s [ACTOR]" % ( repr( title ).ljust( 50 ), repr( category_value ), repr( " / ".join( actors ) ), ) )
                    continue
                # encode/clean copyright
                copyright = unicode( unescape( trailer[ 7 ] ), encoding, "replace" )
                # convert size to long
                size = long( trailer[ 14 ] )
                # add User-Agent to correct poster url
                poster = ( trailer[ 13 ] or trailer[ 12 ] ) + "?|User-Agent=%s" % ( urllib.quote_plus( sys.modules[ "__main__" ].__useragent__ ), )
                # set initial trailer url
                trailer_url = unicode( trailer[ 15 ], "utf-8" )
                # select preferred trailer quality
                if ( self.settings[ "trailer_quality" ] > 0 ):
                    if ( self.settings[ "trailer_quality" ] > 1 and trailers_720p.has_key( trailer[ 0 ] ) ):
                        if ( not self.settings[ "trailer_hd_only" ] ):
                            size, trailer_url = trailers_720p[ trailer[ 0 ] ].split( "\">" )
                        # replace with 1080p if user preference is 1080p
                        if ( self.settings[ "trailer_quality" ] == 3 ):
                            trailer_url = trailer_url.replace( "a720p.m4v", "h1080p.mov" )
                    elif ( trailers_480p.has_key( trailer[ 0 ] ) ):
                        size, trailer_url = trailers_480p[ trailer[ 0 ] ].split( "\">" )
                    # convert size to long
                    size = long( size )
                # add User-Agent to trailer url
                trailer_url += "?|User-Agent=%s" % ( urllib.quote_plus( sys.modules[ "__main__" ].__useragent__ ), )
                # encode/clean plot
                plot = unicode( unescape( trailer[ 9 ] ), encoding, "replace" )
                # duration of trailer
                # this displays right in video info dialog, but not in the lists (the formula xbmc uses does not accept seconds)
                #duration = xbmc.getLocalizedString( 14044 ).replace( "%i", "%s" ) % ( trailer[ 2 ], )
                duration = "%s:%s" % ( trailer[ 2 ].replace( ":", "" ).rjust( 4, "0" )[ : 2 ], trailer[ 2 ].replace( ":", "" ).rjust( 4, "0" )[ 2 : ], )
                # format release date
                releasedate = trailer[ 6 ]
                # add the item to our media list
                ok = self._add_video( { "title": title, "duration": duration, "mpaa": mpaa, "studio": studio, "postdate": postdate, "releasedate": releasedate, "copyright": copyright, "director": director, "plot": plot, "cast": actors, "genre": " / ".join( genres ), "poster": poster, "trailer": trailer_url, "size": size } )
                # if error adding video, raise an exeption
                if ( not ok ): raise
            # set our new postdate
            self.Addon.setSetting( "postdate_min", new_postdate_min )
            self.Addon.setSetting( "postdate_max", new_postdate_max )
        except Exception, e:
            # oops, notify user what error occurred
            LOG( str( e ), xbmc.LOGERROR )
            self.success = False

    def _add_video( self, video ):
        try:
            # get our media item
            dirItem = DirectoryItem()
            # set the default icon
            icon = "DefaultVideo.png"
            # set an overlay if one is practical
            overlay = ( xbmcgui.ICON_OVERLAY_NONE, xbmcgui.ICON_OVERLAY_HD, )[ "720p." in video[ "trailer" ] or "1080p." in video[ "trailer" ] ]
            # only need to add label and thumbnail, setInfo() and addSortMethod() takes care of label2
            dirItem.listitem = xbmcgui.ListItem( video[ "title" ], iconImage=icon, thumbnailImage=video[ "poster" ] )
            # release date and year
            try:
                # format the date
                release_date = datetime.date( int( video[ "releasedate" ].split( "-" )[ 0 ] ), int( video[ "releasedate" ].split( "-" )[ 1 ] ), int( video[ "releasedate" ].split( "-" )[ 2 ] ) ).strftime( self.date_format )
                # we need just year also
                year = int( video[ "releasedate" ].split( "-" )[ 0 ] )
            except:
                release_date = ""
                year = 0
            # set the key information
            dirItem.listitem.setInfo( "video", { "Title": video[ "title" ], "Overlay": overlay, "Size": video[ "size" ], "Year": year, "Plot": video[ "plot" ], "PlotOutline": video[ "plot" ], "MPAA": video[ "mpaa" ], "Genre": video[ "genre" ], "Studio": video[ "studio" ], "Director": video[ "director" ], "Duration": video[ "duration" ], "Cast": video[ "cast" ], "Date": "%s-%s-%s" % ( video[ "postdate" ][ 8 : ], video[ "postdate" ][ 5 : 7 ], video[ "postdate" ][ : 4 ], ) } )
            # set release date property
            dirItem.listitem.setProperty( "releasedate", release_date )
            # get filepath and tmp_filepath
            tmp_path, filepath = get_legal_filepath( video[ "title" ], video[ "trailer" ].split( "?|" )[ 0 ], 2, self.settings[ "download_path" ], self.settings[ "use_title" ], self.settings[ "use_trailer" ] )
            # set theater showtimes menu item
            dirItem.addContextMenuItem( self.Addon.getLocalizedString( 30900 ), "XBMC.RunPlugin(%s?showtimes=%s)" % ( sys.argv[ 0 ], urllib.quote_plus( repr( video[ "title" ] ) ), ) )
            # check if trailer already exists if user specified
            if ( self.settings[ "play_existing" ] and os.path.isfile( filepath.encode( "utf-8" ) ) ):
                dirItem.url = filepath
                # just add play trailer if trailer exists and user preference to always play existing
                dirItem.addContextMenuItem( self.Addon.getLocalizedString( 30920 ), "XBMC.PlayMedia(%s,noresume)" % ( dirItem.url, ) )
            elif ( self.settings[ "play_mode" ] == 0 ):
                dirItem.url = video[ "trailer" ]
                # we want both play and download if user preference is to stream
                dirItem.addContextMenuItem( self.Addon.getLocalizedString( 30910 ), "XBMC.RunPlugin(%s?download=%s)" % ( sys.argv[ 0 ], urllib.quote_plus( video[ "trailer" ].split( "?|" )[ 0 ] ), ) )
                dirItem.addContextMenuItem( self.Addon.getLocalizedString( 30920 ), "XBMC.PlayMedia(%s,noresume)" % ( dirItem.url, ) )
            else:
                dirItem.url = "%s?download=%s" % ( sys.argv[ 0 ], urllib.quote_plus( video[ "trailer" ].split( "?|" )[ 0 ] ) )
                # only add download if user prefernce is not stream
                dirItem.addContextMenuItem( self.Addon.getLocalizedString( 30910 ), "XBMC.RunPlugin(%s?download=%s)" % ( sys.argv[ 0 ], urllib.quote_plus( video[ "trailer" ].split( "?|" )[ 0 ] ), ) )
            # add the movie information item
            dirItem.addContextMenuItem( self.Addon.getLocalizedString( 30930 ), "XBMC.Action(Info)" )
            # add settings menu item
            dirItem.addContextMenuItem( xbmc.getLocalizedString( 1045 ), "XBMC.RunPlugin(%s?settings=open)" % ( sys.argv[ 0 ], ) )
            # add the item to the media list
            return self.MediaWindow.add( dirItem )
        except Exception, e:
            # oops, notify user what error occurred
            LOG( str( e ), xbmc.LOGERROR )


class Main:
    Addon = xbmcaddon.Addon( id=os.path.basename( os.getcwd() ) )
    # base url
    BASE_CURRENT_URL = "http://www.apple.com/trailers/home/xml/%s"
    # base paths
    BASE_CURRENT_SOURCE_PATH = xbmc.translatePath( Addon.getAddonInfo( "Profile" ) )

    def __init__( self ):
        # parse argv for any params
        params = self._parse_argv()
        # get users preference
        self._get_settings()
        # sort methods
        sortmethods = ( xbmcplugin.SORT_METHOD_LABEL, xbmcplugin.SORT_METHOD_SIZE, xbmcplugin.SORT_METHOD_DATE,
                                 xbmcplugin.SORT_METHOD_VIDEO_RUNTIME, xbmcplugin.SORT_METHOD_VIDEO_YEAR, xbmcplugin.SORT_METHOD_GENRE,
                                 xbmcplugin.SORT_METHOD_MPAA_RATING, xbmcplugin.SORT_METHOD_STUDIO, )
        # initialize buttons, we only need to set these once
        buttons = None
        # fetch items
        if ( params[ "category" ] is None ):
            # skin buttons
            buttons = ( xbmc.getLocalizedString( 21866 ),
                                ( 
                                    ( "Recently Added", "Container.Update(%s?category=%s,replace)" % ( sys.argv[ 0 ], urllib.quote_plus( repr( u"recent: Recently Added" ) ), ), None, None, None, ),
                                    ( xbmc.getLocalizedString( 135 ), "Container.Update(%s?category=%s,replace)" % ( sys.argv[ 0 ], urllib.quote_plus( repr( u"genres" ) ), ), None, None, None, ),
                                    ( xbmc.getLocalizedString( 20388 ), "Container.Update(%s?category=%s,replace)" % ( sys.argv[ 0 ], urllib.quote_plus( repr( u"studios" ) ), ), None, None, None, ),
                                    ( xbmc.getLocalizedString( 20348 ), "Container.Update(%s?category=%s,replace)" % ( sys.argv[ 0 ], urllib.quote_plus( repr( u"directors" ) ), ), None, None, None, ),
                                    ( xbmc.getLocalizedString( 344 ), "Container.Update(%s?category=%s,replace)" % ( sys.argv[ 0 ], urllib.quote_plus( repr( u"actors" ) ), ), None, None, None, ),
                                ),
                            )
        # set category
        else:
            self.PluginCategory = params[ "category" ].replace( "genres", xbmc.getLocalizedString( 135 ) ).replace( "studios", xbmc.getLocalizedString( 20388 ) ).replace( "directors", xbmc.getLocalizedString( 20348 ) ).replace( "actors", xbmc.getLocalizedString( 344 ) ).replace( "recent: ", "" )
        # helper functions
        self.MediaWindow = MediaWindow( int( sys.argv[ 1 ] ), category=self.PluginCategory, content="movies", sortmethods=sortmethods, fanart=( self.settings[ "fanart_image" ], self.Fanart, ), buttons=buttons )
        # fetch videos
        self.MediaWindow.end( self.fetch_trailers( params[ "category" ] ) )

    def _parse_argv( self ):
        try:
            # parse sys.argv for params and return result
            params = dict( urllib.unquote_plus( arg ).split( "=" ) for arg in sys.argv[ 2 ][ 1 : ].split( "&" ) )
            # we need to do this as quote_plus and unicode do not work well together
            params[ "category" ] = eval( params[ "category" ] )
        except:
            # no params passed
            params = { "category": None }
        # return params
        return params

    def _get_settings( self ):
        self.settings = {}
        self.PluginCategory = ( self.Addon.getLocalizedString( 30800 ), self.Addon.getLocalizedString( 30801 ), self.Addon.getLocalizedString( 30802 ), self.Addon.getLocalizedString( 30803 ), )[ int( self.Addon.getSetting( "trailer_quality" ) ) ]
        self.Fanart = ( "standard", "480p", "720p", "1080p", )[ int( self.Addon.getSetting( "trailer_quality" ) ) ]
        self.settings[ "trailer_quality" ] = int( self.Addon.getSetting( "trailer_quality" ) )
        self.settings[ "trailer_hd_only" ] = ( self.Addon.getSetting( "trailer_hd_only" ) == "true" )
        ##self.settings[ "poster" ] = ( self.Addon.getSetting( "poster" ) == "true" )
        self.settings[ "rating" ] = int( self.Addon.getSetting( "rating" ) )
        self.settings[ "not_rated_rating" ] = int( self.Addon.getSetting( "not_rated_rating" ) )
        self.settings[ "download_path" ] = self.Addon.getSetting( "download_path" )
        self.settings[ "play_mode" ] = int( self.Addon.getSetting( "play_mode" ) )
        if ( self.settings[ "play_mode" ] == 2 and self.settings[ "download_path" ] == "" ):
            self.settings[ "play_mode" ] = 1
        self.settings[ "use_title" ] = ( self.Addon.getSetting( "use_title" ) == "true" and self.settings[ "play_mode" ] == 2 )
        self.settings[ "use_trailer" ] = ( self.Addon.getSetting( "use_trailer" ) == "true" and self.settings[ "play_mode" ] == 2 )
        self.settings[ "create_nfo" ] = ( self.Addon.getSetting( "create_nfo" ) == "true" )
        self.settings[ "play_existing" ] = ( self.Addon.getSetting( "play_existing" ) == "true" and self.settings[ "download_path" ] != "" )
        self.settings[ "fanart_image" ] = self.Addon.getSetting( "fanart_image" )

    def fetch_trailers( self, category=None ):
        # spam log file
        LOG( ">>> fetch_trailers(category: %s, rating: %s, quality: %s)" % ( repr( category ), ( "G", "PG", "PG-13", "R", "NC-17", "No Limit", )[ self.settings[ "rating" ] ], self.Fanart, ), heading=True )
        ok = False
        # initialize trailers list
        trailers = []
        # fetch source
        xmlSource = self._get_xml_source()
        # parse source and add our items
        if ( xmlSource ):
            ok = self._parse_xml_source( xmlSource, category )
        # spam log file
        LOG( "<<< fetch_trailers()", heading=True )
        # return result
        return ok

    def _get_xml_source( self ):
        try:
            xmlSource = []
            # grab all xml sources
            for source in ( "current.xml", "current_480p.xml", "current_720p.xml", ):
                # set path and url
                base_path = os.path.join( self.BASE_CURRENT_SOURCE_PATH, source )
                base_url = self.BASE_CURRENT_URL % ( source, )
                # get the source files date if it exists
                try: date = os.path.getmtime( base_path )
                except: date = 0
                # we only refresh if it's been more than a day, 24hr * 60min * 60sec
                refresh = ( ( time.time() - ( 24 * 60 * 60 ) ) >= date )
                # only fetch source if it's been more than a day
                if ( refresh ):
                    # open url
                    usock = urllib.urlopen( base_url )
                else:
                    # open path
                    usock = open( base_path, "r" )
                # read source
                xmlSource += [ usock.read() ]
                # close socket
                usock.close()
                # save the xmlSource for future parsing
                if ( refresh ):
                    ok = self._save_xml_source( xmlSource[ -1 ], base_path )
            # return source
            return xmlSource
        except Exception, e:
            # oops, notify user what error occurred
            LOG( str( e ), xbmc.LOGERROR )
            # error so return empty string
            return []

    def _save_xml_source( self, xmlSource, base_path ):
        try:
            # if the path to the source file does not exist create it
            if ( not os.path.isdir( os.path.dirname( base_path ) ) ):
                os.makedirs( os.path.dirname( base_path ) )
            # open source path for writing
            file_object = open( base_path, "w" )
            # write xmlSource
            file_object.write( xmlSource )
            # close file object
            file_object.close()
            # return successful
            return True
        except Exception, e:
            # oops, notify user what error occurred
            LOG( str( e ), xbmc.LOGERROR )
            # error so return False, we don't actually use this for anything
            return False

    def _parse_xml_source( self, xmlSource, category ):
        # Parse xmlSource for videos
        parser = _Parser( self.settings, self.MediaWindow )
        parser.parse_source( xmlSource, category )
        # return result
        return parser.success
