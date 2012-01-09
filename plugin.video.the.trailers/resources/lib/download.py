# main imports
import os
import sys
import xbmc
import xbmcgui
import xbmcaddon
import urllib
import xbmcvfs

from utils import get_filesystem, get_legal_filepath, log

# Retrieve add-on specified detials
__addon__       = xbmcaddon.Addon()
__addonid__     = ( sys.modules[ "__main__" ].__addonid__ )
__addonname__   = ( sys.modules[ "__main__" ].__addonname__ )
__author__      = ( sys.modules[ "__main__" ].__author__ )
__version__     = ( sys.modules[ "__main__" ].__version__ )
__addonpath__   = ( sys.modules[ "__main__" ].__addonpath__ )
__localize__    = __addon__.getLocalizedString

# create the progress dialog (we do it here so there is minimal delay with nothing displayed)
pDialog = xbmcgui.DialogProgress()
pDialog.create( __addonname__ )
pDialog.update( 0 )


class _urlopener( urllib.URLopener ):
    version = sys.modules[ "__main__" ].__useragent__

    # this is where you add headers. they seem to have no affect
    """
    def __init__( self, *args ):
        urllib.URLopener.__init__( self, *args )
        self.addheader( "Host", "movies.apple.com" )
    """
# set for user agent
urllib._urlopener = _urlopener()


class Main:
    Addon = xbmcaddon.Addon()
    # TODO: we may need to store these in the addContextMenuItem() call, when using a mouse, if the user
    #           moves, before this module can be imported the selection can change.
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
    g_thumbnail = unicode( xbmc.getInfoImage( "ListItem.Thumb" ), "utf-8" )
    # set our plotoutline
    g_plotoutline = unicode( xbmc.getInfoLabel( "ListItem.Plot" ), "utf-8" )
    # set movie url
    g_movie_url = unicode( xbmc.getInfoLabel( "ListItem.FilenameAndPath" ), "utf-8" )
    # set our released date
    g_releasedate = xbmc.getInfoLabel( "ListItem.Property(releasedate)" )
    # set our trailer duration
    g_duration = xbmc.getInfoLabel( "ListItem.Duration" )
    # set cast list
    g_cast = unicode( " / ".join( xbmc.getInfoLabel( "ListItem.Cast" ).split( "\n" ) ), "utf-8" )
    # set our year
    g_year = 0
    if ( xbmc.getInfoLabel( "ListItem.Year" ) ):
        g_year = int( xbmc.getInfoLabel( "ListItem.Year" ) )

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
        # parse sys.argv for params and return result
        self.params = dict( urllib.unquote_plus( arg ).split( "=" ) for arg in sys.argv[ 2 ][ 1 : ].split( "&" ) )
        # apple's xml is utf-8 so create a utf-8 url
        self.params[ "download" ] = unicode( self.params[ "download" ], "utf-8" )

    def _get_settings( self ):
        self.settings = {}
        self.settings[ "download_path" ] = self.Addon.getSetting( "download_path" )
        self.settings[ "play_mode" ] = int( self.Addon.getSetting( "play_mode" ) )
        if ( self.settings[ "play_mode" ] == 2 and self.settings[ "download_path" ] == "" ):
            self.settings[ "play_mode" ] = 1
        self.settings[ "use_title" ] = ( self.Addon.getSetting( "use_title" ) == "true" and self.settings[ "play_mode" ] == 2 )
        self.settings[ "use_trailer" ] = ( self.Addon.getSetting( "use_trailer" ) == "true" and self.settings[ "play_mode" ] == 2 )
        self.settings[ "create_nfo" ] = ( self.Addon.getSetting( "create_nfo" ) == "true" )
        self.settings[ "copy_thumb" ] = ( self.Addon.getSetting( "copy_thumb" ) == "true" )
        self.settings[ "trailer_quality" ] = ( "Standard", "480p", "720p", "1080p", )[ int( self.Addon.getSetting( "trailer_quality" ) ) ]

    def _download_video( self ):
        try:
            # spam log file
            log( ">>> _download_video(title: %s)" % ( repr( self.g_title ), ), heading=True )
            # get filepath and tmp_filepath
            tmppath, self.filepath = get_legal_filepath( self.g_title, self.params[ "download" ], self.settings[ "play_mode" ], self.settings[ "download_path" ], self.settings[ "use_title" ], self.settings[ "use_trailer" ] )
            # only download if the trailer doesn't exist
            if ( not xbmcvfs.exists( self.filepath.encode( "utf-8" ) ) ):
                # only need to retrieve video if not in tmp path
                if ( not xbmcvfs.exists( tmppath.encode( "utf-8" ) ) ):
                    # fetch the video
                    urllib.urlretrieve( self.params[ "download" ], tmppath.encode( "utf-8" ), self._report_hook )
                # copy to final location
                ok = self._finalize_download( tmppath )
                ok = self._finalize_download( tmppath )
                # if the copy failed raise an error
                if ( not ok ): raise
                return True
        except Exception, e:
            # oops, notify user what error occurred
            log( str( e ), xbmc.LOGERROR )
            # filepath is not always released immediately, we may need to try more than one attempt, sleeping between
            urllib.urlcleanup()
            remove_tries = 3
            while remove_tries and os.path.isfile( tmppath ):
                try:
                    os.remove( tmppath.encode( "utf-8" ) )
                except:
                    remove_tries -= 1
                    xbmc.sleep( 1000 )
            pDialog.close()
            self.filepath = ""
        # spam log file
        log( "<<< _download_video()", heading=True )

    # TODO: change text to downloading and add the amt download speed/time?
    def _report_hook( self, count, blocksize, totalsize ):
        percent = int( float( count * blocksize * 100) / totalsize )
        msg1 = self.Addon.getLocalizedString( 30500 + ( self.settings[ "play_mode" ] == 2 ) ) % ( os.path.basename( self.filepath ), )
        msg2 = ( "", self.Addon.getLocalizedString( 30502 ) % ( os.path.dirname( self.filepath ), ), )[ self.settings[ "play_mode" ] - 1 ]

        pDialog.update( percent, msg1, msg2 )
        if ( pDialog.iscanceled() ): raise

    def _finalize_download( self, tmppath ):
        try:
            if ( tmppath != self.filepath ):
                # copy the trailer
                msg1 = self.Addon.getLocalizedString( 30503 ) % ( os.path.basename( self.filepath ), )
                msg2 = self.Addon.getLocalizedString( 30502 ) % ( os.path.dirname( self.filepath ), )
                pDialog.update( 0, msg1, msg2 )
                # Copy the file
                source = tmppath.encode( "utf-8" )
                target = self.filepath.encode( "utf-8" )
                xbmcvfs.copy( source, target )
                # remove temporary cache file
                if xbmcvfs.exists( target ):
                    xbmcvfs.delete( source )
                # necessary for dialog to update
                # create thumb and nfo paths
                thumbpath = os.path.splitext( self.filepath )[ 0 ] + ".tbn"
                nfopath = os.path.splitext( self.filepath )[ 0 ] + ".nfo"
                if ( self.settings[ "copy_thumb" ] ):
                    xbmcvfs.copy(self.g_thumbnail, thumbpath.encode( "utf-8" ))
                # create nfo file
                if ( self.settings[ "create_nfo" ] ):
                    ok = self._create_nfo_file( nfopath )
            # we succeeded
            return True
        except Exception, e:
            # oops, notify user what error occurred
            log( str( e ), xbmc.LOGERROR )
            return False

    def _create_nfo_file( self, tmp_nfopath ):
        # set quality, we do this since not all resolutions have trailers
        quality = "Standard"
        if ( "480p." in self.params[ "download" ] ):
            quality = "480p"
        elif ( "780p." in self.params[ "download" ] ):
            quality = "780p"
        elif ( "1080p." in self.params[ "download" ] ):
            quality = "1080p"
        # set movie info
        nfoSource = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<movieinfo>
    <title>%s</title>
    <quality>%s</quality>
    <runtime>%s</runtime>
    <releasedate>%s</releasedate>
    <mpaa>%s</mpaa>
    <genre>%s</genre>
    <studio>%s</studio>
    <director>%s</director>
    <cast>%s</cast>
    <plot>%s</plot>
    <thumb>%s</thumb>
