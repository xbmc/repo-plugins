"""
    Player module: plays the selected video
"""

import xbmc

__settings__ = sys.modules[ "__main__" ].__settings__
__language__ = sys.modules[ "__main__" ].__language__

def _get_keyboard( default="", heading="", hidden=False ):
    """ shows a keyboard and returns a value """
    keyboard = xbmc.Keyboard( default, heading, hidden )
    keyboard.doModal()
    if ( keyboard.isConfirmed() ):
        return keyboard.getText()
    return default

# get the video id (we do it here so there is minimal delay with nothing displayed)
video_id = _get_keyboard( heading=__language__( 30910 ) )

if ( video_id ):
    # create the progress dialog (we do it here so there is minimal delay with nothing displayed)
    import sys
    import xbmcgui
    pDialog = xbmcgui.DialogProgress()
    pDialog.create( sys.modules[ "__main__" ].__plugin__, __language__( 30908 ) )

    import os
    import xbmcplugin

    from urllib import unquote_plus

    from YoutubeAPI.YoutubeClient import YoutubeClient


class _Info:
    def __init__( self, *args, **kwargs ):
        self.__dict__.update( kwargs )


class Main:
    def __init__( self ):
        if ( video_id ):
            self._parse_argv()
            self.play_video( video_id )

    def _parse_argv( self ):
        # call _Info() with our formatted argv to create the self.args object
        exec "self.args = _Info(%s)" % ( unquote_plus( sys.argv[ 2 ][ 1 : ].replace( "&", ", " ) ).replace( "\\u0027", "'" ).replace( "\\u0022", '"' ).replace( "\\u0026", "&" ), )

    def play_video( self, video_id ):
        # Youtube client
        client = YoutubeClient( authkey=__settings__.getSetting( "authkey" ) )
        # construct the video url
        video_url = client.BASE_ID_URL % ( video_id, )
        # fetch video information
        url, title, author, genre, rating, runtime, count, date, thumbnail_url, plot, video_id = client.construct_video_url( video_url, ( 18, 22, )[ __settings__.getSetting( "hd_videos" ) == "true" ] )
        # get cached thumbnail, no need to redownload
        thumbnail = xbmc.getCacheThumbName( sys.argv[ 0 ] + sys.argv[ 2 ] + video_id )
        thumbnail = os.path.join( xbmc.translatePath( "special://profile" ), "Thumbnails", "Video", thumbnail[ 0 ], thumbnail )
        # if thumb not found download it
        if ( not os.path.isfile( thumbnail ) ):
            xbmc.executehttpapi( "FileCopy(%s,%s)" % ( thumbnail_url, thumbnail.encode( "utf-8" ), ) )
        # construct our listitem
        listitem = xbmcgui.ListItem( title, runtime, thumbnailImage=thumbnail )
        # set the key information
        listitem.setInfo( "video", { "Title": title, "Director": author, "Genre": genre, "Rating": rating, "Duration": runtime, "Count": count, "Date": date, "PlotOutline": plot, "Plot": plot } )
        # Play video with the proper core
        xbmc.Player().play( url, listitem )
