"""
    Category module: list of categories to use as folders
"""

# main imports
import sys
import os
import xbmc
import xbmcgui
import xbmcplugin

__settings__ = sys.modules[ "__main__" ].__settings__
__language__ = sys.modules[ "__main__" ].__language__

from urllib import quote_plus, unquote_plus


class _Info:
    def __init__( self, *args, **kwargs ):
        self.__dict__.update( kwargs )


class Main:
    # base paths
    BASE_PLUGIN_THUMBNAIL_PATH = os.path.join( os.getcwd(), "thumbnails" )

    def __init__( self ):
        # parse sys.argv
        self._parse_argv()
        # authenticate user
        self.authenticate()
        if ( not sys.argv[ 2 ] ):
            self.get_categories()
        else:
            self.get_categories( False )

    def _parse_argv( self ):
        if ( not sys.argv[ 2 ] ):
            self.args = _Info( title="" )
        else:
            # call _Info() with our formatted argv to create the self.args object
            exec "self.args = _Info(%s)" % ( unquote_plus( sys.argv[ 2 ][ 1 : ].replace( '&', ', ' ) ).replace( '\\u0027', "'" ).replace( '\\u0022', '"' ).replace( '\\u0026', '&' ), )

    def authenticate( self ):
        # if this is first run open settings
        self.openSettings()
        # authentication is not permanent, so do this only when first launching plugin
        if ( not sys.argv[ 2 ] ):
            # get the users settings
            password = __settings__.getSetting( "user_password" )
            # we can only authenticate if both email and password are entered
            self.authkey = ""
            if ( self.username and password ):
                # our client api
                from YoutubeAPI.YoutubeClient import YoutubeClient
                client = YoutubeClient()
                # make the authentication call
                self.authkey, userid = client.authenticate( self.username, password )
            # save authkey even if failed, so no token expired error
            __settings__.setSetting( "authkey", self.authkey )

    def openSettings( self ):
        # is this the first time plugin was run and user has not set email
        if ( not sys.argv[ 2 ] and __settings__.getSetting( "username" ) == "" and __settings__.getSetting( "runonce" ) == "" ):
            # set runonce
            __settings__.setSetting( "runonce", "1" )
            # open settings
            __settings__.openSettings()
        # we need to get the users email
        self.username = __settings__.getSetting( "username" )

    def get_categories( self, root=True ):
        # default categories
        if ( root ):
            categories = (
                                    ( __language__( 30952 ), "presets_videos", "", "", "", True, "updated", 0, "", False, ),
                                    ( __language__( 30953 ), "presets_users", "", "", "", True, "updated", 0, "", False, ),
                                    ( __language__( 30969 ), "presets_categories", "", "", "", True, "updated", 0, "", False, ),
                                    ( __language__( 30957 ), "top_rated", "", "", "", True, "rating", 0, "", False, ),
                                    ( __language__( 30963 ), "top_favorites", "", "", "", True, "relevance", 0, "", False, ),
                                    ( __language__( 30961 ), "my_uploads", "", "", "", True, "updated", 0, "", True, ),
                                    ( __language__( 30962 ), "my_favorites", "", "", "", True, "updated", 0, "", True, ),
                                    ( __language__( 30971 ), "my_subscriptions", "", "", "", True, "updated", 0, "", True, ),
                                    ( __language__( 30954 ), "recently_featured", "", "", "", True, "updated", 0, "", False, ),
                                    ( __language__( 30967 ), "most_recent", "", "", "", True, "relevance", 0, "", False, ),
                                    ( __language__( 30951 ), "most_viewed", "", "", "", True, "viewCount", 0, "", False, ),
                                    ( __language__( 30964 ), "most_discussed", "", "", "", True, "relevance", 0, "", False, ),
                                    ( __language__( 30965 ), "most_linked", "", "", "", True, "relevance", 0, "", False, ),
                                    ( __language__( 30966 ), "most_responded", "", "", "", True, "relevance", 0, "", False, ),
                                    ( __language__( 30958 ), "watch_on_mobile", "", "", "", True, "updated", 0, "", False, ),
                                    ( __language__( 30960 ), "play_video_by_id", "", "", "", False, "relevance", 0, "", False, ),
                                )
        # search preset category
        elif ( "category='presets_videos'" in sys.argv[ 2 ] ):
            categories = self.get_presets( 0 )
        # user preset category
        elif ( "category='presets_users'" in sys.argv[ 2 ] ):
            categories = self.get_presets( 1 )
        # category preset category
        elif ( "category='presets_categories'" in sys.argv[ 2 ] ):
            categories = self.get_presets( 2 )
        elif ( "category='delete_preset'" in sys.argv[ 2 ] ):
            categories = self.delete_preset()
        elif ( "category='my_subscriptions'" in sys.argv[ 2 ] ):
            categories = self.get_my_subscriptions()
            
        # do not run for delete preset
        if ( categories ):
            # fill media list
            ok = self._fill_media_list( categories )
            # set cache to disc
            cacheToDisc = ( ok and not ( "category='presets_videos'" in sys.argv[ 2 ] or "category='presets_users'" in sys.argv[ 2 ] or "category='presets_categories'" in sys.argv[ 2 ] ) )
            # send notification we're finished, successfully or unsuccessfully
            xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok, cacheToDisc=cacheToDisc )

    def get_presets( self, ptype ):
        # set category
        search_type = ( "videos", "users", "categories", )[ ptype ]
        # initialize our category tuple
        categories = ()
        # add our new search item
        if ( ptype == 2 ):
            categories += ( ( __language__( 30970 ), "search_categories", "", "", "", True, "updated", 3, "", False, ), )
        elif ( ptype == 1 ):
            categories += ( ( __language__( 30955 ), "search_users", "", "", "", True, "updated", 2, "", False, ), )
        else:
            categories += ( ( __language__( 30956 ), "search_videos", "", "", "", True, "updated", 1, "", False, ), )
        # fetch saved presets
        try:
            # read the queries
            presets = eval( __settings__.getSetting( "presets_%s" % ( search_type, ) ) )
            # sort items
            presets.sort()
        except:
            # no presets found
            presets = []
        # enumerate through the presets list and read the query
        for query in presets:
            try:
                # set video query and user query to empty
                vq = username = cat = u""
                # set thumbnail
                thumbnail = query.split( " | " )[ 3 ].encode( "utf-8" )
                # if this is the user presets set username else set video query
                if ( ptype == 2 ):
                    vq = query.split( " | " )[ 0 ].encode( "utf-8" )
                    cat = query.split( " | " )[ 2 ].encode( "utf-8" )
                elif ( ptype == 1 ):
                    username = query.split( " | " )[ 0 ].encode( "utf-8" )
                else:
                    vq = query.split( " | " )[ 0 ].encode( "utf-8" )
                # add preset to our dictionary
                categories += ( ( query.split( " | " )[ 1 ].encode( "utf-8" ), "videos", vq, username, cat, True, "updated", 0, thumbnail, False, ), )
            except:
                # oops print error message
                print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
        return categories

    def delete_preset( self ):
        try:
            # read the queries
            presets = eval( __settings__.getSetting( "presets_%s" % ( "videos", "users", "categories", )[ self.args.issearch - 1  ], ) )
            # if this is an existing search, move it up
            for count, preset in enumerate( presets ):
                if ( self.args.query in repr( preset ) ):
                    del presets[ count ]
                    break
        except:
            # no presets found
            presets = []
        # save presets
        __settings__.setSetting( "presets_%s" % ( "videos", "users", "categories", )[ self.args.issearch - 1  ], repr( presets ) )
        # refresh container so item is removed
        xbmc.executebuiltin( "Container.Refresh" )

    def get_my_subscriptions( self ):
        self.username = __settings__.getSetting( "username" )
        self.authkey = __settings__.getSetting( "authkey" )
        # our client api
        from YoutubeAPI.YoutubeClient import YoutubeClient
        client = YoutubeClient( base_url=YoutubeClient.BASE_USERS_URL, authkey=self.authkey )
        # start index should be 1, TODO: may need to fix for page 2...
        start_index = ( self.args.page - 1 ) * int( __settings__.getSetting( "perpage" ) ) + 1
        # get subscriptions
        feeds = client.my_subscriptions( orderby=self.args.orderby, related=self.args.related, region_id="", time="", racy=__settings__.getSetting( "include_racy" ), start__index=start_index, max__results=int( __settings__.getSetting( "perpage" ) ), vq=self.args.vq, author=self.args.username, category=self.args.cat )
        # initialize our categories
        categories = []
        # iterate thru and create an item same as user search
        for feed in feeds[ "feed" ].get( "entry", [] ):
            # add subscription to our dictionary
            categories += [ [ feed[ "yt$username" ][ "$t" ], "videos", self.args.vq, feed[ "yt$username" ][ "$t" ], self.args.cat, True, "updated", 0, feed[ "media$thumbnail" ][ "url" ], False ] ]
        # return categories
        return categories

    def _fill_media_list( self, categories ):
        try:
            ok = True
            # enumerate through the tuple of categories and add the item to the media list
            for ( ltitle, method, vq, username, cat, isfolder, orderby, issearch, thumbnail, user_required, ) in categories:
                # if a username is required for category and none supplied, skip category
                if ( user_required and self.authkey == "" ): continue
                # set the callback url
                url = '%s?title=%s&category=%s&page=1&vq=%s&username=%s&cat=%s&orderby=%s&related=""&issearch=%d&update_listing=%d' % ( sys.argv[0], quote_plus( repr( ltitle ) ), repr( method ), quote_plus( repr( vq ) ), quote_plus( repr( username ) ), quote_plus( repr( cat ) ), repr( orderby ), issearch, False, )
                # check for a valid custom thumbnail for the current category
                thumbnail = thumbnail or self._get_thumbnail( method )
                # set the default icon
                icon = "DefaultFolder.png"
                # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
                listitem=xbmcgui.ListItem( ltitle, iconImage=icon, thumbnailImage=thumbnail )
                # TODO: verify if this should work
                # set fanart
                fanart = "%s-fanart.png" % os.path.join( sys.modules[ "__main__" ].__plugin__, method, )
                if ( os.path.isfile( fanart ) ):
                    listitem.setProperty( "fanart_image", fanart )
                # add context menu items
                cm = []
                # add queue video
                if ( not issearch and not method.startswith( "presets_" ) and isfolder ):
                    cm += [ ( __language__( 30509 ), "XBMC.Action(Queue)", ) ]
                # add remove from search for presets
                if ( method == "videos" ):
                    issearch = 1 + ( "category='presets_users'" in sys.argv[ 2 ] in sys.argv[ 2 ] ) + ( 2 * ( "category='presets_categories'" in sys.argv[ 2 ] ) )
                    query = vq or username
                    query += " | " + ltitle + " | "
                    cm += [ ( __language__( 30508 ), "XBMC.RunPlugin(%s?category='delete_preset'&issearch=%d&query=%s&update_listing=False)" % ( sys.argv[0], issearch, quote_plus( repr( query ) ), ) ) ]

                # add context menu items
                listitem.addContextMenuItems( cm, replaceItems=True )
                # add the item to the media list
                ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), url=url, listitem=listitem, isFolder=isfolder, totalItems=len( categories ) )
                # if user cancels, call raise to exit loop
                if ( not ok ): raise
            # we do not want to sort queries list
            if ( "category='presets_videos'" in sys.argv[ 2 ] or "category='presets_users'" in sys.argv[ 2 ] or "category='presets_categories'" in sys.argv[ 2 ] ):
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
            # set our plugin category
            xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=self.args.title )
            # set our fanart from user setting
            if ( __settings__.getSetting( "fanart_image" ) ):
                xbmcplugin.setPluginFanart( handle=int( sys.argv[ 1 ] ), image=__settings__.getSetting( "fanart_image" ) )
        except:
            # user cancelled dialog or an error occurred
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            ok = False
        return ok

    def _get_thumbnail( self, title ):
        # create the full thumbnail path for skins directory
        thumbnail = os.path.join( sys.modules[ "__main__" ].__plugin__, title + ".png" )
        # use a plugin custom thumbnail if a custom skin thumbnail does not exists
        if ( not xbmc.skinHasImage( thumbnail ) ):
            # create the full thumbnail path for plugin directory
            thumbnail = os.path.join( self.BASE_PLUGIN_THUMBNAIL_PATH, title + ".png" )
            # use a default thumbnail if a custom thumbnail does not exists
            if ( not os.path.isfile( thumbnail ) ):
                thumbnail = "DefaultFolder.png"
        return thumbnail