</movieinfo>
""" % ( self.g_title, quality, self.g_duration, self.g_releasedate, self.g_mpaa_rating, self.g_genre, self.g_studio, self.g_director, self.g_cast, self.g_plotoutline, self.g_thumbnail )
        # save nfo file to temporary file
        return self._save_nfo_file( nfoSource, tmp_nfopath )

    def _save_nfo_file( self, nfoSource, tmp_nfopath ):
        try:
            # open source path for writing
            file_object = open( tmp_nfopath.encode( "utf-8" ), "w" )
            # write xmlSource
            file_object.write( nfoSource.encode( "utf-8" ) )
            # close file object
            file_object.close()
            # return successful
            return True
        except Exception, e:
            # oops, notify user what error occurred
            log( str( e ), xbmc.LOGERROR )
            # return failed
            return False

    def _play_video( self ):
        if ( self.filepath ):
            # set DVDPLAYER as the player for progressive videos
            core_player = ( xbmc.PLAYER_CORE_MPLAYER, xbmc.PLAYER_CORE_DVDPLAYER, )[ self.params[ "download" ].endswith( "p.mov" ) ]
            # create our playlist
            playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
            # clear any possible entries
            playlist.clear()
            # set the default icon
            icon = "DefaultVideo.png"
            # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
            listitem = xbmcgui.ListItem( self.g_title, iconImage=icon, thumbnailImage=self.g_thumbnail )
            # set the key information
            listitem.setInfo( "video", { "Title": self.g_title, "Genre": self.g_genre, "Studio": self.g_studio, "Director": self.g_director, "MPAA": self.g_mpaa_rating, "Plot": self.g_plotoutline, "Plotoutline": self.g_plotoutline, "Year": self.g_year } )
            # set release date property
            listitem.setProperty( "releasedate", self.g_releasedate )
            # add item to our playlist
            playlist.add( self.filepath, listitem )
            # close dialog
            pDialog.close()
            # play item
            xbmc.Player( core_player ).play( playlist )
