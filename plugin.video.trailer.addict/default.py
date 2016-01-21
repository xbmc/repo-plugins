
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib, re, string, sys, os, buggalo
import simplejson as json
import hashlib
import unwise

plugin = 'Trailer Addict'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '06-01-2013'
__version__ = '2.0.9'
settings = xbmcaddon.Addon( id = 'plugin.video.trailer.addict' )
buggalo.SUBMIT_URL = 'http://www.xbmc.byethost17.com/submit.php'
dbg = False
dbglevel = 3
import CommonFunctions
common = CommonFunctions
common.plugin = plugin + ' ' + __version__

from addonfunc import addListItem, playListItem, getUrl, getPage, setViewMode, getParameters, retry, start_download
from metahandler import metahandlers

next_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )
search_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'search_icon.png' )
clapperboard_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'clapperboard.png' )
film_reel_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'film_reel.png' )
oscar_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'oscar.png' )
popcorn_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'popcorn.png' )
poster_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'poster.png' )
library_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'library.png' )
icon_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'icon.png' )

def clean( name ):
    list = [ ( '&amp;', '&' ), ( '&quot;', '"' ), ( '<em>', '' ), ( '</em>', '' ), ( '&#39;', '\'' ) ]
    for search, replace in list:
        name = name.replace( search, replace )
    return name

def _alpha(_arg1):
    return 'abcdefghijklmnopqrstuvwyxz'[_arg1:_arg1 + 1]

