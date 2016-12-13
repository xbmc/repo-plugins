# -*- coding: UTF-8 -*-
import sys
import os
import urllib
import urlparse
import urllib2
import re
import threading
import Queue
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

stream_url = {
    '1080p': 'http://rfe-lh.akamaihd.net/i/rfe_tvmc5@383630/index_1080_av-p.m3u8',
    '720p': 'http://rfe-lh.akamaihd.net/i/rfe_tvmc5@383630/index_0720_av-p.m3u8',
    '540p': 'http://rfe-lh.akamaihd.net/i/rfe_tvmc5@383630/index_0540_av-p.m3u8',
    '404p': 'http://rfe-lh.akamaihd.net/i/rfe_tvmc5@383630/index_0404_av-p.m3u8',
    '288p': 'http://rfe-lh.akamaihd.net/i/rfe_tvmc5@383630/index_0288_av-p.m3u8'
}
video_url = {
    '720p': '/index_2_av.m3u8',
    '360p': '/index_1_av.m3u8',
    '270p': '/index_0_av.m3u8'
}
main_menu = ([
    [30003, 30004, 'lastvids+next', 	'folder',       '/z/17317.html'],   #Broadcasts
    [30005, 30006, 'tvshows',			'folder',       ''],			    #TV Shows
    [30007, 30008, 'lastvids+next', 	'folder',       '/z/17192.html'],   #All Videos
    [30009, 30010, 'lastvids+next', 	'folder',       '/z/17226.html'],   #Daily Shoots
    [30011, 30012, 'lastvids+next', 	'folder',       '/z/17318.html'],   #Reportages
    [30013, 30014, 'lastvids+next', 	'folder',       '/z/17319.html']    #Interviews
])
tvshows = ([
    [30031, 30032, 'lastvids+archive',  'olevski',	    '/z/20333.html'],
    [30033, 30034, 'lastvids+archive',  'nveurope',     '/z/18657.html'],
    [30035, 30036, 'lastvids+archive',  'nvasia', 	    '/z/17642.html'],
    [30037, 30038, 'lastvids+archive',  'nvamerica',    '/z/20347.html'],
    [30039, 30040, 'lastvids+archive',  'oba', 		    '/z/20366.html'],
    [30041, 30042, 'lastvids+archive',  'itogi', 	    '/z/17499.html'],
    [30043, 30044, 'lastvids+archive',  'week',		    '/z/17498.html'],
    [30045, 30046, 'lastvids+archive',  'baltia', 	    '/z/20350.html'],
    [30047, 30048, 'lastvids+archive',  'bisplan', 	    '/z/20354.html'],
    [30049, 30050, 'lastvids+archive',  'unknownrus',   '/z/20331.html'],
    [30051, 30052, 'lastvids+archive',  'guests', 	    '/z/20330.html']
])
default_view = {
    'skin.confluence':
        {'main_menu': '50', 'tvshows': '500', 'lastvids+next': '515', 'lastvids+archive': '515',
         'allvids_archive': '51', 'video': '515'},
    'skin.aeon.nox.5':
        {'main_menu':'50', 'tvshows': '50', 'lastvids+next': '510', 'lastvids+archive': '510',
         'allvids_archive': '50', 'video': '510'},
    'skin.estuary':
        {'main_menu': '55', 'tvshows': '500', 'lastvids+next': '502', 'lastvids+archive': '502',
         'allvids_archive': '55', 'video': '502'}
}

NUM_OF_PARALLEL_REQ = 6    #queue size
MAX_REQ_TRIES = 3
MAX_ITEMS_TO_SHOW = 12
video_pages_buffer = [None] * 30

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode', [None])[0]
folder_url = args.get('folderurl', [None])[0]
folder_title = args.get('title', [None])[0]
folder_level = int(args.get('level', '0')[0])
folder_name = args.get('name', [None])[0]

site_url = 'http://www.currenttime.tv'
addon_name = 'plugin.video.currenttime.tv'
addon = xbmcaddon.Addon(addon_name)
addon_icon = addon.getAddonInfo('icon')

xbmcplugin.setContent(addon_handle, 'tvshows')  # !!!


def build_url(query):
    """builds dir url"""
    return base_url + '?' + urllib.urlencode(query)


def img_link(name, type):
    """"builds full image path with given name and ext."""
    if type == 'fanart' or type == 'poster':
        ext = '.jpg'
    else:
        ext = '.png'
    return os.path.join(addon.getAddonInfo('path'), "resources/media/" + name + '_' + type + ext)


