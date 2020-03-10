# This Python file uses the following encoding: utf-8
import os
import sys
import time
try:
    from urllib import urlencode, unquote_plus
except ImportError:
    # for python3
    from urllib.parse import urlencode, unquote_plus

import feedparser
import SimpleDownloader as Downloader
from resources import shows
from bs4 import BeautifulSoup
import requests

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
    xbmc.log("[%s-%s]: %s" % (addon_id, addon_version, string),
             level=xbmc.LOGDEBUG)


def make_request(url):
    try:
        res = requests.get(url)
        if not res.status_code == requests.codes.ok:
            addon_log('Bad status code: %s' % res.status_code)
            res.raise_for_status()
        if not res.encoding == 'utf-8':
            res.encoding = 'utf-8'
        return res.text
    except requests.exceptions.HTTPError as error:
        addon_log('We failed to open "%s".' % url)
        addon_log(error)


def display_shows(_filter):
    """ parse shows and add plugin directories """
    if _filter == 'active':
        items = shows.active_shows
    else:
        items = shows.retired_shows
    for i in items:
        add_dir(i['title'], i['url'], i['art'], 'rss_feed',
                {'plot': i['desc']}, i['art'])


def display_main():
    """ display the main directory """
    live_icon = os.path.join(addon_path, 'resources', 'live.png')
    add_dir(language(30001), 'twit_live', live_icon, 'twit_live')
    display_shows('active')
    add_dir(language(30036), 'retired_shows', addon_icon, 'retired_shows')


def get_rss_feed(show_name, iconimage):
    """ parse the rss feed for the episode directory of a show """
    show_data = [i for i in shows.active_shows if show_name == i['title']]
    if not show_data:
        show_data = [i for i in shows.retired_shows if
                     show_name == i['title']]
    comp_shows = ('Radio Leo', 'All TWiT.tv Shows')
    artworks = None
    if show_name in comp_shows:
        artworks = [{i['title']: i['art']} for i in shows.active_shows]
    feed = feedparser.parse(resolve_playback_type(show_data[0]['feeds']))
    for i in feed['entries']:
        title = i['title']
        art = None
        if artworks:
            art_list = [list(x.values())[0] for x in artworks if
                        list(x.keys())[0] in title]
            if art_list:
                art = art_list[0]
        if art is None:
            if 'media_thumbnail' in i:
                art = i['media_thumbnail'][0]['url']
        if art is None:
            art = iconimage
        info = {'duration': duration_to_seconds(i['itunes_duration']),
                'aired': time.strftime('%Y/%m/%d', i['published_parsed'])}
        soup = BeautifulSoup(i['content'][0]['value'], 'html.parser')
        info['plot'] = soup.get_text()
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
        except ValueError:
            addon_log('Not able to int duration_string: %s' % duration_string)
    return seconds


def resolve_playback_type(media_urls):
    playback_options = {
        '0': 'Video-HD',
        '1': 'Video-HI',
        '2': 'Video-LO',
        '3': 'MP3'
    }
    if 'content_type' in params and params['content_type'] == 'audio':
        playback_type = 'MP3'
    else:
        playback_setting = addon.getSetting('playback')
        playback_type = playback_options[playback_setting]
    resolved_url = None
    if playback_type in media_urls:
        resolved_url = media_urls[playback_type]
    else:
        dialog = xbmcgui.Dialog()
        ret = dialog.select(language(30002), list(media_urls.keys()))
        if ret >= 0:
            resolved_url = list(media_urls.values())[ret]
    return resolved_url


def download_file(stream_url, title):
    """ thanks/credit to TheCollective for SimpleDownloader module"""
    path = addon.getSetting('download')
    if path == "":
        xbmc.executebuiltin("xbmcgui.Dialog().notification(%s,%s,10000,%s)"
                            % (language(30038), language(30037), addon_icon))
        addon.openSettings()
        path = addon.getSetting('download')
    if path == "":
        return
    addon_log('######### Download #############')
    file_downloader = Downloader.SimpleDownloader()
    invalid_chars = ['>', '<', '*', '/', '\\', '?', '.']
    for i in invalid_chars:
        title = title.replace(i, '')
    name = '%s.%s' % (title.replace(' ', '_'), stream_url.split('.')[-1])
    addon_log('Title: %s - Name: %s' % (title, name))
    download_params = {"url": stream_url, "download_path": path, "Title": title}
    addon_log(str(download_params))
    file_downloader.download(name, download_params)
    addon_log('################################')


def get_youtube_live_id():
    data = make_request('https://www.youtube.com/user/twit/live')
    soup = BeautifulSoup(data, 'html.parser')
    video_id = soup.find('meta', attrs={'itemprop': "videoId"})['content']
    return video_id


def twit_live():
    live_urls = (
        'https://mixer.com/api/v1/channels/39385369/manifest.m3u8',
        ('http://iphone-streaming.ustream.tv/uhls/1524/streams/live/'
         'iphone/playlist.m3u8'),
        ('plugin://plugin.video.youtube/play/?video_id=%s'
         % get_youtube_live_id()),
        'http://twit.am/listen')

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


def add_dir(name, url, iconimage, dir_mode, info=None, fanart=None):
    if info is None:
        info = {}
    item_params = {'name': name.encode('utf-8'), 'url': url, 'mode': dir_mode,
                   'iconimage': iconimage, 'content_type': content_type}
    plugin_url = '%s?%s' % (sys.argv[0], urlencode(item_params))
    listitem = xbmcgui.ListItem(name, iconImage=iconimage,
                                thumbnailImage=iconimage)
    if name == language(30001):
        contextMenu = [('Run IrcChat',
                        'RunPlugin(plugin://plugin.video.twit/?'
                        'mode=ircchat&name=ircchat&url=live_chat)')]
        listitem.addContextMenuItems(contextMenu)
    isfolder = True
    if dir_mode in ['resolved_url', 'twit_live']:
        isfolder = False
        listitem.setProperty('IsPlayable', 'true')
    if dir_mode is 'resolved_url':
        contextMenu = [(language(30035),
                        'RunPlugin(plugin://plugin.video.twit/?'
                        'mode=download&name=%s&url=%s)' % (name, url))]
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
        xbmc.executebuiltin('xbmcgui.Dialog().notification(%s, %s,10000,%s)' %
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
        (nickname, username, addon.getSetting('password')))


params = {i.split('=')[0]: i.split('=')[1] for
          i in unquote_plus(sys.argv[2])[1:].split('&')}

if 'content_type' in params and params['content_type'] == 'audio':
    content_type = 'audio'
else:
    content_type = 'video'

mode = None
if 'mode' in params:
    mode = params['mode']
    addon_log('Mode: %s, Name: %s, URL: %s' %
              (params['mode'], params['name'], params['url']))
else:
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
    get_rss_feed(params['name'], params['iconimage'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
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
