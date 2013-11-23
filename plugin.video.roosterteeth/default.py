import urllib
import urllib2
import cookielib
import re
import os
import json
import time
from datetime import datetime
from urlparse import urlparse, parse_qs
from traceback import format_exc

import xmltodict
import StorageServer
from bs4 import BeautifulSoup

import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs

cache = StorageServer.StorageServer("roosterteeth", 6)
addon = xbmcaddon.Addon()
addon_profile = xbmc.translatePath(addon.getAddonInfo('profile'))
addon_version = addon.getAddonInfo('version')
addon_id = addon.getAddonInfo('id')
home = addon.getAddonInfo('path')
icon = addon.getAddonInfo('icon')
fanart = addon.getAddonInfo('fanart')
language = addon.getLocalizedString
cookie_file = os.path.join(addon_profile, 'cookie_file')
cookie_jar = cookielib.LWPCookieJar(cookie_file)
base = 'http://roosterteeth.com'


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log'
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message),level=xbmc.LOGDEBUG)


def notify(message):
    xbmc.executebuiltin("XBMC.Notification(%s, %s, 10000, %s)" %(language(30001), message, icon))


def make_request(url, data=None, location=False):
    if not xbmcvfs.exists(cookie_file):
        cookie_jar.save()
    cookie_jar.load(cookie_file, ignore_discard=True, ignore_expires=True)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    urllib2.install_opener(opener)
    addon_log('Request URL: %s' %url)
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0',
        'Referer': 'http://roosterteeth.com'
        }
    try:
        req = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(req)
        response_url = urllib.unquote_plus(response.geturl())
        data = response.read()
        cookie_jar.save(cookie_file, ignore_discard=False, ignore_expires=False)
        response.close()
        if location:
            return (response_url, data)
        else:
            return data
    except urllib2.URLError, e:
        addon_log('We failed to open "%s".' % url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' %e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' % e.code)


def get_soup(data):
    if data:
        if data.startswith('http'):
            data = make_request(data)
        return BeautifulSoup(data, 'html.parser')


def cache_shows():

    def filter_items(item_list):
        parsed = []
        for i in item_list:
            try:
                show = (i.b.string, i.a['href'], i.img['src'],
                        i('a')[2].b.string.split()[0], i.span.string)
                if not show in parsed:
                    parsed.append(show)
            except:
                addon_log('addonException: %s' %format_exc())
                continue
        return parsed

    rt_url = 'http://roosterteeth.com/archive/series.php'
    ah_url = 'http://ah.roosterteeth.com/archive/series.php'
    soup = get_soup(rt_url)
    ah_soup = get_soup(ah_url)
    items = soup('table', class_="border boxBorder")[0].table('tr')
    items += ah_soup('table', class_="border boxBorder")[0].table('tr')
    retired_items = soup('table', class_="border boxBorder")[1].table('tr')
    retired_items += ah_soup('table', class_="border boxBorder")[1].table('tr')
    return repr({'active': filter_items(items), 'retired': filter_items(retired_items)})


def get_shows(shows):
    for i in shows:
        if 'v=trending' in i[1]:
            i[1] = i[1].replace('v=trending','v=more')
        plot = ''
        if i[4]:
            plot = i[4]
        add_dir(i[0], base+i[1], 1, i[2], {'Episode': int(i[3]), 'Plot': plot})


def get_seasons(soup, iconimage):
    try:
        items = soup('td', class_="seasonsBox")[0]('a')
        if len(items) < 1:
            raise
    except IndexError:
        addon_log('Seasons Exception: %s' %format_exc())
        return False
    for i in items:
        name = i.string.encode('utf-8')
        try:
            meta = {'Season': int(name.split(':')[0].split()[1])}
        except:
            meta = {}
        add_dir(name, base+i['href'], 2, iconimage, meta, True)
    return True


