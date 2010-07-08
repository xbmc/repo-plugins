"""
    Videos module: fetches a list of videos for a specific category
"""

# main imports
import sys
import os
import xbmc
import xbmcgui
import xbmcplugin

__settings__ = sys.modules[ "__main__" ].__settings__
__language__ = sys.modules[ "__main__" ].__language__

from urllib import unquote_plus, quote_plus

from YoutubeAPI.YoutubeClient import YoutubeClient


class _Info:
    def __init__( self, *args, **kwargs ):
        self.__dict__.update( kwargs )


class Main:
    # base paths
    BASE_PLUGIN_THUMBNAIL_PATH = os.path.join( os.getcwd(), "thumbnails" )

    def __init__( self ):
        self._get_settings()
        self._get_strings()
        self._get_authkey()
        self._parse_argv()
        self._get_items()

    def _get_settings( self ):
        self.settings = {}
        self.settings[ "username" ] = __settings__.getSetting( "username" )
        self.settings[ "include_racy" ] = ( "exclude", "include", )[ __settings__.getSetting( "include_racy" ) == "true" ]
        self.settings[ "perpage" ] = ( 10, 15, 20, 25, 30, 40, 50, )[ int( __settings__.getSetting( "perpage" ) ) ]
        self.settings[ "feed_time" ] = ( "all_time", "today", "this_week", "this_month", )[ int( __settings__.getSetting( "feed_time" ) ) ]
        self.settings[ "region_id" ] = ( "", "AU", "BR", "CA", "FR", "DE", "GB", "NL", "HK", "IE", "IT", "JP", "MX", "NZ", "PL", "RU", "KR", "ES", "TW", "US", )[ int( __settings__.getSetting( "region_id" ) ) ]
        self.settings[ "saved_searches" ] = ( 10, 20, 30, 40, )[ int( __settings__.getSetting( "saved_searches" ) ) ]
        self.settings[ "download_path" ] = __settings__.getSetting( "download_path" )
        self.settings[ "fanart_image" ] = __settings__.getSetting( "fanart_image" )

    def _get_strings( self ):
        self.localized_string = {}
        self.localized_string[ 30900 ] = __language__( 30900 )
        self.localized_string[ 30901 ] = __language__( 30901 )
        self.localized_string[ 30902 ] = __language__( 30902 )
        self.localized_string[ 30903 ] = __language__( 30903 )
        self.localized_string[ 30905 ] = __language__( 30905 )

    def _parse_argv( self ):
        # call _Info() with our formatted argv to create the self.args object
        exec "self.args = _Info(%s)" % ( unquote_plus( sys.argv[ 2 ][ 1 : ].replace( "&", ", " ) ).replace( "\\u0027", "'" ).replace( "\\u0022", '"' ).replace( "\\u0026", "&" ), )

    def _get_authkey( self ):
        self.authkey = __settings__.getSetting( "authkey" )

    def _get_items( self ):
        # get the videos and/or subcategories and fill the media list
        exec "ok, total = self.%s()" % ( self.args.category, )
        # send notification we're finished, successfully or unsuccessfully
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok, updateListing=self.args.update_listing )#, cacheToDisc=not self.args.issearch )
        # if there were videos and this was a search ask to save result as a preset
        if ( ok and total and self.args.issearch ):
            self.save_as_preset()

    def save_as_preset( self ):
        # select correct query
        query = ( self.args.vq, self.args.username, self.args.vq, )[ self.args.issearch - 1 ]
        # if user or category search and query was found then proceed, should never be an issue for video search
        if ( query or self.args.cat ):
            # fetch saved presets
            try:
                # read the queries
                presets = eval( __settings__.getSetting( "presets_%s" % ( "videos", "users", "categories", )[ self.args.issearch - 1  ], ) )
                # if this is an existing search, move it up
                for count, preset in enumerate( presets ):
                    if ( repr( query + " | " + self.args.title + " | " )[ : -1 ] in repr( preset ) ):
                        del presets[ count ]
                        break
                # limit to number of searches to save
                if ( len( presets ) >= self.settings[ "saved_searches" ] ):
                    presets = presets[ : self.settings[ "saved_searches" ] - 1 ]
            except:
                # no presets found
                presets = []
            # insert our new search
            presets = [ query + " | " + self.args.title + " | " + self.args.cat + " | " + self.query_thumbnail ] + presets
            # save search query
            __settings__.setSetting( "presets_%s" % ( "videos", "users", "categories", )[ self.args.issearch - 1  ], repr( presets ) )

    def most_viewed( self ):
        return self.fetch_videos( YoutubeClient.BASE_STANDARD_URL, feed_time=self.settings[ "feed_time" ], region_id=self.settings[ "region_id" ] )

    def top_rated( self ):
        return self.fetch_videos( YoutubeClient.BASE_STANDARD_URL, feed_time=self.settings[ "feed_time" ], region_id=self.settings[ "region_id" ] )

    def recently_featured( self ):
        return self.fetch_videos( YoutubeClient.BASE_STANDARD_URL, region_id=self.settings[ "region_id" ] )

    def watch_on_mobile( self ):
        return self.fetch_videos( YoutubeClient.BASE_STANDARD_URL )

    def top_favorites( self ):
        return self.fetch_videos( YoutubeClient.BASE_STANDARD_URL, feed_time=self.settings[ "feed_time" ], region_id=self.settings[ "region_id" ] )

    def most_discussed( self ):
        return self.fetch_videos( YoutubeClient.BASE_STANDARD_URL, feed_time=self.settings[ "feed_time" ], region_id=self.settings[ "region_id" ] )

    def most_linked( self ):
        return self.fetch_videos( YoutubeClient.BASE_STANDARD_URL, feed_time=self.settings[ "feed_time" ], region_id=self.settings[ "region_id" ] )

    def most_responded( self ):
        return self.fetch_videos( YoutubeClient.BASE_STANDARD_URL, feed_time=self.settings[ "feed_time" ], region_id=self.settings[ "region_id" ] )

    def most_recent( self ):
        return self.fetch_videos( YoutubeClient.BASE_STANDARD_URL, region_id=self.settings[ "region_id" ] )

    def related( self ):
        return self.fetch_videos( YoutubeClient.BASE_RELATED_URL )

    def search_videos( self ):
        # get the query to search for from the user
        self.args.vq = self._get_keyboard( heading=__language__( 30906 ) )
        # if blank or the user cancelled the keyboard, return
        if ( not self.args.vq ): return False, 0
        # we need to set the title to our query
        self.args.title = self.args.vq
        # we need to set the function to videos
        self.args.category = "videos"
        return self.fetch_videos( YoutubeClient.BASE_SEARCH_URL )

    def search_users( self ):
        # get the username to search for from the user
        self.args.username = self._get_keyboard( heading=__language__( 30907 ) )
        # if blank or the user cancelled the keyboard, return
        if ( not self.args.username ): return False, 0
        # we need to set the title to our query
        self.args.title = self.args.username
        # we need to set the function to users
        self.args.category = "users__uploads"
        ok, total = self.fetch_videos( YoutubeClient.BASE_USERS_URL )
        # if exact match was found return results
        if ( total ): return ok, total
        # if no exact match found we search using regular search engine
        # we need to set the function to videos
        self.args.category = "videos"
        # set the search query to the username
        self.args.vq = self.args.username
        # empty username
        self.args.username = ""
        return self.fetch_videos( YoutubeClient.BASE_SEARCH_URL )

    def search_categories( self ):
        # categories: TODO: maybe download or download in xbmcplugin_categories
        categories = [('Autos', 'Autos & Vehicles'), ('Comedy', 'Comedy'), ('Education', 'Education'), ('Entertainment', 'Entertainment'), ('Film', 'Film & Animation'), ('Games', 'Gaming'), ('Howto', 'Howto & Style'), ('Movies', 'Movies'), ('Movies_Action_adventure', 'Movies - Action/Adventure'), ('Movies_Anime_animation', 'Movies - Anime/Animation'), ('Movies_Classics', 'Movies - Classics'), ('Movies_Comedy', 'Movies - Comedy'), ('Movies_Documentary', 'Movies - Documentary'), ('Movies_Drama', 'Movies - Drama'), ('Movies_Family', 'Movies - Family'), ('Movies_Foreign', 'Movies - Foreign'), ('Movies_Horror', 'Movies - Horror'), ('Movies_Sci_fi_fantasy', 'Movies - Sci-Fi/Fantasy'), ('Movies_Shorts', 'Movies - Shorts'), ('Movies_Thriller', 'Movies - Thriller'), ('Music', 'Music'), ('News', 'News & Politics'), ('Nonprofit', 'Nonprofits & Activism'), ('People', 'People & Blogs'), ('Animals', 'Pets & Animals'), ('Tech', 'Science & Technology'), ('Shortmov', 'Short Movies'), ('Shows', 'Shows'), ('Sports', 'Sports'), ('Trailers', 'Trailers'), ('Travel', 'Travel & Events'), ('Videoblog', 'Videoblogging')]
        # get users choice
        choice = xbmcgui.Dialog().select( __language__( 30912 ), [ title for category, title in categories ] )
        # if user didn't cancel dialog continue
        if ( choice != -1 ):
            # set our category
            self.args.cat = categories[ choice ][ 0 ]
            # get the query to search for from the user
            self.args.vq = self._get_keyboard( heading=__language__( 30913 ) )
            # if blank or the user cancelled the keyboard, return
            if ( not self.args.vq ):
                self.args.cat = ""
                return False, 0
            self.args.vq = ( self.args.vq, "", )[ self.args.vq == "*" ]
            # we need to set the title to our query
            self.args.title = "%s (%s)" % ( self.args.vq, categories[ choice ][ 1 ], )
            self.args.title = self.args.title.strip()
            # we need to set the function to videos
            self.args.category = "videos"
            return self.fetch_videos( YoutubeClient.BASE_SEARCH_URL )

    def my_uploads( self ):
        # logged in users uploads
        return self.fetch_videos( YoutubeClient.BASE_USERS_URL )

    def my_favorites( self ):
        # logged in users favorites
        return self.fetch_videos( YoutubeClient.BASE_USERS_URL )

    def all_videos( self ):
        # we need to set the function to videos
        self.args.category = "videos"
        return self.fetch_videos( YoutubeClient.BASE_SEARCH_URL )

    def videos( self ):
        # we end up here for pages 2 and on
        return self.fetch_videos( YoutubeClient.BASE_SEARCH_URL )

    #def user__favorites( self ):
    #    # set author to user name
    #    self.args.username = self.settings[ "username" ]
    #    return self.fetch_videos( YoutubeClient.BASE_USERS_URL )

    def users__uploads( self ):
        # we end up here for pages 2 and on for user searches
        return self.fetch_videos( YoutubeClient.BASE_USERS_URL )

    def add__favorite( self ):
        # Youtube client
        client = YoutubeClient( YoutubeClient.BASE_USERS_URL, self.authkey )
        client.add_favorites( self.args.video_id )
        return False, 0

    def delete__favorite( self ):
        # Youtube client
        client = YoutubeClient( YoutubeClient.BASE_USERS_URL, self.authkey )
        ok = client.delete_favorites( self.args.edit_url )
        # only need to refresh if successful
        if ( ok ):
            xbmc.executebuiltin( "Container.Refresh" )
        return False, 0

    def fetch_videos( self, url, feed_time="", region_id="" ):
        # Youtube client
        client = YoutubeClient( url, self.authkey )
        # starting video
        start_index = ( self.args.page - 1 ) * self.settings[ "perpage" ] + 1
        # fetch the videos
        # TODO: format=5, <- put this back if videos fail
        exec 'feeds = client.%s( orderby=self.args.orderby, related=self.args.related, region_id=region_id, time=feed_time, racy=self.settings[ "include_racy" ], start__index=start_index, max__results=self.settings[ "perpage" ], vq=self.args.vq, author=self.args.username, category=self.args.cat )' % ( self.args.category, )
        # calculate total pages
        pages = self._get_total_pages( int( feeds[ "feed" ][ "openSearch$totalResults" ][ "$t" ] ) )
        # if this was a search and there is a spelling correction get the correction
        spell_vq = ""
        if ( url == YoutubeClient.BASE_SEARCH_URL and self.args.page == 1 ):
            spell_vq = self._get_spellcorrection( feeds["feed"][ "link" ], feeds[ "encoding" ] )
        # if there are results
        if ( pages or spell_vq ):
            return self._fill_media_list( True, feeds[ "feed" ].get( "entry", [] ), self.args.page, pages, self.settings[ "perpage" ], int( feeds[ "feed" ][ "openSearch$totalResults" ][ "$t" ] ), feeds["encoding"], spell_vq )
        #else return failed
        return False, 0

    def _get_spellcorrection( self, links, encoding ):
        # we need to unquote the spelling correction url
        # initialize the result
        vq = ""
        # enumerate through the links to find a spelling correction url
        for link in links:
            # if we find one, we only need the corrected search phrase
            if ( "spellcorrection" in link[ "rel" ] ):
                # set url using this hack to clean the result (exec is a hack for unescaping \u#### characters)
                exec 'url = u"%s"' % ( unicode( link[ "href" ], encoding ), )
                # find the start of the corrected search phrase
                vq_start = url.find( "vq=" ) + 3
                # find the end of the corrected search phrase
                vq_end = url.find( "&", vq_start )
                # unquote the corrected search phrase
                vq = unquote_plus( url[ vq_start : vq_end ] )
                # no need to continue
                break
        return vq

    def _get_total_pages( self, total ):
        # calculate the total number of pages
        pages = int( total / self.settings[ "perpage" ] ) + ( total % self.settings[ "perpage" ] > 0 )
        return pages

    def _fill_media_list( self, ok, videos, page, pages=1, perpage=1, total=1, encoding="utf-8", spell_vq="" ):
        try:
            # calculate total items including previous, next and spelling folders
            total_items = len( videos ) + ( page < pages ) + ( page > 1 ) + ( spell_vq != "" and len( videos ) )
            # if ok (always is for now) fill directory
            if ( ok ):
                # if this was a search and there is a correction
                if ( spell_vq ):
                    # set the correct query
                    cat = ( "", spell_vq, )[ self.args.issearch == 3 ]
                    username = ( "", spell_vq, )[ self.args.issearch == 2 ]
                    vq = ( "", spell_vq, )[ self.args.issearch == 1 ]
                    # create the callback url
                    url = '%s?title=%s&category=%s&page=%d&vq=%s&username=%s&cat=%s&orderby=%s&related=%s&issearch=%d&update_listing=%d' % ( sys.argv[0], quote_plus( repr( self.args.title ) ), repr( "videos" ), 1, quote_plus( repr( vq ) ), quote_plus( repr( username ) ), quote_plus( repr( cat ) ), repr( self.args.orderby ), repr( self.args.related ), self.args.issearch, True, )
                    # TODO: get rid of self.BASE_PLUGIN_THUMBNAIL_PATH
                    # we set the thumb so XBMC does not try and cache the next pictures
                    thumbnail = os.path.join( self.BASE_PLUGIN_THUMBNAIL_PATH, "spell_page.png" )
                    # set the default icon
                    icon = "DefaultFolder.png"
                    # only need to add label and icon, setInfo() and addSortMethod() takes care of label2
                    listitem=xbmcgui.ListItem( label="%s: %s" % ( __language__( 30911 ), spell_vq, ), iconImage=icon, thumbnailImage=thumbnail )
                    # add the folder item to our media list
                    ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), url=url, listitem=listitem, isFolder=True, totalItems=total_items + ( len( videos ) == 0 ) )
                # if there is more than one page and we are not on the last page, we add our next page folder
                if ( page < pages ):
                    # calculate the starting video
                    startno = page * perpage + 1
                    # calculate the ending video
                    endno = startno + perpage - 1
                    # if there are fewer videos than per_page set endno to total
                    if ( endno > total ):
                        endno = total
                    # create the callback url
                    url = '%s?title=%s&category=%s&page=%d&vq=%s&username=%s&cat=%s&orderby=%s&issearch=0&related=%s&update_listing=%d' % ( sys.argv[0], quote_plus( repr( self.args.title ) ), repr( self.args.category ), page + 1, quote_plus( repr( self.args.vq ) ), quote_plus( repr( self.args.username ) ), quote_plus( repr( self.args.cat ) ), repr( self.args.orderby ), repr( self.args.related ), True, )
                    # TODO: get rid of self.BASE_PLUGIN_THUMBNAIL_PATH
                    # we set the thumb so XBMC does not try and cache the next pictures
                    thumbnail = os.path.join( self.BASE_PLUGIN_THUMBNAIL_PATH, "next.png" )
                    # set the default icon
                    icon = "DefaultFolder.png"
                    # only need to add label and icon, setInfo() and addSortMethod() takes care of label2
                    listitem=xbmcgui.ListItem( label="%s (%d-%d)" % ( __language__( 3 ), startno, endno, ), iconImage=icon, thumbnailImage=thumbnail )
                    # add the folder item to our media list
                    ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), url=url, listitem=listitem, isFolder=True, totalItems=total_items )
                # if we are on page 2 or more, we add our previous page folder
                if ( page > 1 ):
                    # calculate the starting video
                    startno = ( page - 2 ) * perpage + 1
                    # calculate the ending video
                    endno = startno + perpage - 1
                    # create the callback url
                    url = '%s?title=%s&category=%s&page=%d&vq=%s&username=%s&cat=%s&orderby=%s&related=%s&issearch=0&update_listing=%d' % ( sys.argv[0], quote_plus( repr( self.args.title ) ), repr( self.args.category ), page - 1, quote_plus( repr( self.args.vq ) ), quote_plus( repr( self.args.username ) ), quote_plus( repr( self.args.cat ) ), repr( self.args.orderby ), repr( self.args.related ), True, )
                    # TODO: get rid of self.BASE_PLUGIN_THUMBNAIL_PATH
                    # we set the thumb so XBMC does not try and cache the previous pictures
                    thumbnail = os.path.join( self.BASE_PLUGIN_THUMBNAIL_PATH, "previous.png" )
                    # set the default icon
                    icon = "DefaultFolder.png"
                    # only need to add label and icon, setInfo() and addSortMethod() takes care of label2
                    listitem=xbmcgui.ListItem( label="%s (%d-%d)" % ( __language__( 3 ), startno, endno, ), iconImage=icon, thumbnailImage=thumbnail )
                    # add the folder item to our media list
                    ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), url=url, listitem=listitem, isFolder=True, totalItems=total_items )
                # set our thumbnail for queries
                self.query_thumbnail = videos[ 0 ][ "media$group" ][ "media$thumbnail" ][ -1 ][ "url" ]
                # enumerate through the list of pictures and add the item to the media list
                for video in videos:
                    # only add videos with an embeddable video
                    if ( video[ "media$group" ].has_key( "media$player" ) ):
                        # create the title, we use video title and author (exec is a hack for unescaping \u#### characters)
                        exec 'title = u"%s"' % ( unicode( video[ "title" ][ "$t" ].replace( '"', '\\"' ), encoding, "replace" ), )
                        # set the director with author (exec is a hack for unescaping \u#### characters)
                        exec 'director = u"%s"' % ( unicode( video[ "author" ][ 0 ][ "name" ][ "$t" ].replace( '"', '\\"' ), encoding, "replace" ), )
                        # thumbnail url
                        thumbnail_url = video[ "media$group" ][ "media$thumbnail" ][ -1 ][ "url" ]
                        # plot
                        try:
                            # we need to replace \n and \r as it messes up our exec hack (exec is a hack for unescaping \u#### characters)
                            exec 'plot = u"%s"' % ( unicode( video[ "media$group" ][ "media$description" ][ "$t" ].replace( '"', '\\"' ).replace( "\n", "\\n" ).replace( "\r", "\\r" ), encoding, "replace" ), )
                        except:
                            plot = __language__( 30904 )    
                        # format runtime as 00:00
                        runtime = int( video[ "media$group" ][ "yt$duration" ][ "seconds" ] )
                        # video runtime
                        if ( runtime ):
                            runtime = "%02d:%02d" % ( int( runtime / 60 ), runtime % 60, )
                        else:
                            runtime = ""
                        # viewer rating
                        try:
                            rating = float( video[ "gd$rating" ][ "average" ] )
                        except:
                            rating = 0.0
                        # times viewed
                        try:
                            count = int( video[ "yt$statistics" ][ "viewCount" ] )
                        except:
                            count = 0
                        # genre
                        genre = video[ "media$group" ][ "media$category" ][ 0 ][ "$t" ]
                        # updated date
                        date = "%s-%s-%s" % ( video[ "updated" ][ "$t" ][ 8 : 10 ], video[ "updated" ][ "$t" ][ 5 : 7 ], video[ "updated" ][ "$t" ][ : 4 ], )
                        # video url
                        exec 'video_url = u"%s"' % ( unicode( video[ "media$group" ][ "media$player" ][ 0 ][ "url" ], encoding ), )
                        # construct our url
                        url = "%s?category='play_video'&video_url=%s&releated=%s&update_listing=%d" % ( sys.argv[0], quote_plus( repr( video_url ) ), repr( video[ "id" ][ "$t" ].split( "/" )[ -1 ] ), False, )
                        # set the default icon
                        icon = "DefaultVideo.png"
                        # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
                        listitem=xbmcgui.ListItem( label=title, iconImage=icon, thumbnailImage=thumbnail_url )
                        # add the different infolabels we want to sort by
                        listitem.setInfo( type="Video", infoLabels={ "Title": title, "Director": director, "Duration": runtime, "Plot": plot, "Rating": rating, "Genre": genre, "Count": count, "Date": date } )
                        # set isplayable property
                        listitem.setProperty( "IsPlayable", "true" )
                        # set context menu items
                        cm = []
                        # add queue video
                        cm += [ ( __language__( 30504 ), "XBMC.Action(Queue)", ) ]
                        # add related videos
                        cm += [ ( __language__( 30500 ), "Container.Update(%s?title=%s&category='related'&page=1&vq=''&username=''&cat=''&orderby='relevance'&related=%s&issearch=False&update_listing=False)" % ( sys.argv[0], repr( __language__( 30968 ) ), repr( video[ "id" ][ "$t" ].split( "/" )[ -1 ] ), ), ) ]
                        # add author videos
                        cm += [ ( __language__( 30507 ) % ( director, ), "Container.Update(%s?title=%s&category='users__uploads'&page=1&vq=''&username=%s&cat=''&orderby='relevance'&related=''&issearch=False&update_listing=False)" % ( sys.argv[0], quote_plus( repr( director ) ), quote_plus( repr( director ) ), ), ) ]
                        # if download path set, add download item
                        if ( self.settings[ "download_path" ] != "" ):
                            cm += [ ( __language__( 30501 ), "XBMC.RunPlugin(%s?category='download_video'&video_url=%s)" % ( sys.argv[0], quote_plus( repr( video_url ) ), ), ) ]
                        # add movie info
                        cm += [ ( __language__( 30502 ), "XBMC.Action(Info)", ) ]
                        # add to favourites
                        if ( self.args.category != "my_favorites" and self.authkey ):
                            cm += [ ( __language__( 30503 ), "XBMC.RunPlugin(%s?category='add__favorite'&video_id=%s&update_listing=False)" % ( sys.argv[0], repr( video[ "id" ][ "$t" ].split( "/" )[ -1 ] ), ) ) ]
                        else:
                            # find the edit url
                            for link in video["link"]:
                                # this is the edit url, so set the context menu item
                                if ( link["rel"] == "edit" ):
                                    # set url using this hack to clean the result (exec is a hack for unescaping \u#### characters)
                                    exec 'edit_url = u"%s"' % ( unicode( link[ "href" ], encoding ), )
                                    # add context menu item
                                    cm += [ ( __language__( 30506 ), "XBMC.RunPlugin(%s?category='delete__favorite'&edit_url=%s&update_listing=False)" % ( sys.argv[0], quote_plus( repr( edit_url ) ), ), ) ]
                        # add now playing
                        cm += [ ( __language__( 30505 ), "XBMC.ActivateWindow(10028)", ) ]
                        # add context menu items
                        listitem.addContextMenuItems( cm, replaceItems=True )
                        # add the video to the media list
                        ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), url=url, listitem=listitem, isFolder=False, totalItems=total_items )
                        # if user cancels, call raise to exit loop
                        if ( not ok ): raise
                if ( spell_vq ):
                    self.args.username = ( "", spell_vq, )[ self.args.issearch == 2 ]
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            ok = False
        # if successful and user did not cancel, add all the required sort methods
        if ( ok ):
            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RATING )
            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_PROGRAM_COUNT )
            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
            xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
            # set content
            xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content="movies" )
            # set our plugin category
            xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=self.args.title )
            # if skin has fanart image use it
            fanart_image = os.path.join( sys.modules[ "__main__" ].__plugin__, self.args.category + "-fanart.png" )
            if ( xbmc.skinHasImage( fanart_image ) ):
                xbmcplugin.setPluginFanart( handle=int( sys.argv[ 1 ] ), image=fanart_image )
            # set our fanart from user setting
            elif ( self.settings[ "fanart_image" ] ):
                xbmcplugin.setPluginFanart( handle=int( sys.argv[ 1 ] ), image=self.settings[ "fanart_image" ] )
        return ok, total_items

    def _get_keyboard( self, default="", heading="", hidden=False ):
        """ shows a keyboard and returns a value """
        keyboard = xbmc.Keyboard( default, heading, hidden )
        keyboard.doModal()
        if ( keyboard.isConfirmed() ):
            return unicode( keyboard.getText(), "utf-8" )
        return default
