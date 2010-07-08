"""
    Player module: plays the selected video
"""

# create the progress dialog (we do it here so there is minimal delay with nothing displayed)
import sys
import xbmc
import xbmcgui

__settings__ = sys.modules[ "__main__" ].__settings__
__language__ = sys.modules[ "__main__" ].__language__

pDialog = xbmcgui.DialogProgress()
pDialog.create( sys.modules[ "__main__" ].__plugin__, __language__( 30908 ) )

# main imports
import os
import urllib
import xbmcplugin

from urllib import unquote_plus

from YoutubeAPI.YoutubeClient import YoutubeClient


class _Info:
    def __init__( self, *args, **kwargs ):
        self.__dict__.update( kwargs )


class Main:
    def __init__( self ):
        # parse video url
        self._parse_argv()
        # get user preferences
        self._get_settings()
        # download the video
        self._download_video()
        # play the video
        self._play_video()

    def _parse_argv( self ):
        # call _Info() with our formatted argv to create the self.args object
        exec "self.args = _Info(%s)" % ( unquote_plus( sys.argv[ 2 ][ 1 : ].replace( "&", ", " ) ).replace( "\\u0027", "'" ).replace( "\\u0022", '"' ).replace( "\\u0026", "&" ), )

    def _get_settings( self ):
        self.settings = {}
        self.settings[ "download_path" ] = __settings__.getSetting( "download_path" )
        self.settings[ "use_title" ] = ( __settings__.getSetting( "use_title" ) == "true" )

    def _get_filesystem( self ):
        # get the flavor of XBMC
        filesystem = os.environ.get( "OS", "xbox" )
        # use win32 illegal characters for smb shares to be safe (eg run on linux, save to windows)
        if ( self.settings[ "download_path" ].startswith( "smb://" ) ):
            filesystem = "win32"
        return filesystem

    def _download_video( self ):
        try:
            # Youtube client
            client = YoutubeClient( authkey=__settings__.getSetting( "authkey" ) )
            # construct the video url with session id and get video details
            url, self.g_title, self.g_director, self.g_genre, self.g_rating, self.g_runtime, self.g_count, self.g_date, self.g_thumbnail, self.g_plotoutline, video_id = client.construct_video_url( self.args.video_url, ( 18, 22, )[ __settings__.getSetting( "hd_videos" ) == "true" ] )
            # create our temp save path
            tmp_path = xbmc.translatePath( "special://temp/%s.flv" % ( video_id, ) )
            # get a valid filepath
            if ( self.settings[ "use_title" ] ):
                # add extension to video title
                title = self.g_title + ".flv"
            else:
                # we use the urls trailer name
                title = video_id + ".flv"
            # make the path legal for the users platform
            self.filepath = self._make_legal_filepath( title )
            # get the filesystem the trailer will be saved to
            filesystem = self._get_filesystem()
            # win32 requires encoding to work proper
            if ( self._get_filesystem() == "win32" ):
                filepath = self.filepath.encode( "utf-8" )
            else:
                filepath = self.filepath
            # only download if the trailer doesn't exist
            if ( not os.path.isfile( tmp_path ) and not os.path.isfile( self.filepath ) ):
                # fetch the video
                urllib.urlretrieve( url, tmp_path, self._report_hook )
            ok = True
            # finalize
            if ( not os.path.isfile( filepath ) ):
                # copy to final location
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
        msg1 = __language__( 30601  ) % ( os.path.split( self.filepath )[ 1 ], )
        msg2 = __language__( 30602 ) % ( os.path.split( self.filepath )[ 0 ], )
        pDialog.update( percent, msg1, msg2 )
        if ( pDialog.iscanceled() ): raise

    def _make_legal_filepath( self, title ):
        # TODO: figure out how to determine download_path's filesystem, statvfs() not available on windows
        import re
        # different os's have different illegal characters
        illegal_characters = { "xbox": '\\/,*=|<>?;:\"+', "win32": '\\/*|<>?:\"', "Linux": "/", "OS X": "/:" }
        # get the flavor of XBMC
        environment = os.environ.get( "OS", "xbox" )
        # get the filesystem the trailer will be saved to
        filesystem = self._get_filesystem()
        # clean the filename
        filename = re.sub( '[%s]' % ( illegal_characters[ filesystem ], ), "_", title )
        # we need to set the length to 37 if filesystem is xbox and filepath isn't a smb share for the .conf file
        if ( filesystem == "xbox" and len( filename ) > 37 and not self.settings[ "download_path" ].startswith( "smb://" ) ):
            name, ext = os.path.splitext( filename )
            filename = name[ : 37 - len( ext ) ].strip() + ext
        # replace any charcaters whose ord > 127 for xbox filesystem
        if ( filesystem == "xbox" ):
            for char in filename:
                if ( ord( char ) > 127 ):
                    filename = filename.replace( char, "_" )
        # return a unicode object
        return unicode( xbmc.translatePath( os.path.join( self.settings[ "download_path" ], filename ) ), "utf-8", "replace" )

    def _finalize_download( self, tmp_path ):
        try:
            # copy the trailer
            pDialog.update( -1 )
            # only copy if the trailer doesn't exist
            if ( not os.path.isfile( self.filepath ) ):
                xbmc.executehttpapi( "FileCopy(%s,%s)" % ( tmp_path, urllib.quote_plus( self.filepath.encode( "utf-8" ) ), ) )
            # fetch the thumbnail
            thumbpath = os.path.splitext( self.filepath )[ 0 ] + ".tbn"
            # necessary for dialog to update
            if ( not os.path.isfile( thumbpath ) ):
                xbmc.executehttpapi( "FileCopy(%s,%s)" % ( self.g_thumbnail, urllib.quote_plus( thumbpath.encode( "utf-8" ) ), ) )
            self.g_thumbnail = thumbpath
            # we succeeded
            return True
        except:
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return False

    def _play_video( self ):
        if ( not self.filepath ):
            pDialog.close()
            return
        # create our playlist
        playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
        # clear any possible entries
        playlist.clear()
        # set the default icon
        icon = "DefaultVideo.png"
        # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
        listitem = xbmcgui.ListItem( self.g_title, iconImage=icon, thumbnailImage=self.g_thumbnail )
        # set the key information
        listitem.setInfo( "video", { "Title": self.g_title, "Genre": self.g_genre, "Director": self.g_director, "Rating": self.g_rating, "Plot": self.g_plotoutline, "Plotoutline": self.g_plotoutline, "Year": int( self.g_date[ -4 : ] ) } )
        # add item to our playlist
        playlist.add( self.filepath, listitem )
        # play item
        xbmc.Player().play( playlist )