def index(soup, season=True):
    episode_patterns = [re.compile('Episode (.+?):'), re.compile('Episode (.+?) -'),
                        re.compile('Volume (.+?):'), re.compile('#(.+?):')]
    if season:
        items = soup('div', attrs={'id' : "profileAjaxContent"})[0]('table')[1]('a')
    else:
        items = soup('div', attrs={'id' : "profileAjaxContent"})[0]('table')[0]('a')
    for i in items:
        href = i['href']
        item_id = href.split('id=')[1].split('&')[0]
        try:
            thumb = i.img['src']
        except:
            thumb = icon
        name = i('span')[0].string
        if name is None:
            name = i('span')[0].contents[0]
        try:
            if (not i('span')[1].string is None) and (not i('span')[1].string in name):
                name += ': ' + i('span')[1].string
        except:
            pass
        name = name.encode('utf-8', 'ignore')
        meta = {}
        duration = i.td.string
        if duration:
            meta['Duration'] = get_duration(duration)
        for i in episode_patterns:
            try:
                meta['Episode'] = int(i.findall(name)[0])
                break
            except:
                pass
        add_dir(name, item_id, 3, thumb, meta, False, False)
    try:
        next_page = soup('a', attrs={'id' : "streamLoadMore"})[0]['href']
        add_dir(language(30002), base + next_page, 2, icon, {}, season)
    except:
        addon_log("Didn't find next page!")


def resolve_url(item_id, retry=False):
    url = 'http://roosterteeth.com/archive/new/_loadEpisode.php?id=%s&v=morev' %item_id
    data = json.loads(make_request(url))
    soup = get_soup(data['embed']['html'])
    try:
        filetype = soup.div['data-filetype']
        if filetype == 'youtube':
            youtube_id = soup.iframe['src'].split('/')[-1].split('?')[0]
            addon_log('youtube id:' + youtube_id)
            path = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' %youtube_id
        elif filetype == 'blip':
            blip_url = soup.iframe['src']
            addon_log('blip_url: ' + blip_url)
            path = get_blip_location(blip_url)
            addon_log('path: %s' %path)
        return path
    except:
        if retry:
            addon_log('retryException: %s' %format_exc())
            sorry = check_sorry(soup)
        elif addon.getSetting('is_sponsor') == 'true':
            logged_in = check_login()
            if not logged_in:
                logged_in = login()
                if logged_in:
                    return resolve_url(item_id, True)
                notify(language(30025))
                xbmc.sleep(5000)
            sorry = check_sorry(soup)
        else:
            sorry = check_sorry(soup)
        if not sorry:
            notify(language(30024))
            addon_log('addonException: resolve_url')


def check_sorry(soup):
    sorry = ['Video recordings and live broadcasts of the podcast are only available for Sponsors.',
             'Sorry, you must be a Sponsor to see this video.']
    for i in sorry:
        pattern = re.compile(i)
        if pattern.findall(str(soup)):
            notify(language(30003))
            addon_log(i)
            return True


