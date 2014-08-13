import urllib
import urllib2
import re
import os
import json
import time
from datetime import datetime
from traceback import format_exc
from urlparse import urlparse, parse_qs

import StorageServer
from bs4 import BeautifulSoup

import xbmcplugin
import xbmcgui
import xbmcaddon

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_version = addon.getAddonInfo('version')
addon_fanart = addon.getAddonInfo('fanart')
addon_icon = addon.getAddonInfo('icon')
addon_path = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8')
language = addon.getLocalizedString
cache = StorageServer.StorageServer("twit", 2)
base_url = 'http://twit.tv'


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log: %s' %format_exc()
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message), level=xbmc.LOGDEBUG)


def cache_shows_file():
    ''' creates an initial cache from the shows file '''
    show_file = os.path.join(addon_path, 'resources', 'shows')
    cache.set("shows", open(show_file, 'r').read())


def make_request(url, locate=False):
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        if locate:
            return response.geturl()
        return data
    except urllib2.URLError, e:
        addon_log( 'We failed to open "%s".' %url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' %e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' %e.code)


def shows_cache():
    ''' this function updates the shows cache '''
    shows = eval(cache.get('shows'))
    url = base_url + '/shows'
    soup = BeautifulSoup(make_request(url), 'html.parser')
    active_list = soup.findAll('div', class_='item-list')[2]('li')
    retired_list = soup.findAll('div', class_='item-list')[3]('li')
    for shows_ in [active_list, retired_list]:
        if shows_ is active_list:
            show_type = 'active'
        elif shows_ is retired_list:
            show_type = 'retired'
        for i in shows_:
            try:
                name = i('a')[-1].string.encode('utf-8')
            except:
                addon_log('addonException: %s' %format_exc())
                continue
            if name == 'Radio Leo': continue
            if not shows[show_type].has_key(name):
                addon_log('Show not in cache: %s' %name)
                desc = ''
                thumb = addon_icon
                try:
                    location = make_request(base_url + i('a')[-1]['href'], True)
                    # the location url points to an episode, we want the full list
                    show_url = None
                    episode == location.rsplit('/', 1)[1]
                    # sometimes the episode is seperated with a dash instead of a slash
                    if '-' in episode:
                        episode == location.rsplit('-', 1)[1]
                        try:
                            int(episode)
                            show_url = location.rsplit('-', 1)[0]
                        except ValueError:
                            pass
                    else:
                        try:
                            int(episode)
                            show_url = location.rsplit('/', 1)[0]
                        except ValueError:
                            pass
                    # if there is not an episode we will skip caching
                    if show_url is None:
                        addon_log('Not caching new show: %s' %name)
                        return "True"
                    addon_log('Show URL: %s' %show_url)
                    soup = BeautifulSoup(make_request(show_url), 'html.parser')
                    desc_tag = soup.find('div', class_='field-content')
                    desc = ''
                    if desc_tag and desc_tag.getText():
                        desc = desc_tag.getText()
                    thumb_tag = soup.find('div', class_='views-field views-field-field-cover-art-fid')
                    thumb = addon_icon
                    if thumb_tag and thumb_tag.find('img'):
                        thumb = thumb_tag.img['src']
                    shows[show_type][name] = {'show_url': url, 'thumb': thumb, 'description': desc}
                    addon_log('Cached new show: %s' %name)
                except:
                    addon_log('addonException cache new show: %s' %format_exc)
            if shows['active'].has_key(name) and show_type == 'retired':
                del shows['active'][name]
    cache.set('shows', repr(shows))
    return "True"


def display_shows():
    ''' display the main directory '''
    # update the show cache at the set cacheFunction interval
    cache_shows = eval(cache.cacheFunction(shows_cache))
    live_icon = 'http://twit-xbmc.googlecode.com/svn/images/live_icon.png'
    add_dir(language(30000), 'latest_episodes', addon_icon, 'latest_episodes')
    add_dir(language(30001), 'twit_live', live_icon, 'twit_live')
    shows = eval(cache.get('shows'))
    items = sorted(shows['active'].keys(), key=str.lower)
    for i in items:
        item = shows['active'][i]
        add_dir(i, item['show_url'], item['thumb'],
                'episodes', {'plot': item['description']})
    add_dir(language(30036), 'retired_shows', addon_icon, 'retired_shows')


def get_retired_shows():
    ''' displays the retired shows directory '''
    shows = eval(cache.get('shows'))
    items = sorted(shows['retired'].keys(), key=str.lower)
    for i in items:
        item = shows['retired'][i]
        add_dir(i, item['show_url'], item['thumb'],
                'episodes', {'plot': item['description']})