@retry((IndexError, TypeError))
def find_trailers( url, name, page, library ):
    save_name = name
    save_page = page
    data = getUrl( url ).decode('ascii', 'ignore')
    link_thumb = re.compile( '<a href="(.+?)"><img src="(.+?)" name="thumb' ).findall( data )
    thumbs = re.compile( 'img src="/psize\.php\?dir=(.+?)" style' ).findall( data )
    if len( thumbs ) == 0:
        thumb = "DefaultVideo.png"
    else:
        thumb = 'http://www.traileraddict.com/' + thumbs[0]
    title = re.compile( '<div class="abstract"><h2><a href="(.+?)">(.+?)</a></h2><br />', re.DOTALL ).findall( data )
    trailers = re.compile( '<dl class="dropdown">(.+?)</dl>', re.DOTALL ).findall( data )
    if len(title) == 0 and len(trailers) == 0:
        list = common.parseDOM(data, "div", attrs = { "class": "info" })
        header = common.parseDOM(data, "div", attrs = { "class": "trailerheader" })
        nexturl = common.parseDOM(header, "a", attrs = { "title": "Next Page" }, ret = "href")
        totalItems = len(list)
        if totalItems == 0:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(plugin, settings.getLocalizedString( 30012 ))
            ok = dialog.ok(plugin, settings.getLocalizedString( 30051 ))
            buggalo.addExtraData('url', url)
            buggalo.addExtraData('name', name)
            raise Exception('find_trailers Error A')
            return
        for video in list:
            h2 = common.parseDOM(video, "h2")
            title = common.parseDOM(h2, "a")[0]
            url = 'http://www.traileraddict.com' + common.parseDOM(h2, "a", ret = "href")[0]
            thumb = 'http://www.traileraddict.com' + common.parseDOM(video, "img", attrs = { "class": "dimmer" }, ret = "src")[0].replace('-t.jpg','.jpg')
            #infoLabels = { "Title": title, "Plot": save_name + ' (' + clean( title ) + ')' }
            cm = []
            run = sys.argv[0] + '?' + urllib.urlencode({ 'mode': '5', 'name': save_name + ' (' + clean( title ) + ')', 'url': url, 'download': 'True' })
            cm.append( (settings.getLocalizedString(30059), "XBMC.RunPlugin(%s)" % run) )
            cm.append( (settings.getLocalizedString(30014), "XBMC.RunPlugin(plugin://plugin.video.couchpotato_manager/movies/add?title=%s)" % save_name) )
            u = { 'mode': '5', 'name': save_name + ' (' + clean( title ) + ')', 'url': url }
            addListItem(label = clean( title ), image = thumb, url = u, isFolder = False, totalItems = totalItems, infoLabels = False, cm = cm)
        if len(nexturl) > 0:
            url = 'http://www.traileraddict.com' + nexturl[0]
            u = { 'mode': '4', 'name': save_name, 'url': url, 'page': str( int( save_page ) + 1 ) }
            addListItem(label = '[Next Page (' + str( int( save_page ) + 2 ) + ')]', image = next_thumb, url = u, isFolder = True, totalItems = 0, infoLabels = False)
        xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
        setViewMode("502", "movies")
        xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
        return
    item_count = 0
    if len( trailers ) > 0:
        check1 = re.compile( '<a href="(.+?)"><img src="\/images\/usr\/arrow\.png" border="0" style="float:right;" \/>(.+?)</a>' ).findall( trailers[0] )
        check2 = re.compile( '<a href="(.+?)"( style="(.*?)")?>(.+?)<br />' ).findall( trailers[0] )
        totalItems = len( check1 )
        totalItems2 = len( check2 )
        if totalItems > 0:
            url_title = check1
            if library == True:
                return url_title[0][0]
            for url, title in url_title:
                url = 'http://www.traileraddict.com' + url
                cm = []
                run = sys.argv[0] + '?' + urllib.urlencode({ 'mode': '5', 'name': save_name + ' (' + clean( title ) + ')', 'url': url, 'download': 'True' })
                cm.append( (settings.getLocalizedString(30059), "XBMC.RunPlugin(%s)" % run) )
                cm.append( (settings.getLocalizedString(30014), "XBMC.RunPlugin(plugin://plugin.video.couchpotato_manager/movies/add?title=%s)" % save_name) )
                infoLabels = { "Title": title, "Plot": save_name + ' (' + clean( title ) + ')' }
                u = { 'mode': '5', 'name': save_name + ' (' + clean( title ) + ')', 'url': url }
                addListItem(label = clean( title ), image = thumb, url = u, isFolder = False, totalItems = totalItems, infoLabels = False, cm = cm)
            xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
            setViewMode("502", "movies")
            xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
        elif totalItems2 > 0:
            url_title = check2
            if library == True:
                return url_title[0][0]
            for url, trash1, trash2, title in url_title:
                url = 'http://www.traileraddict.com' + url
                #infoLabels = { "Title": title, "Plot": save_name + ' (' + clean( title ) + ')' }
                cm = []
                run = sys.argv[0] + '?' + urllib.urlencode({ 'mode': '5', 'name': save_name.decode('ascii', 'ignore') + ' (' + clean( title ) + ')', 'url': url, 'download': 'True' })
                cm.append( (settings.getLocalizedString(30059), "XBMC.RunPlugin(%s)" % run) )
                cm.append( (settings.getLocalizedString(30014), "XBMC.RunPlugin(plugin://plugin.video.couchpotato_manager/movies/add?title=%s)" % save_name.decode('ascii', 'ignore')) )
                u = { 'mode': '5', 'name': save_name.decode('ascii', 'ignore') + ' (' + clean( title ) + ')', 'url': url }
                addListItem(label = clean( title ), image = thumb, url = u, isFolder = False, totalItems = totalItems2, infoLabels = False, cm = cm)
            xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
            setViewMode("502", "movies")
            xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
        else:
            # dia = xbmcgui.Dialog()
            # ok = dia.ok(plugin, settings.getLocalizedString(30006) )
            # ok = dia.ok(plugin, settings.getLocalizedString( 30051 ))
            # buggalo.addExtraData('url', url)
            # buggalo.addExtraData('name', save_name)
            # raise Exception('find_trailers Error 2')
            # xbmc.executebuiltin('Notification('+plugin+',Only video clips were found!,5000,'+icon_thumb+')')
            list = common.parseDOM(data, "div", attrs = { "class": "info" })
            header = common.parseDOM(data, "div", attrs = { "class": "trailerheader" })
            nexturl = common.parseDOM(header, "a", attrs = { "title": "Next Page" }, ret = "href")
            totalItems = len(list)
            if totalItems == 0:
                dialog = xbmcgui.Dialog()
                ok = dialog.ok(plugin, settings.getLocalizedString( 30012 ))
                ok = dialog.ok(plugin, settings.getLocalizedString( 30051 ))
                buggalo.addExtraData('url', url)
                buggalo.addExtraData('name', name)
                raise Exception('find_trailers Error B')
                return
            for video in list:
                h2 = common.parseDOM(video, "h2")
                title = common.parseDOM(h2, "a")[0]
                url = 'http://www.traileraddict.com' + common.parseDOM(h2, "a", ret = "href")[0]
                thumb = 'http://www.traileraddict.com' + common.parseDOM(video, "img", attrs = { "class": "dimmer" }, ret = "src")[0].replace('-t.jpg','.jpg')
                #infoLabels = { "Title": title, "Plot": save_name + ' (' + clean( title ) + ')' }
                cm = []
                run = sys.argv[0] + '?' + urllib.urlencode({ 'mode': '5', 'name': save_name + ' (' + clean( title ) + ')', 'url': url, 'download': 'True' })
                cm.append( (settings.getLocalizedString(30059), "XBMC.RunPlugin(%s)" % run) )
                cm.append( (settings.getLocalizedString(30014), "XBMC.RunPlugin(plugin://plugin.video.couchpotato_manager/movies/add?title=%s)" % save_name) )
                u = { 'mode': '5', 'name': save_name + ' (' + clean( title ) + ')', 'url': url }
                addListItem(label = clean( title ), image = thumb, url = u, isFolder = False, totalItems = totalItems, infoLabels = False, cm = cm)
            if len(nexturl) > 0:
                url = 'http://www.traileraddict.com' + nexturl[0]
                u = { 'mode': '4', 'name': save_name, 'url': url, 'page': str( int( save_page ) + 1 ) }
                addListItem(label = '[Next Page (' + str( int( save_page ) + 2 ) + ')]', image = next_thumb, url = u, isFolder = True, totalItems = 0, infoLabels = False)
            xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
            setViewMode("502", "movies")
            xbmcplugin.endOfDirectory( int( sys.argv[1] ) )
    else:
        totalItems = len(link_thumb)
        for url, thumb2 in link_thumb:
            if clean( title[item_count][1] ).find( 'Trailer' ) > 0: 
                url = 'http://www.traileraddict.com' + url
                cm = []
                run = sys.argv[0] + '?' + urllib.urlencode({ 'mode': '5', 'name': save_name + ' (' + clean( title[item_count][1] ) + ')', 'url': url, 'download': 'True' })
                cm.append( (settings.getLocalizedString(30059), "XBMC.RunPlugin(%s)" % run) )
                cm.append( (settings.getLocalizedString(30014), "XBMC.RunPlugin(plugin://plugin.video.couchpotato_manager/movies/add?title=%s)" % save_name) )
                infoLabels = { "Title": title[item_count][1], "Plot": save_name + ' (' + clean( title[item_count][1] ) + ')' }
                u = { 'mode': '5', 'name': save_name + ' (' + clean( title[item_count][1] ) + ')', 'url': url }
                addListItem(label = clean( title[item_count][1] ), image = thumb, url = u, isFolder = False, totalItems = totalItems, infoLabels = False, cm = cm)
            item_count = item_count + 1
        xbmcplugin.addSortMethod( handle = int( sys.argv[1] ), sortMethod = xbmcplugin.SORT_METHOD_NONE )
        setViewMode("502", "movies")
        xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry((IndexError, TypeError))
