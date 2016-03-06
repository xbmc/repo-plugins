import urllib
import urllib2
import os
import time
from traceback import format_exc
from urlparse import urlparse, parse_qs

import feedparser
import StorageServer
import SimpleDownloader as downloader
from BeautifulSoup import BeautifulSoup
from resources import artwork

import xbmcplugin
import xbmcgui
import xbmcaddon

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_version = addon.getAddonInfo('version')
addon_fanart = addon.getAddonInfo('fanart')
addon_icon = addon.getAddonInfo('icon')
addon_path = xbmc.translatePath(addon.getAddonInfo('path')
    ).encode('utf-8')
language = addon.getLocalizedString
cache = StorageServer.StorageServer("twit", 6)
base_url = 'https://twit.tv'


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log: %s' %format_exc()
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message),
                             level=xbmc.LOGDEBUG)


def make_request(url):
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data
    except urllib2.URLError, e:
        addon_log( 'We failed to open "%s".' %url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' %e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' %e.code)


def shows_cache():
    ''' this function will cache a dict of all shows '''
    def parse_shows_to_list(shows_url):
        soup = BeautifulSoup(make_request(shows_url),
                             convertEntities=BeautifulSoup.HTML_ENTITIES)
        shows_tag = (soup.find('div', attrs={'class': 'list media shows'})
                        ('div', attrs={'class': "item media-object"}))
        show_list = [{'url': i.a['href'],
                      'thumb': i.img['src'],
                      'title': x.a.getText(),
                      'desc': x.div.getText()} for
            i in shows_tag for x in i('div', attrs={'class': 'media-bd'})]
        return show_list
    shows = {
        'active': parse_shows_to_list(base_url + '/shows?shows_active=1'),
        'retired': parse_shows_to_list(base_url + '/shows?shows_active=0')
        }
    return shows


def display_shows(filter):
    ''' parse shows cache and add directories '''
    # update the show cache at the set cacheFunction interval
    shows = cache.cacheFunction(shows_cache)
    shows_sorted = sorted(shows[filter], key=lambda k: k['title'])
    for i in shows_sorted:
        try:
            thumb = artwork.arts[i['title']]
            fanart = thumb
        except:
            addon_log('NO Artwork %s' %i['title'])
            thumb = i['thumb']
            fanart = None
        title = i['title']
        mode = 'rss_feed'
        if filter == 'retired':
            mode = 'episodes'
        add_dir(title, i['url'], thumb, mode, {'plot': i['desc']}, fanart)


def display_main():
    ''' display the main directory '''
    live_icon = os.path.join(addon_path, 'resources', 'live.png')
    search_icon = os.path.join(addon_path, 'resources', 'search.png')
    add_dir(language(30001), 'twit_live', live_icon, 'twit_live')
    display_shows('active')
    add_dir(language(30008), 'search', search_icon, 'search')
    add_dir(language(30036), 'retired_shows', addon_icon, 'retired_shows')
    add_dir(language(30000), 'featured_episodes', addon_icon,
            'featured_episodes')


def get_rss_feed(url, show_name, iconimage):
    ''' parse the rss feed fot the initial episode directory of a show '''
    soup = BeautifulSoup(make_request(base_url + url),
                         convertEntities=BeautifulSoup.HTML_ENTITIES)
    get_art = False
    if show_name in ['Radio Leo', 'All TWiT.tv Shows']:
        get_art = True
        art_keys = artwork.arts.keys()
    media_urls = {}
    for i in soup('div', attrs={'class': 'choice'}):
        media_urls[i.label.string] = [x['value'] for x in i('option') if
                                      x.string == 'RSS'][0]
    feed = feedparser.parse(resolve_playback_type(media_urls))
    for i in feed['entries']:
        title = i['title'].encode('utf-8')
        try:
            if get_art:
                art = [artwork.arts[x] for x in art_keys if x in title][0]
            else:
                art = iconimage
        except:
            addon_log(format_exc())
            art = iconimage
        info = {}
        info['duration'] = duration_to_seconds(i['itunes_duration'])
        info['aired'] = time.strftime('%Y/%m/%d', i['published_parsed'])
        info['plot'] = i['content'][0]['value'].encode('utf-8')
        add_dir(title, i['id'], art, 'resolved_url', info, iconimage)
    if not get_art:
        all_episodes_tag = soup.find('div', attrs={'class': 'all-episodes'})
        if all_episodes_tag:
            add_dir(all_episodes_tag.a.string, all_episodes_tag.a['href'],
                    iconimage, 'episodes', {}, iconimage)