def get_blip_location(blip_url):
    blip_data = make_request(blip_url, location=True)
    pattern = re.compile('http://blip.tv/rss/flash/(.+?)&')
    try:
        feed_id = pattern.findall(blip_data[0])[0]
    except IndexError:
        patterns = [re.compile('config.id = "(.+?)";'),
                    re.compile('data-episode-id="(.+?)"')]
        for i in patterns:
            try:
                feed_id = i.findall(blip_data[1])[0]
            except IndexError:
                feed_id = None
                pass
            if feed_id:
                break
        if not feed_id:
            addon_log('Did not find the feed ID')
            return
    blip_xml = 'http://blip.tv/rss/flash/' + feed_id
    media_content = []
    try:
        blip_dict = xmltodict.parse(make_request(blip_xml))
        items = blip_dict['rss']['channel']['item']['media:group'][u'media:content']
        # if only one result items will be a dict
        if isinstance(items, dict):
            try:
                return items['@url']
            except:
                raise
        media_content = [i for i in items if i.has_key('@blip:role')]
    except:
        addon_log('addonException: %s' %format_exc())
        return
    if len(media_content) < 1:
        addon_log('Did not find media content')
        return
    url = None
    default = None
    preferred_quality = addon.getSetting('quality')
    if preferred_quality == '0':
        try:
            items = [{'type': i['@blip:role'], 'url': i['@url']} for i in media_content if
                     '720' in i['@blip:role'] or 'Source' in i['@blip:role']]
            if len(items) == 1:
                return items[0]['url']
            else:
                try:
                    return [i['url'] for i in items if '720' in i['type']][0]
                except:
                    return [i['url'] for i in items if 'Source' in i['type']][0]
        except IndexError:
            addon_log('Preffered setting not found')
    elif preferred_quality == '1':
        try:
            url = [i['@url'] for i in media_content if
                   'Blip SD' in i['@blip:role'] or 'web' in i['@blip:role']][0]
            return url
        except IndexError:
            addon_log('Preffered setting not found')
    elif preferred_quality == '2':
        try:
            url = [i['@url'] for i in media_content if
                   'Blip LD' in i['@blip:role'] or 'Portable' in i['@blip:role']][0]
            return url
        except IndexError:
            addon_log('Preffered setting not found')
    elif preferred_quality == '3':
        try:
            dialog = xbmcgui.Dialog()
            ret = dialog.select(language(30006), [i['@blip:role'] for i in media_content])
            if ret > -1:
                return media_content[ret]['@url']
        except:
            addon_log('addonException: select stream: %s' %format_exc())
            return
    try:
        url = [i['@url'] for i in media_content if
               i.has_key('@isDefault') and i['@isDefault'] == 'true'][0]
        return url
    except IndexError:
        addon_log('addonException: did not find a default type')
        return media_content[0]['@url']


def get_podcasts():
    podcast_path = 'http://s3.roosterteeth.com/podcasts/'
    add_dir('RT Podcast', podcast_path + 'index.xml', 5, podcast_path + 'rtpodcast.jpg')
    add_dir('The Patch', podcast_path + 'gaming-index.xml', 5, podcast_path + 'gamingpodcast.jpg')
    add_dir('Spoilercast', podcast_path + 'spoiler-index.xml', 5, podcast_path + 'spoilercast_black.jpg')


def get_podcasts_episodes(url, iconimage):
    data = make_request(url)
    pod_dict = xmltodict.parse(data)
    items = pod_dict['rss']['channel']['item']
    for i in items:
        title = i['title'].encode('utf-8')
        date_time = datetime(*(time.strptime(i['pubDate'], '%a, %d %b %Y %H:%M:%S GMT')[0:6]))
        meta = {'Duration': get_duration(i['itunes:duration']),
                'Date': date_time.strftime('%d.%m.%Y'),
                'Premiered': date_time.strftime('%d-%m-%Y'),
                'Episode': title.split('#')[1]}
        add_dir('%s :  %s' %(title, i['description']),
                i['link'], 6, iconimage, meta, False, False)


def resolve_podcast_url(episode_url, retry=False):
    soup = get_soup(episode_url)
    is_video = soup('embed')
    if is_video:
        try:
            if 'swf#' in soup.embed['src']:
                blip_id = soup.embed['src'].split('swf#')[1]
                resolved = get_blip_location('http://blip.tv/play/' + blip_id)
                return resolved
        except:
            addon_log('addonException resolve_podcast_url: %s' %format_exc())
    elif retry:
        addon_log('No video embed found')
        sorry = check_sorry(soup)
        if not sorry:
            notify(language(30024))
    elif addon.getSetting('is_sponsor') == 'true':
        logged_in = check_login()
        if not logged_in:
            logged_in = login()
            if logged_in:
                return resolve_podcast_url(episode_url, True)
            notify(language(30025))
            xbmc.sleep(3000)
            sorry = check_sorry(soup)
    else:
        sorry = check_sorry(soup)
    if sorry:
        xbmc.sleep(5000)

    downloads = []
    items = soup.find('div', class_="titleLine", text="DOWNLOAD").findNext('div')('a')
    for i in items:
        downloads.append((i.b.contents[0], i['href']))
    if len(downloads) > 0:
        dialog = xbmcgui.Dialog()
        ret = dialog.select(language(30004), [i[0] for i in downloads])
        if ret > -1:
            return downloads[ret][1]