def build_main_directory():
    main=[
        ( settings.getLocalizedString(30000), search_thumb, '0' ),
        ( settings.getLocalizedString(30001), film_reel_thumb, '1' ),
        ( settings.getLocalizedString(30002), clapperboard_thumb, '2' ),
        ( settings.getLocalizedString(30003), oscar_thumb, '3' ),
        #( settings.getLocalizedString(30004), popcorn_thumb, '6' ),
        ( settings.getLocalizedString(30015), library_thumb, '7' )
        ]
    for name, thumbnailImage, mode in main:
        listitem = xbmcgui.ListItem( label = name, iconImage = "DefaultVideo.png", thumbnailImage = thumbnailImage )
        u = { 'mode': mode, 'name': name }
        addListItem(label = name, image = thumbnailImage, url = u, isFolder = True, totalItems = 0, infoLabels = False)
    build_features_list(1)
        
@retry((IndexError, TypeError))
def build_features_list(save_page):
    metaget=metahandlers.MetaData()
    form_data = {'page': save_page}
    data = getUrl( 'http://www.traileraddict.com/ajax/features_home.php', form_data=form_data )
    movie_info = re.compile('class="featured_box[ sp rb]*">(.+?)</a>[\\r\\n\\t]+</div>', re.DOTALL).findall(data)
    for movie in movie_info:
        url_thumb_x_title = re.compile( '<a href="(.+?)" class="movie_img" title="(.+?)"><img alt=".+?" src="(.+?)" />' ).findall( movie )
        totalItems = len(url_thumb_x_title)
        for url, title, thumb in url_thumb_x_title:
            title = title.rsplit( ' - ' )
            name1 = clean( title[0] )
            if len( title ) > 1:
                name2 = clean( title[0] ) + ' (' + clean( title[1] ) + ')'
            else:
                name2 = clean( title[0] )
            url = 'http://www.traileraddict.com' + url
            thumb = 'http:' + thumb
            cm = []
            run = sys.argv[0] + '?' + urllib.urlencode({ 'mode': '5', 'name': name2, 'url': url, 'download': 'True' })
            cm.append( (settings.getLocalizedString(30059), "XBMC.RunPlugin(%s)" % run) )
            cm.append( (settings.getLocalizedString(30014), "XBMC.RunPlugin(plugin://plugin.video.couchpotato_manager/movies/add?title=%s)" % name1) )
            cm.append(('Show Information', 'XBMC.Action(Info)'))
            u = { 'mode': '5', 'name': name2, 'url': url }
            
            #Try to clean up the name as best we can before grabbing meta data
            scrape_name = name1.lower().replace('theatrical trailer','').replace('feature trailer','').replace('international trailer','').replace('final trailer','').replace('red band', '').replace('feature red band', '').replace('international red band ', '').replace('trailer', '')
            meta=metaget.get_meta('movie', scrape_name)
            meta['title'] = name1
            meta['trailer'] = ''
            
            addListItem(label = name1, image = thumb, url = u, isFolder = False, totalItems = totalItems, infoLabels = meta, cm = cm)
    if save_page < 94:
        u = { 'mode': '6', 'page': str( int( save_page ) + 1 ) }
        addListItem(label = '[Next Page (' + str( int( save_page ) + 1 ) + ')]', image = next_thumb, url = u, isFolder = True, totalItems = 0, infoLabels = False)
    xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
    setViewMode("500", "movies")
    xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry((IndexError, TypeError)) 