def add_dir(arg):
    """adds dir item by given in arg parameters"""
    li = xbmcgui.ListItem(label=arg['title'])
    if arg['mode'] != 'play':
        arg['url'] = build_url({'mode': arg['mode'], 'title': arg['title'], 'name': arg['name'],
                                'level': str(folder_level + 1), 'folderurl': arg['url']})
        isFolder = True
        li.setProperty("IsPlayable", "false")  # !!!
    else:
        isFolder = False
        li.setProperty("IsPlayable", "true")  # !!!
    info = {
        'mediatype': 'tvshow',                 # !!!
        'plot': arg['plot']
    }
    li.setInfo('video', info)
    li.setArt({'thumb': arg['thumb'], 'fanart': arg['fanart']})
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=arg['url'], listitem=li, isFolder=isFolder)
    return ok


def get_video_dir(page):
    """creates playable dir item after parsing page with video for corresponding details """
    try:
        if page is None:
            raise Exception
        match = re.compile('<a class="html5PlayerImage" href="(.+?)">\n'
                           '<img src="(.+?)"').findall(page)
        match_title = re.compile('<meta name="title" content="(.+?)" />').findall(page)
        match_plot = re.compile('<meta name="description" content="(.+?)" />', re.DOTALL).findall(page)
        if len(match_plot) < 1:
            match_plot = [' ']
        thumb = ''
        fanart = ''
        if xbmcplugin.getSetting(addon_handle, 'download_thumbnails') == 'true':
            thumb = re.sub(r'_w\w+', '_w512_r1.jpg', match[0][1])
        if xbmcplugin.getSetting(addon_handle, 'download_fanart') == 'true':
            fanart = re.sub(r'_w\w+', '_w1280_r1.jpg', match[0][1])
        return {
            'name':     folder_name,
            'thumb':    thumb,
            'fanart':   fanart,
            'mode':     'play',
            'title':    re.sub('&.{0,5};', clean_txt, match_title[0]),
            'plot':     re.sub('&.{0,5};', clean_txt, match_plot[0]),
            'url':      re.sub('/master.m3u8', video_url[xbmcplugin.getSetting(addon_handle, 'res_video')], match[0][0])
        }
    except:
        return None


def clean_txt(str_to_clean):
    """clean html mess from str, replace things like '&#code;' with corresponding symbol"""
    try:
        #remove first and last chars ('&' and ';')
        str = str_to_clean.group(0)[1:-1]
        # remove '#' if there is one
        str = re.sub('#', '', str)
        if str == ('quot' or 'QUOT'):
            return '"'
        return unichr(int(str)).encode('utf8')
    except:
        return ''


def get_video_page_thread(page_url, where_to_put, index_to_put):
    """requests page and stores it in list 'where_to_put[index_to_put]'"""
    where_to_put[index_to_put] = read_page(page_url)
    queue.get(True, None)
    queue.task_done()


