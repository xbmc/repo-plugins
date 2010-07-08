"""
    Player module: plays the selected video
"""

# main imports
import os
import sys

import xbmc
import xbmcgui
import xbmcplugin

__settings__ = sys.modules[ "__main__" ].__settings__
__language__ = sys.modules[ "__main__" ].__language__

from urllib import unquote_plus

from YoutubeAPI.YoutubeClient import YoutubeClient


class _Info:
    def __init__( self, *args, **kwargs ):
        self.__dict__.update( kwargs )


class Main:
    def __init__( self ):
        self._parse_argv()
        self._play_video()

    def _parse_argv( self ):
        # call _Info() with our formatted argv to create the self.args object
        exec "self.args = _Info(%s)" % ( unquote_plus( sys.argv[ 2 ][ 1 : ].replace( "&", ", " ) ).replace( "\\u0027", "'" ).replace( "\\u0022", '"' ).replace( "\\u0026", "&" ), )
    def _play_video( self ):
        # Youtube client
        client = YoutubeClient( authkey=__settings__.getSetting( "authkey" ) )
        # construct the video url with session id and get video details
        url, title, director, genre, rating, runtime, count, date, thumbnail, plotoutline, video_id = client.construct_video_url( self.args.video_url, ( 18, 22, )[ __settings__.getSetting( "hd_videos" ) == "true" ] )
        # get cached thumbnail, no need to redownload
        thumbnail = xbmc.getCacheThumbName( sys.argv[ 1 ] + sys.argv[ 2 ] )
        thumbnail = os.path.join( xbmc.translatePath( "special://profile" ), "Thumbnails", "Video", thumbnail[ 0 ], thumbnail )
        # construct our listitem
        listitem = xbmcgui.ListItem( title, thumbnailImage=thumbnail, path=url )
        # set the key information
        listitem.setInfo( "video", { "Title": title, "Plotoutline": plotoutline, "Plot": plotoutline, "Director": director, "Genre": genre, "Rating": rating, "Date": date } )
        # Resolve url
        xbmcplugin.setResolvedUrl( int( sys.argv[ 1 ] ), True, listitem )
