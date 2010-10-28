"""
    Videos module: fetches a list of playable streams for a specific category
"""

# main imports
import sys
import os
import xbmc
import xbmcgui
import xbmcplugin

import xml.dom.minidom
import urllib

from resources.lib.utils import LOG, Addon


class _Info:
    def __init__( self, *args, **kwargs ):
        self.__dict__.update( kwargs )


class _Parser:
    """
        Parses an xml document for videos
    """
    USERAGENT = "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)"
    # base urls
    BASE_URL = "http://www.cnn.com/"
    BASE_STREAMING_URL = "http://ht.cdn.turner.com/cnn/big/%s_640x360_dl.flv?|User-Agent=%s"#&Accept=%s&Accept-Language=%s&Referer=%s&x-flash-version=%s&Accept-Encoding=%s&Host=%s&Connection=%s"
    BASE_LIVE_STREAMING_URL = "http://www.cnn.com/video/live/cnnlive_%s.asx"

    def __init__( self, xmlSource ):
        # list of _Info() objects
        self.videos = []
        self.large_thumb = Addon.getSetting( "use_large_thumb" ) == "true"
        self._get_videos( xmlSource )

    def _get_videos( self, xmlSource ):
        try:
            # load and parse xmlSource
            doc = xml.dom.minidom.parseString( xmlSource )
            # make sure this is valid <cnn_video> xml source
            root = doc.documentElement
            if ( not root or root.tagName != "cnn_video" ): raise
            # parse and resolve each <video> tag
            videos = root.getElementsByTagName( "video" )
            for video in videos:
                node = video.firstChild
                video_id = image_url = video_url = date = tease_txt = vid_duration = ""
                while ( node ):
                    if ( node.nodeType == node.ELEMENT_NODE and node.hasChildNodes() ):
                        # use this to create the video url
                        if ( node.tagName == "video_id" ):
                            video_id = node.firstChild.nodeValue
                            video_url = self.BASE_STREAMING_URL % ( video_id[ 7 : ], urllib.quote_plus( self.USERAGENT ), )#urllib.quote_plus( "*/*" ), urllib.quote_plus( "en-US" ), urllib.quote_plus( "http://i.cdn.turner.com/xslo/cvp/player/cvp_1.3.4a.24.swf?videoId=world/2010/04/19/intv.dubai.internet.ash.wedding.cnn&player=640x406_start_" ), urllib.quote_plus( "10,0,45,2" ), urllib.quote_plus( "gzip, deflate" ), urllib.quote_plus( "ht.cdn.turner.com" ), urllib.quote_plus( "Keep-Alive" ) )
                            tease_txt = video_id
                        # use larger image file and date
                        elif ( node.tagName == "image_url" or ( self.large_thumb and node.tagName == "splash_image_url" ) ):
                            image_url = node.firstChild.nodeValue
                            if ( not image_url.startswith( "http://" ) ):
                                image_url = self.BASE_URL + image_url[ 1 : ]
                            date = "%s-%s-%s" % ( image_url.split( "/" )[ -2 ], image_url.split( "/" )[ -3 ], image_url.split( "/" )[ -4 ], )
                        # use this for live streams
                        elif ( node.tagName == "video_url" ):
                            video = node.firstChild.nodeValue
                            if ( video.startswith( "Stream" ) ):
                                video_url = self.BASE_LIVE_STREAMING_URL % ( video[ -1 ], )
                        # use this for the title
                        elif ( node.tagName == "tease_txt" ):
                            tease_txt = node.firstChild.nodeValue
                        # duration of video
                        elif ( node.tagName == "vid_duration" ):
                            vid_duration = node.firstChild.nodeValue.replace( ":", "" ).rjust( 4, "0" )
                            vid_duration = "%s:%s" % ( vid_duration[ : 2 ], vid_duration[ 2 : ], )
                    node = node.nextSibling
                # add to our object list
                self.make_object( image_url, video_url, date, tease_txt, vid_duration )
        except Exception, e:
            # oops, notify user what error occurred
            LOG( str( e ), xbmc.LOGERROR )
        # clean-up document object
        try: doc.unlink()
        except: pass

    def make_object( self, image_url, video_url, date, tease_txt, vid_duration ):
        # add item to our _Info() object list
        self.videos += [ _Info( image_url=image_url, url=video_url, date=date, title=tease_txt, duration=vid_duration ) ]


