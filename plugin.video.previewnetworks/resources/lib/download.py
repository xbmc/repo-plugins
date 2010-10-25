"""
    Player module: plays the selected video
"""

import sys
import xbmc
import xbmcaddon
import os

__plugin__ = "plugin.video.previewnetworks"

# set our title
g_title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
# set our studio (only works if the user is using the video library)
g_studio = unicode( xbmc.getInfoLabel( "ListItem.Studio" ), "utf-8" )
# set our studio (only works if the user is using the video library)
g_director = unicode( xbmc.getInfoLabel( "ListItem.Director" ), "utf-8" )
# set our genre (only works if the user is using the video library)
g_genre = unicode( xbmc.getInfoLabel( "ListItem.Genre" ), "utf-8" )
# set our rating (only works if the user is using the video library)
g_mpaa_rating = unicode( xbmc.getInfoLabel( "ListItem.MPAA" ), "utf-8" )
# set our thumbnail
g_thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
# set our plotoutline
g_plotoutline = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
# set movie url
g_movie_url = xbmc.getInfoLabel( "ListItem.FilenameAndPath" )
# set our released date
g_releasedate = xbmc.getInfoLabel( "ListItem.Property(releasedate)" )
# set our year
g_year = 0
if ( xbmc.getInfoLabel( "ListItem.Year" ) ):
    g_year = int( xbmc.getInfoLabel( "ListItem.Year" ) )

# create the progress dialog (we do it here so there is minimal delay with nothing displayed)
import xbmcgui
pDialog = xbmcgui.DialogProgress()
pDialog.create( sys.modules[ "__main__" ].__plugin__ )

import os
import xbmcplugin
import urllib

from util import get_filesystem, get_legal_filepath


class _urlopener( urllib.FancyURLopener ):
    version = sys.modules[ "__main__" ].__useragent__
# set for user agent
urllib._urlopener = _urlopener()


class _Info:
    def __init__( self, *args, **kwargs ):
        self.__dict__.update( kwargs )