def get_episodes(url, iconimage):
    ''' display episodes of a specific show '''
    soup = BeautifulSoup(make_request(url), 'html.parser')
    id_tag = soup.find('div', attrs={'id': 'block-views-show_list-block_1'})
    if not id_tag:
        # seems the tech guy html is a little different
        id_tag = soup.find('div', class_='view-display-id-block_4')
    if not id_tag:
        # sometimes new shows wont have episodes yet
        addon_log('episode list not found')
        return
    items = id_tag('div', class_='views-row')
    for i in items:
        item_text = i.get_text(' | ', True).encode('utf-8')
        items_ = item_text.split(' | ')
        item_url = i.a['href']
        info = {}
        episode_string = items_[1]
        try:
            info['episode'] = int(re.findall('#(.+?):', episode_string)[0])
        except:
            addon_log('addonException: %s' %format_exc())
            try:
                info['episode'] = int(episode_string.split(' ')[-1])
            except:
                addon_log('addonException: %s' %format_exc())
        try:
            item_date = items_[0]
            info['plot'] = items_[-1]
            info['aired'] = item_date
            date_time = None
            try:
                date_time = datetime.strptime(item_date, '%B %d, %Y')
            except:
                try:
                    date_time = datetime(*(time.strptime(item_date, '%B %d, %Y')[0:6]))
                except:
                    addon_log('addonException: %s' %format_exc())
            if date_time:
                info['date'] = date_time.strftime('%d.%m.%Y')
                info['premiered'] = date_time.strftime('%d-%m-%Y')
        except:
            addon_log('addonException: %s' %format_exc())
        add_dir(episode_string, item_url, iconimage, 'resolve_url', info)
    page_tag = soup.find('li', class_='pager-next')
    if page_tag:
        if page_tag.find('a') and page_tag.a.has_attr('href'):
            page_url = base_url + page_tag.a['href']
            add_dir(language(30019), page_url, iconimage, 'episodes')


def cache_latest_episods():
    shows = eval(cache.get('shows'))
    soup = BeautifulSoup(make_request(base_url), 'html.parser')
    section_tag = soup.find('section', id='block-views-frontpage-block_3')
    items = section_tag('div', class_='views-row')
    episodes = []
    for i in items:
        item_text = i.get_text(' | ', True).encode('utf-8')
        items_ = item_text.split(' | ')
        info = {}
        item_url = i.a['href']
        show_name = items_[0]
        episode_string = items_[1]
        info['title'] = '%s - %s' %(show_name, episode_string)
        info['plot'] = items_[-1]
        try:
            info['episode'] = int(re.findall('#(.+?):', episode_string)[0])
        except:
            addon_log('addonException: %s' %format_exc())
            try:
                info['episode'] = int(episode_string.split(' ')[-1])
            except:
                addon_log('addonException: %s' %format_exc())
        try:
            item_date = ''.join([items_[2][:items_[2].index(',') - 2],
                                 items_[2][items_[2].index(',') :]])
            date_time = datetime(*(time.strptime(item_date, '%B %d, %Y')[0:6]))
            info['date'] = date_time.strftime('%d.%m.%Y')
            info['premiered'] = date_time.strftime('%d-%m-%Y')
            info['aired'] = item_date
        except:
            addon_log('addonException: %s' %format_exc())
        try:
            thumbnail = shows['active'][show_name]['thumb']
        except:
            addon_log('addonException: %s' %format_exc())
            if i.find('img') and i.img.has_attr('src'):
                thumbnail =  i.img['src']
            else:
                thumbnail = addon_icon
        episodes.append({'url': item_url, 'thumb': thumbnail, 'info': info})
    return episodes


def get_latest_episodes():
    episodes = cache.cacheFunction(cache_latest_episods)
    for i in episodes:
        add_dir(i['info']['title'], i['url'], i['thumb'], 'resolve_url', i['info'])


def resolve_url(url):
    playback_options = {
        '0': 'hd',
        '1': 'sd',
        '2': 'sd-low',
        '3': 'audio'
        }
    soup = BeautifulSoup(make_request(url), 'html.parser')
    media_urls = {}
    for i in soup('span', class_='download'):
        media_urls[i.a['class'][0]] = i.a['href']
    if params.has_key('content_type') and params['content_type'] == 'audio':
        playback_setting = '3'
        playback_type = 'audio'
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