class Main:
    # base paths
    BASE_CACHE_PATH = os.path.join( xbmc.translatePath( "special://profile/" ), "Thumbnails", "Video" )
    # plugin handle
    _handle = int( sys.argv[ 1 ] )

    def __init__( self ):
        self._parse_argv()
        self.get_videos()

    def _parse_argv( self ):
        # call _Info() with our formatted argv to create the title and url constants
        exec "self.args = _Info(%s)" % ( urllib.unquote_plus( sys.argv[ 2 ][ 1 : ].replace( "&", ", " ) ), )

    def get_videos( self ):
        try:
            # open url
            usock = urllib.urlopen( self.args.url )
            # read source
            xmlSource = usock.read()
            # close socket
            usock.close()
            # parse xmlSource for videos and fill media list
            ok = self._fill_media_list( _Parser( xmlSource ).videos )
        except Exception, e:
            # oops, notify user what error occurred
            LOG( str( e ), xbmc.LOGERROR )
            # set failed
            ok = False
        # send notification we're finished, successfully or unsuccessfully
        xbmcplugin.endOfDirectory( handle=self._handle, succeeded=ok )

    def _fill_media_list( self, videos ):
        try:
            ok = True
            # enumerate through the list of videos and add the item to the media list
            for video in videos:
                # if this is a live stream clear the thumbnail
                if ( video.url.endswith( ".asx" ) ):
                    self._clear_asx_thumbnail( video.url )
                # set default icon
                icon = "DefaultVideo.png"
                # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
                listitem=xbmcgui.ListItem( label=video.title, iconImage=icon, thumbnailImage=video.image_url )
                # add the different infolabels we want to sort by
                listitem.setInfo( type="Video", infoLabels={ "TVShowTitle": "CNN Video", "Season": 1, "Episode": 1, "Title": video.title, "Genre": self.args.title, "Duration": video.duration, "Date": video.date, "Premiered": video.date } )
                # add the item to the media list
                ok = xbmcplugin.addDirectoryItem( handle=self._handle, url=video.url, listitem=listitem, totalItems=len( videos ) )
                # if user cancels, call raise to exit loop
                if ( not ok ): raise
            # set content
            xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content="episodes" )
        except Exception, e:
            # oops, notify user what error occurred
            LOG( str( e ), xbmc.LOGERROR )
        # if successful and user did not cancel, add all the required sort methods and set plugin category
        if ( ok ):
            xbmcplugin.addSortMethod( handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
            xbmcplugin.addSortMethod( handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_DATE )
            xbmcplugin.addSortMethod( handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
            # set fanart
            self._set_fanart()
            # set our plugin category
            xbmcplugin.setPluginCategory( handle=self._handle, category=self.args.title )
        # return result
        return ok

    def _set_fanart( self ):
        # user fanart preference
        fanart = [ Addon.getSetting( "fanart_image" ), [ None, Addon.getSetting( "fanart_path" ) ][ Addon.getSetting( "fanart_path" ) != "" and Addon.getSetting( "fanart_type" ) == "0" ], self.args.title ]
        # if user passed fanart tuple (image, category path,)
        if ( fanart is not None ):
            # if skin has fanart image use it
            fanart_image = Addon.getAddonInfo( "id" ) + "-fanart.png"
            # if no skin image check for a category image
            if ( not xbmc.skinHasImage( fanart_image ) ):
                if ( fanart[ 1 ] is not None ):
                    # set category image
                    fanart_image = fanart[ 1 ] + "%s.png" % fanart[ 2 ].split( ": " )[ 0 ]
                else:
                    # set user preference image
                    fanart_image = fanart[ 0 ]
            # set fanart
            xbmcplugin.setPluginFanart( handle=self._handle, image=fanart_image )

    def _clear_asx_thumbnail( self, url ):
        # make the proper cache filename and path
        filename = xbmc.getCacheThumbName( url )
        filepath = os.path.join( self.BASE_CACHE_PATH, filename[ 0 ], filename )
        try:
            # remove the cached thumbnail for live streams
            if ( os.path.isfile( filepath ) ):
                os.remove( filepath )
        except Exception, e:
            # oops, notify user what error occurred
            LOG( str( e ), xbmc.LOGERROR )