def read_page(page_url, tries=MAX_REQ_TRIES):
    """request page by 'page_url' and returns it, if request fails 'tries' times returns None"""
    req = urllib2.Request(page_url)
    req.add_header('User-Agent',
                   ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    for t in range(0, tries):
        try:
            response = urllib2.urlopen(req, timeout=3)
            page = response.read()
            return page
        except:
            if t < (tries - 1):
                xbmc.sleep(1000)
            else:
                break
        finally:
            response.close()
    return None


def show_menu(menu):
    """generates menu with dir items' parameters stored in 'menu' list"""
    for title, plot, mode, name, url in menu:
        add_dir({
            'name':    name,
            'thumb':   img_link(name, 'thumb'),
            'fanart':  img_link(name, 'fanart'),
            'mode':    mode,
            'title':   addon.getLocalizedString(title).encode('utf-8'),
            'plot':    addon.getLocalizedString(plot).encode('utf-8'),
            'url':     url
        })
    xbmcplugin.endOfDirectory(addon_handle)


try:
    ### Main menu
    if mode is None:
        mode = ['main_menu']
        add_dir({
            'name':     'live',
            'thumb':    img_link('live', 'thumb'),
            'fanart':   img_link('live', 'fanart'),
            'mode':     'play',
            'title':    '[COLOR blue]' + addon.getLocalizedString(30001).encode('utf-8') + '[/COLOR]',
            'plot':     addon.getLocalizedString(30002).encode('utf-8'),
            'url':      stream_url[xbmcplugin.getSetting(addon_handle, 'res_stream')],
        })
        show_menu(main_menu)

    ### TV Programmes menu
    elif mode == 'tvshows':
        show_menu(tvshows)

    ### List videos with NEXT link
    elif mode == 'lastvids+next':
        page = read_page(site_url + re.sub(r'.html', '/pc30.html', folder_url))
        match_url = re.compile('<span class="date" >.+</span>\n'
                           '<a href="(.+?)"').findall(page)

        queue = Queue.Queue(NUM_OF_PARALLEL_REQ)
        llast = folder_level * MAX_ITEMS_TO_SHOW
        if llast > len(match_url):
            llast = len(match_url)
        for lnum in range(llast - MAX_ITEMS_TO_SHOW, llast):
            queue.put(1, True, None)
            t = threading.Thread(
                target=get_video_page_thread,
                args=(site_url + match_url[lnum], video_pages_buffer, lnum - llast + MAX_ITEMS_TO_SHOW))
            t.daemon = True
            t.start()
        # now block and wait until all request tasks are done
        queue.join()
        for lnum in range(0, MAX_ITEMS_TO_SHOW):
            if video_pages_buffer[lnum] is not None:
                add_dir(get_video_dir(video_pages_buffer[lnum]))
        # add menu item 'Next'
        if llast < len(match_url):
            add_dir({
                'name':     folder_name,
                'thumb':    img_link('folder', 'thumb'),
                'fanart':   img_link(folder_name, 'fanart'),
                'mode':     'lastvids+next',
                'title':    '[B][COLOR blue]>> ' + addon.getLocalizedString(30101).encode('utf-8')
                            + '... (' + str(folder_level + 1) + ')[/COLOR][/B]',  # Next
                'plot':     addon.getLocalizedString(30102),
                'url':      folder_url
            })
        xbmcplugin.endOfDirectory(addon_handle)

    ### List videos with ARCHIVE link
    elif mode == 'lastvids+archive':
        page = read_page(site_url + folder_url)
        match_url = re.compile('<span class="date" >.+</span>\n'
                           '<a href="(.+?)"').findall(page)
        queue = Queue.Queue(NUM_OF_PARALLEL_REQ)
        i = 0
        for url in match_url:
            queue.put(1, True, None)
            t = threading.Thread(target=get_video_page_thread, args=(site_url + url, video_pages_buffer, i))
            t.daemon = True
            t.start()
            i += 1
        # now block and wait until all request tasks are done
        queue.join()
        for lnum in range(0, i):
            if video_pages_buffer[lnum] is not None:
                add_dir(get_video_dir(video_pages_buffer[lnum]))
        # add menu item 'Archive'
        add_dir({
            'name':     folder_name,
            'thumb':    img_link('folder', 'thumb'),
            'fanart':   img_link(folder_name, 'fanart'),
            'mode':     'allvids_archive',
            'title':    '[B][COLOR blue]' + addon.getLocalizedString(30103).encode('utf-8') + ' "' + folder_title
                        + '"[/COLOR][/B]',  # Archive
            'plot':     addon.getLocalizedString(30104).encode('utf-8'),
            'url':      folder_url
        })
        xbmcplugin.endOfDirectory(addon_handle)

    ### List ARCHIVE
    elif mode == 'allvids_archive':
        page = read_page(site_url + re.sub(r'.html', '/pc1000.html', folder_url))
        match = re.compile('</a>\n<div class="content">\n'
                           '<span class="date" >(.+?)</span>\n'
                           '<a href="(.+?)" >\n<h4>\n').findall(page)
        for date, url in match:
            add_dir({
                'name':     folder_name,
                'thumb':    img_link('folder', 'thumb'),
                'fanart':   img_link(folder_name, 'fanart'),
                'mode':     'video',
                'title':    date,  # +' | '+folder_title,
                'plot':     folder_title,
                'url':      url
            })
        xbmcplugin.endOfDirectory(addon_handle)

    ### List ONE video from archive
    elif mode == 'video':
        add_dir(get_video_dir(read_page(site_url + folder_url)))
        xbmcplugin.endOfDirectory(addon_handle)

    #### Set default view
    if xbmcplugin.getSetting(addon_handle, 'default_view') == 'true':
        try:
            xbmc.executebuiltin('Container.SetViewMode(' + default_view[xbmc.getSkinDir()][mode] + ')')
        except:
            pass

except Exception as e:
    msg = addon.getLocalizedString(30801)
    xbmcgui.Dialog().notification(addon_name, msg, addon_icon)