def build_search_directory(name, url):
    if url != 'library':
        keyboard = xbmc.Keyboard( '', settings.getLocalizedString(30007) )
        keyboard.doModal()
        if ( keyboard.isConfirmed() == False ):
            return
        search_string = keyboard.getText().replace( ' ', '+' )
        if len( search_string ) == 0:
            return
    else:
        search_string = name
    data = getUrl( 'http://www.traileraddict.com/search.php?q=' + search_string )
    image = re.compile( '<center>\r\n<div style="background:url\((.*?)\);" class="searchthumb">', re.DOTALL ).findall( data )
    link_title = re.compile( '</div><a href="/tags/(.*?)">(.*?)</a><br />' ).findall( data )
    if len( link_title ) == 0:
        if url == 'library':
            return None
        dialog = xbmcgui.Dialog()
        ok = dialog.ok( plugin , settings.getLocalizedString(30009) + search_string + '.\n' + settings.getLocalizedString(30010) )
        build_main_directory()
        return
    item_count=0
    totalItems = len(link_title)
    if url == 'library':
        return link_title[0][0]
    for url, title in link_title:
        url = 'http://www.traileraddict.com/tags/' + url
        thumb = 'http://www.traileraddict.com' + image[item_count].replace( '/pthumb.php?dir=', '' ).replace( '\r\n', '' )
        u = { 'mode': '4', 'name': clean( title ), 'url': url }
        addListItem(label = clean( title ), image = thumb, url = u, isFolder = True, totalItems = totalItems, infoLabels = False)
        item_count = item_count + 1
    xbmcplugin.addSortMethod( handle = int( sys.argv[1] ), sortMethod = xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry((IndexError, TypeError))
def build_film_database_directory():
    keyboard = xbmc.Keyboard( '', settings.getLocalizedString(30011) )
    keyboard.doModal()
    search_string = keyboard.getText().rsplit(' ')[0]
    if ( (keyboard.isConfirmed() == False) or (len( search_string ) == 0) ):
        return
    data = getUrl( 'http://www.traileraddict.com/thefilms/' + search_string )
    link_title = re.compile( '<img src="/images/arrow2.png" class="arrow"> <a href="(.+?)">(.+?)</a>' ).findall( data )
    if len( link_title ) == 0:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok( plugin , settings.getLocalizedString(30009) + search_string + '.\n' + settings.getLocalizedString(30013) )
        build_main_directory()
        return
    item_count=0
    totalItems = len(link_title)
    for url, title in link_title:
        url = 'http://www.traileraddict.com/' + url
        u = { 'mode': '4', 'name': clean( title ), 'url': url }
        addListItem(label = clean( title ), image = poster_thumb, url = u, isFolder = True, totalItems = totalItems, infoLabels = False)
        item_count = item_count + 1
    xbmcplugin.addSortMethod( handle = int( sys.argv[1] ), sortMethod = xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry((IndexError, TypeError))
def build_coming_soon_directory():
    data = getUrl( 'http://www.traileraddict.com/comingsoon' )
    margin_right = re.compile( '<div style=\"float:right(.*?)<div style="float:left; width:300px;', re.DOTALL ).findall( data )[0]
    margin_left = re.compile( '<div style=\"float:left; width:300px;(.*?)<div style="clear:both;">', re.DOTALL ).findall( data )[0]
    link_title = re.compile( '<img src="/images/arrow2.png" class="arrow"> <a href="(.+?)">(.+?)</a>' ).findall( margin_left )
    item_count = 0
    totalItems = len(link_title)
    for url, title in link_title:
        url = 'http://www.traileraddict.com/' + url
        u = { 'mode': '4', 'name': clean( title ), 'url': url }
        addListItem(label = clean( title ), image = poster_thumb, url = u, isFolder = True, totalItems = totalItems, infoLabels = False)
        item_count = item_count + 1
    link_title = re.compile( '<img src="/images/arrow2.png" class="arrow"> <a href="(.+?)">(.+?)</a>' ).findall( margin_right )
    item_count = 0
    totalItems = len(link_title)
    for url, title in link_title:
        url = 'http://www.traileraddict.com/' + url
        u = { 'mode': '4', 'name': clean( title ), 'url': url }
        addListItem(label = clean( title ), image = poster_thumb, url = u, isFolder = True, totalItems = totalItems, infoLabels = False)
        item_count = item_count + 1
    xbmcplugin.addSortMethod( handle = int( sys.argv[1] ), sortMethod = xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry((IndexError, TypeError))
def build_top_150_directory():
    data = getUrl( 'http://www.traileraddict.com/top150' )
    link_title_views = re.compile( '<li><a href="(.+?)" class="m_title">(.+?)</a></li>' ).findall( data )
    item_count = 75
    for list in range( 0, 149 ):
        if item_count == 149:
            item_count = 0
        title = link_title_views[item_count][1]
        url = 'http://www.traileraddict.com' + link_title_views[item_count][0]
        u = { 'mode': '4', 'name': clean( title.rsplit(' (')[0] ), 'url': url }
        addListItem(label = clean( title ), image = poster_thumb, url = u, isFolder = True, totalItems = 150, infoLabels = False)
        item_count = item_count + 1
    xbmcplugin.addSortMethod( handle = int( sys.argv[1] ), sortMethod = xbmcplugin.SORT_METHOD_NONE )
    xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry((IndexError, TypeError))
def build_featured_directory( page ):
    save_page = page
    data = getUrl( 'http://www.traileraddict.com/attraction/' + str( int( page ) + 1) )
    url_thumb_x_title = re.compile( '<a href="/trailer/(.+?)"><img src="(.+?)" border="0" alt="(.+?)" title="(.+?)" style="margin:8px 5px 2px 5px;"></a>' ).findall( data )
    totalItems = len(url_thumb_x_title)
    for url, thumb, x, title in url_thumb_x_title:
        title = title.rsplit( ' - ' )
        name1 = clean( title[0] )
        if len( title ) > 1:
            name2 = clean( title[0] ) + ' (' + clean( title[1] ) + ')'
        else:
            name2 = clean( title[0] )
        url = 'http://www.traileraddict.com/trailer/' + url
        thumb = 'http://www.traileraddict.com' + thumb
        cm = []
        run = sys.argv[0] + '?' + urllib.urlencode({ 'mode': '5', 'name': name2, 'url': url, 'download': 'True' })
        cm.append( (settings.getLocalizedString(30059), "XBMC.RunPlugin(%s)" % run) )
        cm.append( (settings.getLocalizedString(30014), "XBMC.RunPlugin(plugin://plugin.video.couchpotato_manager/movies/add?title=%s)" % name1) )
        u = { 'mode': '5', 'name': name2, 'url': url }
        addListItem(label = name1, image = thumb, url = u, isFolder = False, totalItems = totalItems, infoLabels = False, cm = cm)
    u = { 'mode': '6', 'page': str( int( save_page ) + 1 ) }
    addListItem(label = '[ Next Page (' + str( int( save_page ) + 2 ) + ') ]', image = next_thumb, url = u, isFolder =  True, totalItems = 0, infoLabels = False)
    xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
    setViewMode("500", "movies")
    xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry((IndexError, TypeError)) 
def play_video( url, name, download ):
    data = getUrl( url )
    
    title = re.search('<meta itemprop="name" content="(.+?)">', data)
    thumb = re.search('<meta itemprop="thumbnailUrl" content="(.+?)">', data)

    trailerId = re.search( '<meta itemprop="embedUrl" content=".+traileraddict\.com/emd/(.+?)\?id=.+?">', data)
    
    if trailerId:
        data = getUrl('http://v.traileraddict.com/%s' % trailerId.group(1))
        data = unwise.unwise_process(data)
        video_urls = re.compile("file:[\\\]*'(.+?)'").findall(data)
    else:
        return
    
    if title:
        name = urllib.unquote_plus(title.group(1)) + ' (' + settings.getLocalizedString(30017) + ')'
    if thumb:
        if thumb.group(1) == 'http://www.traileraddict.com/images/noembed-removed.png':
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(plugin, settings.getLocalizedString( 30012 ))
            return
    if settings.getSetting('streamQuality') == '1':
        url = video_urls[1]
    else:
        url = video_urls[0]
    url = url.replace( '%3A', ':').replace( '%2F', '/' ).replace( '%3F', '?' ).replace( '%3D', '=' ).replace( '%26', '&' ).replace( '%2F', '//' ).strip()
    infoLabels = { "Title": name , "Studio": plugin }
    if download == 'True':
        start_download(name, str(url))
    else:
        playListItem(label = name, image = xbmc.getInfoImage( "ListItem.Thumb" ), path = str(url), infoLabels = infoLabels, PlayPath = False)

@retry(ValueError)      
def getMovieLibrary():
    try:
        if common.getXBMCVersion() >= 12.0:
            properties = ['year', 'imdbnumber', 'thumbnail', 'plot', 'dateadded', 'rating']
        else:
            properties = ['year', 'imdbnumber', 'thumbnail', 'plot', 'rating']
    except:
        properties = ['year', 'imdbnumber', 'thumbnail', 'plot', 'rating']
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetMovies', 'params':{'properties': properties, "sort": { "order": "ascending", "method": "label", "ignorearticle": True } }, "id": "libMovies"})
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    if 'error' in result:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(plugin, settings.getLocalizedString( 30018 ))
        build_main_directory()
        return  
    if (result['result']['limits']['total'] == 0):
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(plugin, settings.getLocalizedString( 30016 ))
        build_main_directory()
        return
    totalItems = len(result['result']['movies'])
    for movie in result['result']['movies']:
        label = movie['label'].encode('ascii', 'ignore')
        plot = movie['plot'].encode('ascii', 'ignore')
        if 'dateadded' in movie:
            day = movie['dateadded'].split(' ')[0].split('-')
            date = day[2] + '.' + day[1] + '.' + day[0]
        else:
            date = '0000.00.00'
        thumbnail = movie['thumbnail']
        year = movie['thumbnail']
        url = movie['imdbnumber'].rsplit('tt')
        if len(url) == 2:
            url = url[1]
        else:
            url = '1'
        listitem = xbmcgui.ListItem( label = label, iconImage = thumbnail, thumbnailImage = thumbnail )
        u = { 'mode': '8', 'name': label, 'url': url }
        cm = []
        run = sys.argv[0] + '?' + urllib.urlencode({ 'mode': '8', 'name': label, 'url': url, 'download': 'True' })
        cm.append( (settings.getLocalizedString(30059), "XBMC.RunPlugin(%s)" % run) )
        infoLabels = { "Title": label, "Plot": plot, "date": date, "Year": movie['year'], "Rating": movie['rating'] }
        addListItem(label = label, image = thumbnail, url = u, isFolder = False, totalItems = totalItems, infoLabels = infoLabels, cm = cm)
    xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_TITLE )
    xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_VIDEO_YEAR )
    xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_VIDEO_RATING )
    setViewMode("500", "movies")
    xbmcplugin.endOfDirectory( int( sys.argv[1] ) )