class Main:
    #Addon = xbmcaddon.Addon( id=os.path.basename( os.getcwd() ) )
    Addon = xbmcaddon.Addon( id=__plugin__)
    
    def __init__( self ):
        # parse argv
        self._parse_argv()
        # get user preferences
        self._get_settings()
        # download the video
        self._download_video()
        # play the video
        self._play_video()

    def _parse_argv( self ):
        # call _Info() with our formatted argv to create the self.args object
        exec "self.args = _Info(%s)" % ( urllib.unquote_plus( sys.argv[ 2 ][ 1 : ].replace( "&", ", " ) ), )
        # strip User-Agent from trailer url
        self.args.trailer_url = self.args.trailer_url.split( "?|" )[ 0 ]

    def _get_settings( self ):
        self.settings = {}
        self.settings[ "download_path" ] = self.Addon.getSetting( "download_path" )
        self.settings[ "play_mode" ] = int( self.Addon.getSetting( "play_mode" ) )
        if ( self.settings[ "play_mode" ] == 2 and self.settings[ "download_path" ] == "" ):
            self.settings[ "play_mode" ] = 1
        self.settings[ "use_title" ] = ( self.Addon.getSetting( "use_title" ) == "true" and self.settings[ "play_mode" ] == 2 )
        self.settings[ "use_trailer" ] = ( self.Addon.getSetting( "use_trailer" ) == "true" and self.settings[ "use_title" ] == True and self.settings[ "play_mode" ] == 2 )

    def _download_video( self ):
        try:
            # get filepath and tmp_filepath
            tmp_url_split=self.args.trailer_url.split("?")[ 0 ]
            tmp_path, self.filepath = get_legal_filepath( g_title,
                                                          tmp_url_split,
                                                          self.settings[ "play_mode" ],
                                                          self.settings[ "download_path" ],
                                                          self.settings[ "use_title" ],
                                                          self.settings[ "use_trailer" ] )
            # only download if the trailer doesn't exist
            if ( not os.path.isfile( self.filepath.encode( "utf-8" ) ) ):
                # only need to retrieve video if not in tmp path
                if ( not os.path.isfile( tmp_path.encode( "utf-8" ) ) ):
                    # fetch the video
                    urllib.urlretrieve( self.args.trailer_url.encode( "utf-8" ), tmp_path, self._report_hook )
                # create the conf file for xbox and copy to final location
                ok = self._finalize_download( tmp_path )
                # if the copy failed raise an error
                if ( not ok ): raise
        except:
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            # filepath is not always released immediately, we may need to try more than one attempt, sleeping between
            urllib.urlcleanup()
            remove_tries = 3
            while remove_tries and os.path.isfile( tmp_path ):
                try:
                    os.remove( tmp_path )
                except:
                    remove_tries -= 1
                    xbmc.sleep( 1000 )
            pDialog.close()
            self.filepath = ""

    def _report_hook( self, count, blocksize, totalsize ):
        percent = int( float( count * blocksize * 100) / totalsize )
        msg1 = self.Addon.getLocalizedString( 30500 + ( self.settings[ "play_mode" ] == 2 ) ) % ( os.path.basename( self.filepath ), )
        msg2 = ( "", self.Addon.getLocalizedString( 30502 ) % ( os.path.dirname( self.filepath ), ), )[ self.settings[ "play_mode" ] - 1 ]
        pDialog.update( percent, msg1, msg2 )
        if ( pDialog.iscanceled() ): raise
        
    def _finalize_download( self, tmp_path ):
        try:
            if ( tmp_path != self.filepath ):
                # copy the trailer
                msg1 = xbmc.getLocalizedString( 30503 ) % ( os.path.split( self.filepath )[ 1 ], )
                msg2 = xbmc.getLocalizedString( 30502 ) % ( os.path.split( self.filepath )[ 0 ], )
                pDialog.update( -1, msg1, msg2 )
                # necessary for dialog to update
                xbmc.sleep( 50 )
                # use httpapi for file copying
                xbmc.executehttpapi( "FileCopy(%s,%s)" % ( tmp_path, self.filepath.encode( "utf-8" ), ) )
                # remove temporary cache file
                os.remove( tmp_path )
                # create conf file for better MPlayer playback only when trailer saved on xbox and not progressive
                if ( not self.filepath.startswith( "smb://" ) and not self.args.trailer_url.endswith( "p.mov" ) and not os.path.isfile( self.filepath + ".conf" ) and os.environ.get( "OS", "xbox" ) == "xbox" ):
                    f = open( self.filepath + ".conf" , "w" )
                    f.write( "nocache=1" )
                    f.close()
                # copy the thumbnail
                thumbpath = os.path.splitext( self.filepath )[ 0 ] + ".tbn"
                msg1 = xbmc.getLocalizedString( 30503 ) % ( os.path.split( thumbpath )[ 1 ], )
                pDialog.update( -1, msg1, msg2 )
                # necessary for dialog to update
                xbmc.sleep( 50 )
                xbmc.executehttpapi( "FileCopy(%s,%s)" % ( g_thumbnail, thumbpath.encode( "utf-8" ), ) )
            # we succeeded
            return True
        except:
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return False

    def _play_video( self ):
        if ( self.filepath ):
            # set DVDPLAYER as the player for progressive videos
            core_player = ( xbmc.PLAYER_CORE_MPLAYER, xbmc.PLAYER_CORE_DVDPLAYER, )[ self.args.trailer_url.endswith( "p.mov" ) ]
            # create our playlist
            playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
            # clear any possible entries
            playlist.clear()
            # set the default icon
            icon = "DefaultVideo.png"
            # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
            listitem = xbmcgui.ListItem( g_title, iconImage=icon, thumbnailImage=g_thumbnail )
            # set the key information
            listitem.setInfo( "video", { "Title": g_title, "Genre": g_genre, "Studio": g_studio, "Director": g_director, "MPAA": g_mpaa_rating, "Plot": g_plotoutline, "Plotoutline": g_plotoutline, "Year": g_year } )
            # set release date property
            listitem.setProperty( "releasedate", g_releasedate )
            # add item to our playlist
            playlist.add( self.filepath, listitem )
            # close dialog
            pDialog.close()
            # play item
            xbmc.Player( core_player ).play( playlist )