def get_episodes(url, iconimage):
    ''' display episodes of a specific show from the website'''
    soup = BeautifulSoup(make_request(base_url + url),
                         convertEntities=BeautifulSoup.HTML_ENTITIES)
    episodes = (soup.find('div', attrs={'class': 'list hero episodes'})
                    ('div', attrs={'class': 'episode item'}))
    for i in episodes:
        try:
            title = i.span.getText(' ').strip()
        except:
            addon_log(format_exc())
            continue
        add_dir(title, base_url + i.a['href'], i.img['src'], 'resolve_url',
                {'plot': i.a['title']}, iconimage)
    # find more pages
    all_episodes_tag = soup.find('div', attrs={'class': 'all-episodes'})
    if all_episodes_tag:
        add_dir(all_episodes_tag.a.string, all_episodes_tag.a['href'],
                iconimage, 'episodes', {}, iconimage)
    else:
        pagination_tag = soup.find('div', attrs={'class': 'pagination'})
        if pagination_tag:
            page_url = None
            next_page_tag = pagination_tag.find('svg',
                                                attrs={'title': 'Next'})
            if next_page_tag > 0:
                title = ('%s - Next' %
                         pagination_tag('span',
                            attrs={'class': 'page-number'})[0].string)
                page_url = pagination_tag('a', attrs={'class': 'next'}
                                          )[0]['href']
            elif next_page_tag:
                title = ('%s %s' %
                         (pagination_tag.span.string,
                          pagination_tag.a.span.string))
                page_url = pagination_tag.a['href']
            if page_url:
                add_dir(title, '/list/episodes' + page_url, iconimage,
                        'episodes', {}, iconimage)


def get_episode(url):
    ''' this function is used for search results,
        some arent linked to a episode page'''
    if 'transcript' in url:
        soup = BeautifulSoup(make_request(base_url + url),
                             convertEntities=BeautifulSoup.HTML_ENTITIES)
        episode_url = base_url + soup.find(
            'div', attrs={'class': 'episode item'}).a['href']
    else:
        episode_url = base_url + url
    set_resolved_url(resolve_url(episode_url))


def get_featured_episodes():
    ''' display episodes from twit.tv homepage'''
    soup = BeautifulSoup(make_request(base_url),
                         convertEntities=BeautifulSoup.HTML_ENTITIES)
    categories = soup('div', attrs={'class': 'list hero episodes'})
    for i in categories:
        cat_name = i.findPrevious('h2').a.string.strip()
        episodes = i('div', attrs={'class': 'episode item'})
        for x in episodes:
            try:
                episode_name = x.span.getText(' ').strip()
                title = '[%s] %s' %(cat_name, episode_name)
            except:
                addon_log(format_exc())
                continue
            try:
                fanart = artwork.arts[episode_name.rsplit(' Episode', 1)[0].strip()]
            except:
                addon_log(format_exc())
                fanart = addon_fanart
            add_dir(title, base_url + x.a['href'], x.img['src'],
                    'resolve_url', {'plot': x.a['title']}, fanart)


def search_twit():
    keyboard = xbmc.Keyboard('', "Search")
    keyboard.doModal()
    if (keyboard.isConfirmed() == False):
        return
    search_string = keyboard.getText()
    if len(search_string) == 0:
        return
    search_url = '%s/search/%s' %(base_url, urllib2.quote(search_string))
    soup = BeautifulSoup(make_request(search_url),
                         convertEntities=BeautifulSoup.HTML_ENTITIES)
    items = soup.findAll('h3', attrs={'class': 'title'})
    for i in items:
        title = i.a.string.rstrip(' (Transcript)')
        info = {'plot': i.findNext('div').string}
        add_dir(title, i.a['href'], addon_icon, 'episode', info)