def set_resolved_url(resolved_url):
    success = False
    if resolved_url:
        success = True
    else:
        resolved_url = ''
    item = xbmcgui.ListItem(path=resolved_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)


def get_duration(duration):
    if duration is None:
        return 1
    d_split = duration.split(':')
    if len(d_split) == 4:
        del d_split[-1]
    minutes = int(d_split[-2])
    if int(d_split[-1]) >= 30:
        minutes += 1
    if len(d_split) >= 3:
        minutes += (int(d_split[-3]) * 60)
    if minutes < 1:
        minutes = 1
    return minutes


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


def add_dir(name, url, mode, iconimage, meta={}, season=False, isfolder=True):
    params = {'name': name, 'url': url, 'mode': mode, 'iconimage': iconimage, 'season': season}
    url = '%s?%s' %(sys.argv[0], urllib.urlencode(params))
    listitem = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    listitem.setProperty( "Fanart_Image", fanart )
    meta["Title"] = name
    meta['Genre'] = language(30026)
    if not isfolder:
        listitem.setProperty('IsPlayable', 'true')
    listitem.setInfo(type="Video", infoLabels=meta)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isfolder)


def check_login():
    logged_in = False
    cookies = {}
    cookie_jar.load(cookie_file, ignore_discard=False, ignore_expires=False)
    for i in cookie_jar:
        cookies[i.name] = i.value
    if cookies.has_key('rtusername') and cookies['rtusername'] == addon.getSetting('username'):
        logged_in = True
        addon_log('Already logged in')
    return logged_in


def login():
    url = 'https://roosterteeth.com/members/signinPost.php'
    username = addon.getSetting('username')
    login_data = {'pass': addon.getSetting('password'),
                  'user': username,
                  'return': '/sponsor/'}
    data = make_request(url, urllib.urlencode(login_data))
    soup = BeautifulSoup(data, 'html.parser')
    logged_in_tag = soup.find('span', attrs={'id': 'signedInName'})
    if logged_in_tag and username in str(logged_in_tag):
        addon_log('Logged in successfully')
        return True


def set_view_mode():
    view_modes = {
        '0': '502',
        '1': '51',
        '2': '3',
        '3': '504',
        '4': '503',
        '5': '515'
        }
    view_mode = addon.getSetting('view_mode')
    if view_mode == '6':
        return
    xbmc.executebuiltin('Container.SetViewMode(%s)' %view_modes[view_mode])


# check if dir exists, needed to save cookies to file
if not xbmcvfs.exists(addon_profile):
    xbmcvfs.mkdir(addon_profile)

params = get_params()

try:
    mode = int(params['mode'])
except:
    mode = None

addon_log(repr(params))

if mode == None:
    # display main plugin dir
    add_dir(language(30008), 'get_latest', 8, icon)
    add_dir(language(30005), 'get_podcasts', 4, icon)
    shows = eval(cache.cacheFunction(cache_shows))
    get_shows(shows['active'])
    add_dir(language(30007), 'get_retired_shows', 7, icon)
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 1:
    # display show, if seasons, else episodes
    soup = get_soup(params['url'])
    seasons = get_seasons(soup, params['iconimage'])
    if seasons:
        xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    else:
        index(soup, False)
        set_view_mode()
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 2:
    # display show episodes
    soup = get_soup(params['url'])
    index(soup, params['season'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 3:
    # resolve show episode
    set_resolved_url(resolve_url(params['url']))

elif mode == 4:
    # display podcast dir
    get_podcasts()
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 5:
    # display podcast episodes
    get_podcasts_episodes(params['url'], params['iconimage'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 6:
    # resolve podcast episode
    set_resolved_url(resolve_podcast_url(params['url']))

elif mode == 7:
    # display retired shows
    shows = eval(cache.cacheFunction(cache_shows))
    get_shows(shows['retired'])
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 8:
    # display latest episodes
    soup = get_soup('http://roosterteeth.com/archive/?sid=rvb&v=newest')
    index(soup, False)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))