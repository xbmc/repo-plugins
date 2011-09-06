"""
    Plugin for streaming from "preview network"
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
import urllib2
import datetime
from xml.sax.saxutils import unescape

from util import get_filesystem, get_legal_filepath, test_quality
from MediaWindow import MediaWindow, DirectoryItem

__plugin__ = "plugin.video.previewnetworks"

class _urlopener( urllib.FancyURLopener ):
    version = sys.modules[ "__main__" ].__useragent__

# set for user agent
urllib._urlopener = _urlopener()

class _Parser:

    Addon = xbmcaddon.Addon( id=__plugin__)

    def __init__( self, xmlSource, settings, MediaWindow ):
        self.success = True
        self.settings = settings
        self.MediaWindow = MediaWindow
        # get our regions format
        self.date_format = xbmc.getRegion( "datelong" ).replace( "DDDD,", "" ).replace( "MMMM", "%B" ).replace( "D", "%d" ).replace( "YYYY", "%Y" ).strip()
        # get the list
        self.success = self._get_current_videos( xmlSource )

    def _get_current_videos( self, xmlSource ):
        try:
            type_filter = ""
            quality_filter = ""
            title_option = ""
            #quality_target = -1
            quality_target = int(self.Addon.getSetting( "quality" ))
            # encoding
            encoding = re.findall( "<\?xml version=\"[^\"]*\" encoding=\"([^\"]*)\"\?>", xmlSource )[ 0 ]
            # gather all video records <movieinfo>
            movies = re.findall( "<movie movie_id[^>]*>(.*?)</movie>", xmlSource )
            # enumerate thru the movie list and gather info
            ok = True
            for movie in movies:
                info = re.findall( "<products>(.*?)</products>", movie )
                cast = re.findall( "<actors>(.*?)</actors>", movie )
                producers = re.findall( "<producers>(.*?)</producers>", movie )
                products = re.findall( "<products>(.*?)</products>", movie )
                genre = re.findall( "<categories>(.*?)</categories>", movie )
                posters = re.findall( "<pictures>(.*?)</pictures>", movie )
                preview = re.findall( "<clips>(.*?)</clips>", movie )
                # info
                original_titles = re.findall( "<original_title>(.*?)</original_title>", movie )
                titles = re.findall( "<product_title>(.*?)</product_title>", products[ 0 ] )
                studios = re.findall( "<distributor id=\"[^\"]*\">(.*?)</distributor>", products[ 0 ] )
                if ( studios ):
                    studio = unicode( unescape( studios [ 0 ] ), encoding, "replace" )
                postdate = ""
                tmp_postdate = re.findall( "<premiere unix stamp=\"[^\"]*\">(.*?)</premiere>", products[ 0 ] )
                if ( tmp_postdate ):
                   postdate = "%s-%s-%s" % ( tmp_postdate[ 8 : ], tmp_postdate[ 5 : 7 ], tmp_postdate[ : 4 ], )
                copyright = "preview networks"
                directors = re.findall( "<director id=\"[^\"]*\">(.*?)</director>", movie )
                if (directors):
                        director = directors [ 0 ]
                plots = re.findall( "<description>(.*?)</description>", products[ 0 ] )
                if (plots):
                    plot = unicode( unescape( plots[ 0 ] ), encoding, "replace" )
                    plot = re.sub("&#(\d+);", lambda m: chr(int(m.group(1))), plot)
                    plot = re.sub("&quot;", '"', plot)
                    plot = re.sub("&amp;", '&', plot)
                # actors
                actors = []
                if ( cast ):
                    actor_list = re.findall( "<actor id=\"[^\"]*\">(.*?)</actor>", cast[ 0 ] )
                    for actor in actor_list:
                        actors += [ unicode( unescape( actor ), encoding, "replace" ) ]
                # genres
                genres = []
                if ( genre ):
                    genres = re.findall( "<categorie id=\"[^\"]*\">(.*?)</categorie>", genre[ 0 ] )
                genre = " / ".join( genres )

                # poster
                posters_url = []
                posters_type = []
                n_poster = 0
                poster=''
                locations=['','','','','']
                string_reference = "<picture[^>]*>(.*?)</picture>"
                pictures = re.findall( string_reference, posters[ 0 ] )
                for picture in pictures:
                    n_poster += 1
                    posters_url += re.findall ("<url>(.*?)</url>", picture)
                    posters_type += re.findall ("<type_pic id=\"(.*?)\"[^>]*>[^<]*</type_pic>", picture)
                poster = posters_url[0]
                for ind in range( 0, n_poster-1):
                    # poster
                    if (posters_type[ind]=='1'):
                        locations[0] = posters_url[ind]
                    # poster_larger
                    elif (posters_type[ind]=='3'):
                        locations[1] = posters_url[ind]
                    # lobby still
                    elif (posters_type[ind]=='5'):
                        locations[2] = posters_url[ind]
                    # gallery image
                    elif (posters_type[ind]=='7'):
                        locations[3] = posters_url[ind]
                    # video still
                    elif (posters_type[ind]=='11'):
                        locations[4] = posters_url[ind]

                if (locations[self.settings[ "poster" ]]):
                    poster = locations[self.settings[ "poster" ]]
                elif (self.settings["poster"] > 0):
                    if locations[2]:
                        poster = locations[2]
                    elif locations[3]:
                        poster = locations[3]
                    elif locations[4]:
                        poster = locations[4]
                #
                fanart=''
                if locations[2]:
                    fanart=locations[2]
                elif locations[3]:
                    fanart=locations[3]
                elif locations[4]:
                    fanart=locations[4]
                #
                ok = True
                string_reference = "<clip(.*?)</clip>"
                trailers = re.findall( string_reference, preview[ 0 ] )
                for trailer in trailers:
                    # extract trailer_name and trailer_type
                    string_reference = "clip_id=\"[^\"]*\" name=\"(.*?)\""
                    trailer_name = re.findall( string_reference, trailer )
                    string_reference = "clip_id=\"[^\"]*\" name=\"[^\"]*\" clip_type_id=\"(.*?)\""
                    trailer_type = re.findall( string_reference, trailer )
                    if (self.settings[ "extra" ] == True or int(trailer_type[0]) < 5):
                        # extract files
                        string_reference = "<file (.*?)</file>"
                        trailer_files = re.findall(string_reference, trailer )
                        quality_prev = -1
                        quality_curr = -1
                        title_trailer = ''
                        for file_extract in trailer_files:
                            # extract file_type and file_size
                            file_type = re.findall( "format=\"(.*?)\"", file_extract )[ 0 ]
                            file_size = re.findall( "size=\"(.*?)\"", file_extract ) [ 0 ]
                            quality_curr = test_quality(file_size)
                            # seleziona solo i tipi opzionati
                            if ((self.settings[ "type" ] == "all" or self.settings[ "type" ] == file_type )
                                and quality_curr <= quality_target):
                                #quality_prev = quality_curr
                                quality = file_size
                                # extract url
                                trailers = re.findall( "<url>(.*?)</url>", file_extract )
                                if (trailers):
                                    trailer = trailers[ 0 ]
                                else:
                                    trailer = ""
                                # size
                                sizes = re.findall( "<size>(.*?)</size>", file_extract )
                                if (sizes):
                                    size = long(sizes[ 0 ])
                                else:
                                    size = 0
                                releasedates = re.findall( "<pub_date unix_stamp=\"[^\"]*\">(.*?)</pub_date>", file_extract )
                                if ( releasedates ):
                                    releasedate = releasedates[ 0 ]
                                else:
                                    releasedate = ""
                                runtimes = re.findall( "<duration>(.*?)</duration>", file_extract )
                                if (runtimes):
                                    runtime = runtimes [ 0 ]
                                else:
                                    runtime = ""
                                # add the item to our media list
                                if self.settings[ "showtype" ]==True:
                                    title_option = ' (' + file_type + '/' + file_size + ')'
                                else:
                                    title_option = ''
                                #
                                if (self.settings[ "originaltitle" ]==True):
                                    title_trailer = original_titles[ 0 ] + '   [' + trailer_name[ 0 ] + '] ' + title_option
                                else:
                                    title_trailer = titles[ 0 ] + '   [' + trailer_name[ 0 ] + '] ' + title_option
                                title_trailer = unicode( unescape( title_trailer ), encoding, "replace" )
                                title_trailer = re.sub("&#(\d+);", lambda m: chr(int(m.group(1))), title_trailer)
                                title_trailer = re.sub("&quot;", '"', title_trailer)
                                title_trailer = re.sub("&amp;", '&', title_trailer)
                                #
                                # print "quality curr %s, target %s, selected %s" % (quality_curr,quality_target, quality_curr-quality_target)
                                if (quality_curr == quality_target):
                                    quality_prev = quality_target
                                    ok = self._add_video( { "title": title_trailer, "runtime": runtime, "studio": studio, "postdate": postdate, "releasedate": releasedate, "copyright": copyright, "director": director, "plot": plot, "cast": actors, "genre": genre, "poster": poster, "trailer": trailer, "size": size, "fanart": fanart, "quality": quality }, 0 )
                                    # if user cancels, call raise to exit loop
                                    if ( not ok ): raise
                        # -- exit from loop
                        #if self.settings[ "quality" ]=='max' and title_trailer <> '' and quality_curr <> quality_target:
                        if title_trailer <> '' and quality_prev <> quality_target:
                            ok = self._add_video( { "title": title_trailer, "runtime": runtime, "studio": studio, "postdate": postdate, "releasedate": releasedate, "copyright": copyright, "director": director, "plot": plot, "cast": actors, "genre": genre, "poster": poster, "trailer": trailer, "size": size, "fanart": fanart, "quality": quality }, 0 )
                            # if user cancels, call raise to exit loop
                            if ( not ok ): raise
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            ok = False
        return ok

    def _add_video( self, video, total ):
        try:
            # get our media item
            dirItem = DirectoryItem()

            # set total items
            dirItem.totalItems = total
            # set the default icon
            #icon = "DefaultVideo.png"
            #icon = os.path.join(os.getcwd(),'resource','images','list.png')
            icon = os.path.join(self.Addon.getAddonInfo('path'),'resource','images','list.png')
            overlay = ( xbmcgui.ICON_OVERLAY_NONE, xbmcgui.ICON_OVERLAY_HD, )[ video["quality"] == "HD 480p" or video["quality"] == "HD 720p" or video["quality"] == "HD 1080p"]

##            if video["quality"] == "HD 480p":
##                overlay = os.path.join(os.getcwd(),'resource','images','480.png')
##            elif video["quality"] == "HD 720p":
##                overlay = os.path.join(os.getcwd(),'resource','images','720.png')
##            elif video["quality"] == "HD 1080p":
##                overlay = os.path.join(os.getcwd(),'resource','images','1080.png')
##            else:
##                overlay = xbmcgui.ICON_OVERLAY_NONE

            # only need to add label and thumbnail, setInfo() and addSortMethod() takes care of label2
            dirItem.listitem = xbmcgui.ListItem( video[ "title" ], iconImage=icon, thumbnailImage=video[ "poster" ])
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
            dirItem.listitem.setInfo( "video", { "Title": video[ "title" ], "Overlay": overlay, "Size": video[ "size" ], "Year": year, "Plot": video[ "plot" ], "PlotOutline": video[ "plot" ], "Genre": video[ "genre" ], "Studio": video[ "studio" ], "Director": video[ "director" ], "Duration": video[ "runtime" ], "Cast": video[ "cast" ], "Date": video[ "postdate" ] } )
            # set release date property
            dirItem.listitem.setProperty( "releasedate", release_date )
            dirItem.listitem.setProperty( "fanart_image", video[ "fanart" ] )
            # get filepath and tmp_filepath
            tmp_path, filepath = get_legal_filepath( video[ "title" ], video[ "trailer" ], 2, self.settings[ "download_path" ], self.settings[ "use_title" ], self.settings[ "use_trailer" ] )
            # add the movie information item
            dirItem.addContextMenuItem( self.Addon.getLocalizedString(30930), "XBMC.Action(Info)" )
            # set theater showtimes menu item
            #..dirItem.addContextMenuItem( 30900, "XBMC.RunPlugin(%s?Fetch_Showtimes=True&title=%s)" % ( sys.argv[ 0 ], urllib.quote_plus( repr( video[ "title" ] ) ), ) )
            # check if trailer already exists if user specified
            if ( self.settings[ "play_existing" ] and os.path.isfile( filepath.encode( "utf-8" ) ) ):
                dirItem.url = filepath
                # just add play trailer if trailer exists and user preference to always play existing
                dirItem.addContextMenuItem( self.Addon.getLocalizedString(30920), "XBMC.PlayMedia(%s)" % ( dirItem.url, ) )
            elif ( self.settings[ "play_mode" ] == 0 ):
                dirItem.url = video[ "trailer" ]
                # we want both play and download if user preference is to stream
                dirItem.addContextMenuItem( self.Addon.getLocalizedString(30910), "XBMC.RunPlugin(%s?Download_Trailer=True&trailer_url=%s)" % ( sys.argv[ 0 ], urllib.quote_plus( repr( video[ "trailer" ] ) ), ) )
                dirItem.addContextMenuItem( self.Addon.getLocalizedString(30920), "XBMC.PlayMedia(%s)" % ( dirItem.url, ) )
            else:
                dirItem.url = "%s?Download_Trailer=True&trailer_url=%s" % ( sys.argv[ 0 ], urllib.quote_plus( repr( video[ "trailer" ] ) ) )
                # only add download if user prefernce is not stream
                dirItem.addContextMenuItem( self.Addon.getLocalizedString( 30910), "XBMC.RunPlugin(%s?Download_Trailer=True&trailer_url=%s)" % ( sys.argv[ 0 ], urllib.quote_plus( repr( video[ "trailer" ] ) ), ) )
            # add settings menu item
            dirItem.addContextMenuItem(  xbmc.getLocalizedString( 1045 ), "XBMC.RunPlugin(%s?OpenSettings)" % ( sys.argv[ 0 ], ) )
            # add the item to the media list
            return self.MediaWindow.add( dirItem )
        except:
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return False


class Main:
    Addon = xbmcaddon.Addon( id=__plugin__)
    # base paths
    BASE_CURRENT_URL = ""
    ITEM_CURRENT_URL = ""
    BASE_DATA_PATH = os.path.join( xbmc.translatePath( "special://profile/" ), "addon_data", os.path.basename( Addon.getAddonInfo('path') ), "cache" )
    BASE_CURRENT_SOURCE_PATH = os.path.join( xbmc.translatePath( "special://profile/" ), "addon_data", os.path.basename( Addon.getAddonInfo('path')),  "cache" , "trailer_%s.xml" )
    title_option = ""
    type_filter = ""
    quality_filter = ""

    def __init__( self , url_source, item):
        # get users preference
        self.BASE_CURRENT_URL = url_source
        self.ITEM_CURRENT_URL = item
        self._get_settings()

        # sort methods
        sortmethods = ( xbmcplugin.SORT_METHOD_LABEL, xbmcplugin.SORT_METHOD_SIZE, xbmcplugin.SORT_METHOD_DATE,
                        xbmcplugin.SORT_METHOD_VIDEO_RUNTIME, xbmcplugin.SORT_METHOD_VIDEO_YEAR, xbmcplugin.SORT_METHOD_GENRE,
                        xbmcplugin.SORT_METHOD_STUDIO, )
        # skin buttons
        buttons = ( ( 1045, "XBMC.RunPlugin(%s?OpenSettings)" % ( sys.argv[ 0 ], ), None, None, 2, ), )
        # helper functions
        self.MediaWindow = MediaWindow( int( sys.argv[ 1 ] ),
                                        category=self.PluginCategory,
                                        content="movies",
                                        sortmethods=sortmethods,
                                        fanart=self.settings[ "fanart_image" ], buttons=buttons )
        # fetch videos
        self.MediaWindow.end( self.get_videos() )

    def _get_settings( self ):
        self.settings = {}
        self.settings[ "channel_id" ] = "391100379-1"
        self.settings[ "product" ] = "Cinema"
        self.PluginCategory = ( self.Addon.getLocalizedString( 30800 ), self.Addon.getLocalizedString( 30801 ), self.Addon.getLocalizedString( 30802 ), self.Addon.getLocalizedString( 30803 ), self.Addon.getLocalizedString( 30804 ),self.Addon.getLocalizedString( 30805 ),self.Addon.getLocalizedString( 30806 ),self.Addon.getLocalizedString( 30807 ),self.Addon.getLocalizedString( 30808 ),self.Addon.getLocalizedString( 30809 ), )[ int( self.Addon.getSetting( "quality" ) ) ]
        self.Fanart = ( "normal", "normal", "normal", "normal", "normal", "HD", "HD", "HD", "max", )[ int( self.Addon.getSetting( "quality" ) ) ]
        self.settings[ "fanart_image" ] = None
        self.settings[ "quality" ] = ( "small", "medium", "large", "xlarge", "xxlarge", "HD 480p", "HD 720p", "HD 1080p", "max", )[ int( self.Addon.getSetting( "quality" ) ) ]
        self.settings[ "type" ] = ( "flv", "mov", "wmv", "mp4", "3gp", "all", )[ int( self.Addon.getSetting( "type" ) ) ]
        self.settings[ "poster" ] = int( self.Addon.getSetting( "poster" ) )
        self.settings[ "download_path" ] = self.Addon.getSetting( "download_path" )
        self.settings[ "play_mode" ] = int( self.Addon.getSetting( "play_mode" ) )
        if ( self.settings[ "play_mode" ] == 2 and self.settings[ "download_path" ] == "" ):
            self.settings[ "play_mode" ] = 1
        self.settings[ "use_title" ] = ( self.Addon.getSetting( "use_title" ) == "true")
        self.settings[ "use_trailer" ] = ( self.settings[ "download_path" ] != "" )
        self.settings[ "play_existing" ] = ( self.Addon.getSetting( "play_existing" ) == "true" and self.settings[ "download_path" ] != "" )
        self.settings[ "extra" ] = ( self.Addon.getSetting( "extra" ) == "true" )
        self.settings[ "originaltitle" ] = ( self.Addon.getSetting( "originaltitle" ) == "true" )
        self.settings[ "showtype" ] = ( self.Addon.getSetting( "showtype" ) == "true" )
        if (self.settings[ "type" ] == "all" and self.settings[ "quality" ] == "all"):
            self.settings[ "showtype" ] = True
        self.settings[ "country" ] = [ int( self.Addon.getSetting( "country" ) ) ]
        self.settings[ "region" ] = ( "uk", "fr", "de", "es", "it", "ch", "ch-fr", "nl", "dk", "se", "fi", )[ int( self.Addon.getSetting( "country" ) ) ]

    def getKeyboard(self, default = '', heading = '', hidden = False):
        kboard = xbmc.Keyboard(default, heading, hidden)
        kboard.doModal()
        if kboard.isConfirmed():
            return urllib.quote_plus(kboard.getText())
        return ''

    def get_videos( self ):
        ok = False
        # fetch xml source
        xmlSource = self.get_xml_source()
        # parse source and add our items
        if ( xmlSource ):
            ok = self.parse_xml_source( xmlSource )
        return ok

    def get_xml_source( self ):
        try:
            ok = True
            # set proper source
            extension = self.settings[ "region" ]+self.settings[ "product" ]+self.ITEM_CURRENT_URL
            base_path = self.BASE_CURRENT_SOURCE_PATH % extension

            if self.ITEM_CURRENT_URL == '99':
                curr_phrase = ''
                search_phrase = self.getKeyboard(default = curr_phrase, heading = self.Addon.getLocalizedString(30102))
                if search_phrase == '':
                    return -1
                curr_phrase = search_phrase
                base_url = self.BASE_CURRENT_URL % (self.settings[ "region" ],self.settings[ "product" ],self.settings[ "channel_id" ],search_phrase)
            else:
                base_url = self.BASE_CURRENT_URL % (self.settings[ "region" ],self.settings[ "product" ],self.settings[ "channel_id" ])
            #
            # get the source files date if it exists
            try: date = os.path.getmtime( base_path )
            except: date = 0
            # we only refresh if it's been more than a day, 24hr * 60min * 60sec
            if self.ITEM_CURRENT_URL == '99':
                refresh = True
            else:
                refresh = ( ( time.time() - ( 24 * 60 * 60 ) ) >= date )
            # only fetch source if it's been more than a day
            if ( refresh ):
                # open url
                usock = urllib.urlopen( base_url )
            else:
                # open path
                usock = open( base_path, "r" )
            # format xml source
            xmlSource = ''
            for line in usock.read().split( '\n' ):
                xmlSource += line.lstrip().rstrip().replace( '\r', '' ).replace( '\t', '' ).replace( '\n', '' )

            # close socket
            usock.close()
            # save the xmlSource for future parsing
            if ( refresh ):
            	ok = self.save_xml_source( xmlSource )
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            ok = False
        if ( ok ):
            return xmlSource
        else:
            return ""

    def save_xml_source( self, xmlSource ):
        try:
            # set proper source
            # base_path = self.BASE_CURRENT_SOURCE_PATH
            extension = self.settings[ "region" ]+self.settings[ "product" ]+self.ITEM_CURRENT_URL
            base_path = self.BASE_CURRENT_SOURCE_PATH % extension
            # if the path to the source file does not exist create it
            if ( not os.path.isdir( self.BASE_DATA_PATH ) ):
                os.makedirs( self.BASE_DATA_PATH )
            # open source path for writing
            file_object = open( base_path, "w" )
            # write xmlSource
            file_object.write( xmlSource )
            # close file object
            file_object.close()
            # return successful
            return True
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return False

    def parse_xml_source( self, xmlSource ):
        # Parse xmlSource for videos
        parser = _Parser( xmlSource, self.settings, self.MediaWindow )
        return parser.success