def duration_to_seconds(duration_string):
    d = duration_string.split(':')
    seconds = (((int(d[0]) * 60) + int(d[1])) * 60) + int(d[2])
    return seconds


def resolve_playback_type(media_urls):
    playback_options = {
        '0': 'HD Video',
        '1': 'SD Video Large',
        '2': 'SD Video Small',
        '3': 'Audio'
        }
    if (params.has_key('content_type') and
        params['content_type'] == 'audio'):
        playback_setting = '3'
        playback_type = 'Audio'
    else:
        playback_setting = addon.getSetting('playback')
        playback_type = playback_options[playback_setting]
    resolved_url = None
    if media_urls.has_key(playback_type):
        resolved_url = media_urls[playback_type]
    else:
        dialog = xbmcgui.Dialog()
        ret = dialog.select(language(30002), media_urls.keys())
        if ret >= 0:
            resolved_url = media_urls.values()[ret]
    return resolved_url



def resolve_url(url, download=False):
    ''' resolve the stream url from the episode page'''
    soup = BeautifulSoup(make_request(url),
                         convertEntities=BeautifulSoup.HTML_ENTITIES)
    media_urls = {}
    stream_tag = soup.find('div', attrs={'class': 'choices subscribe-form'})
    if stream_tag:
        streams = stream_tag('a')
        for i in streams:
            media_urls[i.string] = i['href']
    resolved_url = None
    if media_urls:
        if not download:
            resolved_url = resolve_playback_type(media_urls)
        else:
            dialog = xbmcgui.Dialog()
            ret = dialog.select(language(30002), media_urls.keys())
            if ret >= 0:
                resolved_url = media_urls.values()[ret]
    return resolved_url


def download_file(url, title):
    ''' thanks/credit to TheCollective for SimpleDownloader module'''
    if not url.endswith('.mp4') and not url.endswith('.mp3'):
        stream_url =  resolve_url(url, True)
    else:
        stream_url = url
    path = addon.getSetting('download')
    if path == "":
        xbmc.executebuiltin("XBMC.Notification(%s,%s,10000,%s)"
                %(language(30038), language(30037), addon_icon))
        addon.openSettings()
        path = addon.getSetting('download')
    if path == "":
        return
    addon_log('######### Download #############')
    file_downloader = downloader.SimpleDownloader()
    invalid_chars = ['>', '<', '*', '/', '\\', '?', '.']
    for i in invalid_chars:
        title = title.replace(i, '')
    name = '%s.%s' %(title.replace(' ', '_'), stream_url.split('.')[-1])
    addon_log('Title: %s - Name: %s' %(title, name))
    params = {"url": stream_url, "download_path": path, "Title": title}
    addon_log(str(params))
    file_downloader.download(name, params)
    addon_log('################################')


def twit_live():
    live_urls = [
        ('http://twit.live-s.cdn.bitgravity.com/cdn-live-s1/_definst_/'
         'twit/live/high/playlist.m3u8'),
        ('http://twit.live-s.cdn.bitgravity.com/cdn-live-s1/_definst_/'
         'twit/live/low/playlist.m3u8'),
        'http://bglive-a.bitgravity.com/twit/live/high?noprefix',
        'http://bglive-a.bitgravity.com/twit/live/low?noprefix',
        ('http://iphone-streaming.ustream.tv/ustreamVideo/1524/'
         'streams/live/playlist.m3u8'),
        ('http://hls.cdn.flosoft.biz/flosoft/smil:twitStreamAll.smil/'
         'playlist.m3u8'),
        'http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_720/playlist.m3u8',
        'http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_540/playlist.m3u8',
        'http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_360/playlist.m3u8',
        'http://twit.am/listen'
        ]
    if content_type == 'audio':
        resolved_url = live_urls[-1]
    else:
        resolved_url = live_urls[int(addon.getSetting('twit_live'))]
    return resolved_url


