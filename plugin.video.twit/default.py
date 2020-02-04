import urllib
import urllib2
import os
import time
from traceback import format_exc
from urlparse import urlparse, parse_qs

import feedparser
import SimpleDownloader as downloader
from resources import shows
from bs4 import BeautifulSoup

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


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log: %s' %format_exc()
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message),
                             level=xbmc.LOGDEBUG)


def make_request(url):
    addon_log('Make Request: %s' %url)
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data
    except urllib2.URLError as e:
        addon_log( 'We failed to open "%s".' %url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' %e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' %e.code)


def display_shows(filter):
    ''' parse shows and add plugin directories '''
    if filter == 'active':
        items = shows.active_shows
    else:
        items = shows.retired_shows
    for i in items:
        add_dir(i['title'], i['url'], i['art'], 'rss_feed',
                {'plot': i['desc']}, i['art'])


def display_main():
    ''' display the main directory '''
    live_icon = os.path.join(addon_path, 'resources', 'live.png')
    add_dir(language(30001), 'twit_live', live_icon, 'twit_live')
    display_shows('active')
    add_dir(language(30036), 'retired_shows', addon_icon, 'retired_shows')


def get_rss_feed(url, show_name, iconimage):
    ''' parse the rss feed for the episode directory of a show '''
    show_data = [i for i in shows.active_shows if show_name == i['title']]
    if not show_data:
        show_data = [i for i in shows.retired_shows if
                show_name == i['title']]
    feed = feedparser.parse(resolve_playback_type(show_data[0]['feeds']))
    for i in feed['entries']:
        title = i['title'].encode('utf-8')
        if i.has_key('media_thumbnail'):
            art = i['media_thumbnail'][0]['url']
        else:
            art = iconimage
        info = {}
        info['duration'] = duration_to_seconds(i['itunes_duration'])
        info['aired'] = time.strftime('%Y/%m/%d', i['published_parsed'])
        soup = BeautifulSoup(i['content'][0]['value'], 'html.parser')
        info['plot'] = soup.get_text().encode('utf-8')
        stream_url = i['id']
        if not stream_url.startswith('http'):
            stream_url = i['media_content'][0]['url']
        add_dir(title, stream_url, art, 'resolved_url', info, iconimage)


def duration_to_seconds(duration_string):
    seconds = None
    if duration_string and len(duration_string.split(':')) >= 2:
        d = duration_string.split(':')
        if len(d) == 3:
            seconds = (((int(d[0]) * 60) + int(d[1])) * 60) + int(d[2])
        else:
            seconds = (int(d[0]) * 60) + int(d[1])
    elif duration_string:
        try:
            seconds = int(duration_string)
        except:
            addon_log(format_exc())
    return seconds


def resolve_playback_type(media_urls):
    playback_options = {
        '0': 'Video-HD',
        '1': 'Video-HI',
        '2': 'Video-LO',
        '3': 'MP3'
        }
    if (params.has_key('content_type') and
        params['content_type'] == 'audio'):
        playback_setting = '3'
        playback_type = 'MP3'
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


def download_file(stream_url, title):
    ''' thanks/credit to TheCollective for SimpleDownloader module'''
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


def get_youtube_live_id():
    data = make_request('https://www.youtube.com/user/twit/live')
    soup = BeautifulSoup(data, 'html.parser')
    video_id = soup.find('meta', attrs={'itemprop': "videoId"})['content']
    return video_id


def twit_live():
    live_urls = [
        'https://mixer.com/api/v1/channels/39385369/manifest.m3u8',
        ('http://iphone-streaming.ustream.tv/uhls/1524/streams/live/'
            'iphone/playlist.m3u8'),
        ('plugin://plugin.video.youtube/play/?video_id=%s'
            %get_youtube_live_id()),
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
    if mode in ['resolved_url', 'twit_live']:
        isfolder = False
        listitem.setProperty('IsPlayable', 'true')
    if mode is 'resolved_url':
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

elif mode == 'rss_feed':
    get_rss_feed(params['url'], params['name'], params['iconimage'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'resolved_url':
    set_resolved_url(params['url'])

elif mode == 'download':
    download_file(params['url'], params['name'])

elif mode == 'twit_live':
    set_resolved_url(twit_live())
    xbmc.sleep(1000)
    if addon.getSetting('run_chat') == 'true':
        run_ircchat()

elif mode == 'ircchat':
    run_ircchat()