@retry(TypeError)   
def library_trailers( url, name, page, download ):
    url = 'http://api.traileraddict.com/?imdb=' + url
    data = getUrl( url )
    slug = re.compile( '<link>http:\/\/www\.traileraddict\.com\/trailer\/(.+?)\/' ).findall( data )
    if len(slug):
        slug = slug[0]
    else:
        slug = build_search_directory(name, 'library')
    if slug == None:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(plugin, settings.getLocalizedString( 30019) + name + '.')
        return
    url = 'http://www.traileraddict.com/tags/' + slug
    url = find_trailers( url, name, page, True )
    url = 'http://www.traileraddict.com' + url
    play_video( url, name + ' (' + settings.getLocalizedString(30017) + ')', download )

params = getParameters(sys.argv[2])
url = None
name = None
mode = None
download = None
library = False
page = 0

try:
    url = urllib.unquote_plus( params['url'] )
except:
    pass
try:
    name = urllib.unquote_plus( params['name'] )
except:
    pass
try:
    download = urllib.unquote_plus( params['download'] )
except:
    pass
try:
    mode = int( params['mode'] )
except:
    pass
try:
    page = int( params['page'] )
except:
    pass

try:
    if mode == None:
        build_main_directory()
    elif mode == 0:
        build_search_directory(name, url)
    elif mode == 1:
        build_film_database_directory()
    elif mode == 2:
        build_coming_soon_directory()
    elif mode == 3:
        build_top_150_directory()
    elif mode == 4:
        find_trailers( url, name, page, library )
    elif mode == 5:
        play_video( url, name, download )
    elif mode == 6:
        build_features_list( page )
    elif mode == 7:
        getMovieLibrary()
    elif mode == 8:
        library_trailers( url, name, page, download )
except Exception:
    buggalo.onExceptionRaised()