def set_resolved_url(resolved_url):
    success = False
    if resolved_url:
        success = True
    else:
        resolved_url = ''
    item = xbmcgui.ListItem(path=resolved_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)


def add_dir(name, url, iconimage, mode, info={}, fanart=None):
    item_params = {'name': name, 'url': url, 'mode': mode,
                   'iconimage': iconimage, 'content_type': content_type}
    plugin_url = '%s?%s' %(sys.argv[0], urllib.urlencode(item_params))
    listitem = xbmcgui.ListItem(name, iconImage=iconimage,
                                thumbnailImage=iconimage)
    if name == language(30001):
        contextMenu = [('Run IrcChat',
                        'RunPlugin(plugin://plugin.video.twit/?'
                        'mode=ircchat&name=ircchat&url=live_chat)')]
        listitem.addContextMenuItems(contextMenu)
    isfolder = True
    if mode in ['resolve_url', 'resolved_url', 'twit_live', 'episode']:
        isfolder = False
        listitem.setProperty('IsPlayable', 'true')
    if mode in ['resolve_url', 'episode', 'resolved_url']:
        contextMenu = [(language(30035),
                       'RunPlugin(plugin://plugin.video.twit/?'
                       'mode=download&name=%s&url=%s)' %(name, url))]
        listitem.addContextMenuItems(contextMenu)
    if fanart is None:
        fanart = addon_fanart
    listitem.setProperty('Fanart_Image', fanart)
    info_type = 'video'
    if content_type == 'audio':
        info_type = 'music'
    listitem.setInfo(type=info_type, infoLabels=info)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), plugin_url,
                                listitem, isfolder)


def run_ircchat():
    # check chat args
    nickname = addon.getSetting('nickname')
    username = addon.getSetting('username')
    if not nickname or not username:
        xbmc.executebuiltin('XBMC.Notification(%s, %s,10000,%s)' %
            ('IrcChat', language(30024), addon_icon))
        addon.openSettings()
        nickname = addon.getSetting('nickname')
        username = addon.getSetting('username')
    if not nickname or not username:
            return
    # run ircchat script
    xbmc.executebuiltin(
        'RunScript(script.ircchat, run_irc=True&nickname=%s&username=%s'
        '&password=%s&host=irc.twit.tv&channel=twitlive)' %
        (nickname, username, addon.getSetting('password'))
        )


def set_view_mode():
    view_mode = addon.getSetting('view_mode')
    if view_mode == "0":
        return
    view_modes = {
        '1': '502', # List
        '2': '51', # Big List
        '3': '500', # Thumbnails
        '4': '501', # Poster Wrap
        '5': '508', # Fanart
        '6': '504',  # Media info
        '7': '503',  # Media info 2
        '8': '515'  # Media info 3
        }
    xbmc.executebuiltin('Container.SetViewMode(%s)' %view_modes[view_mode])


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


params = get_params()

if params.has_key('content_type') and params['content_type'] == 'audio':
    content_type = 'audio'
else:
    content_type = 'video'

mode = None
try:
    mode = params['mode']
    addon_log('Mode: %s, Name: %s, URL: %s' %
              (params['mode'], params['name'], params['url']))
except:
    addon_log('Get root directory')

if mode is None:
    display_main()
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'retired_shows':
    display_shows('retired')
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'episodes':
    get_episodes(params['url'], params['iconimage'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'episode':
    get_episode(params['url'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'featured_episodes':
    get_featured_episodes()
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'search':
    search_twit()
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'rss_feed':
    get_rss_feed(params['url'], params['name'], params['iconimage'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'resolved_url':
    set_resolved_url(params['url'])

elif mode == 'resolve_url':
    set_resolved_url(resolve_url(params['url']))

elif mode == 'download':
    download_file(params['url'], params['name'])

elif mode == 'twit_live':
    set_resolved_url(twit_live())
    xbmc.sleep(1000)
    if addon.getSetting('run_chat') == 'true':
        run_ircchat()

elif mode == 'ircchat':
    run_ircchat()