def twit_live():
    live_urls = [
        'http://twit.live-s.cdn.bitgravity.com/cdn-live-s1/_definst_/twit/live/high/playlist.m3u8',
        'http://twit.live-s.cdn.bitgravity.com/cdn-live-s1/_definst_/twit/live/low/playlist.m3u8',
        'http://bglive-a.bitgravity.com/twit/live/high?noprefix',
        'http://bglive-a.bitgravity.com/twit/live/low?noprefix',
        'http://iphone-streaming.ustream.tv/ustreamVideo/1524/streams/live/playlist.m3u8',
        'justintv',
        'http://hls.cdn.flosoft.biz/flosoft/smil:twitStreamAll.smil/playlist.m3u8',
        'http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_720/playlist.m3u8',
        'http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_540/playlist.m3u8',
        'http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_360/playlist.m3u8',
        'http://twit.am/listen'
        ]
    if content_type == 'audio':
        resolved_url = live_urls[-1]
    else:
        resolved_url = live_urls[int(addon.getSetting('twit_live'))]
        if resolved_url == 'justintv':
            resolved_url = get_jtv()
    return resolved_url


def set_resolved_url(resolved_url):
    success = False
    if resolved_url:
        success = True
    else:
        resolved_url = ''
    item = xbmcgui.ListItem(path=resolved_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)


def get_jtv():
    token_url = 'https://api.twitch.tv/api/channels/twit/access_token?as3=t'
    data = json.loads(make_request(token_url))
    url_params = [
        'nauthsig=%s' %data['sig'],
        'player=jtvweb',
        'private_code=null',
        'type=any',
        'nauth=%s' %urllib2.quote(data['token']),
        'allow_source=true',
            ]
    resolved_url = 'http://usher.twitch.tv/select/twit.json?' + '&'.join(url_params)
    return resolved_url


def add_dir(name, url, iconimage, mode, info={}):
    item_params = {'name': name, 'url': url, 'mode': mode,
                   'iconimage': iconimage, 'content_type': content_type}
    plugin_url = '%s?%s' %(sys.argv[0], urllib.urlencode(item_params))
    listitem = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    if name == language(30001):
        contextMenu = [('Run IrcChat',
                        'RunPlugin(plugin://plugin.video.twit/?'
                        'mode=ircchat&name=ircchat&url=live_chat)')]
        listitem.addContextMenuItems(contextMenu)
    isfolder = True
    if mode == 'resolve_url' or mode == 'twit_live':
        isfolder = False
        listitem.setProperty('IsPlayable', 'true')
    fanart = addon_fanart
    if (addon.getSetting('show_art') == 'true' and
            not name in [language(30000), language(30001), language(30036)]):
        fanart = iconimage
    listitem.setProperty('Fanart_Image', fanart)
    info_type = 'video'
    if content_type == 'audio':
        info_type = 'music'
    listitem.setInfo(type=info_type, infoLabels=info)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), plugin_url, listitem, isfolder)


def run_ircchat():
    # check chat args
    nickname = addon.getSetting('nickname')
    username = addon.getSetting('username')
    if not nickname or not username:
        xbmc.executebuiltin('XBMC.Notification(%s, %s,10000,%s)'
            %('IrcChat', language(30024), icon))
        addon.openSettings()
        nickname = addon.getSetting('nickname')
        username = addon.getSetting('username')
    if not nickname or not username:
            return
    # run ircchat script
    xbmc.executebuiltin(
        'RunScript(script.ircchat, run_irc=True&nickname=%s&username=%s'
        '&password=%s&host=irc.twit.tv&channel=twitlive)'
        %(nickname, username, addon.getSetting('password'))
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


first_run = addon.getSetting('first_run')
if first_run != addon_version:
    cache_shows_file()
    addon_log('first_run, caching shows file')
    xbmc.sleep(1000)
    addon.setSetting('first_run', addon_version)

params = get_params()

if params.has_key('content_type') and params['content_type'] == 'audio':
    content_type = 'audio'
else:
    content_type = 'video'

mode = None
try:
    mode = params['mode']
    addon_log('Mode: %s, Name: %s, URL: %s'
              %(params['mode'], params['name'], params['url']))
except:
    addon_log('Get root directory')

if mode is None:
    try:
        shows = eval(cache.get('shows'))
        if isinstance(shows, dict):
            display_shows()
        else:
            raise
    except:
        addon_log('"shows" cache missing')
        cache_shows_file()
        addon_log('caching shows file,'
                  'this should only happen if common cache db is reset')
        xbmc.sleep(1000)
        shows = eval(cache.get('shows'))
        if isinstance(shows, dict):
            display_shows()
        else:
            addon_log('"shows" cache ERROR')
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'retired_shows':
    get_retired_shows()
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'episodes':
    get_episodes(params['url'], params['iconimage'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'latest_episodes':
    get_latest_episodes()
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'resolve_url':
    set_resolved_url(resolve_url(params['url']))

elif mode == 'twit_live':
    set_resolved_url(twit_live())
    xbmc.sleep(1000)
    if addon.getSetting('run_chat') == 'true':
        run_ircchat()

elif mode == 'ircchat':
    run_ircchat()