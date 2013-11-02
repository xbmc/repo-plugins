import urllib
import urllib2
import re
import json
from urlparse import urlparse, parse_qs
from traceback import format_exc

import xmltodict
import StorageServer
from bs4 import BeautifulSoup

import xbmcplugin
import xbmcgui
import xbmcaddon

cache = StorageServer.StorageServer("roosterteeth", 24)
addon = xbmcaddon.Addon()
addon_version = addon.getAddonInfo('version')
addon_id = addon.getAddonInfo('id')
home = addon.getAddonInfo('path')
icon = addon.getAddonInfo('icon')
fanart = addon.getAddonInfo('fanart')
base = 'http://roosterteeth.com'
language = addon.getLocalizedString


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log'
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message),level=xbmc.LOGDEBUG)


def make_request(url, location=False):
    addon_log('Request URL: %s' %url)
    try:
        headers = {
            'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0',
            'Referer': 'http://roosterteeth.com'
            }
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)
        response_url = urllib.unquote_plus(response.geturl())
        data = response.read()
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
        return BeautifulSoup(data)


def cache_shows():

    def filter_items(item_list):
        parsed = []
        for i in item_list:
            try:
                show = (i.b.string, i.a['href'], i.img['src'])
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
        add_dir(i[0], base+i[1], 1, i[2])


def get_seasons(soup, iconimage):
    try:
        items = soup('td', class_="seasonsBox")[0]('a')
        if len(items) < 1:
            raise
    except IndexError:
        addon_log('Seasons Exception: %s' %format_exc())
        return False
    for i in items:
        add_dir(i.string, base+i['href'], 2, iconimage, '', True)
    return True


def index(soup, season=True):
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
        duration = i.td.string
        if duration is None:
            diration = ''
        add_dir(name.encode('utf-8', 'ignore'), item_id, 3, thumb, duration, False, False)
    try:
        next_page = soup('a', attrs={'id' : "streamLoadMore"})[0]['href']
        add_dir(language(30002), base + next_page, 2, icon, '', season)
    except:
        addon_log("Didn't find next page!")


def resolve_url(item_id):
    url = 'http://roosterteeth.com/archive/new/_loadEpisode.php?id=%s&v=morev' %item_id
    data = json.loads(make_request(url))
    soup = get_soup(data['embed']['html'])
    try:
        filetype = soup.div['data-filetype']
        if filetype == 'youtube':
            youtube_id = soup.iframe['src'].split('/')[-1].split('?')[0]
            addon_log('youtube id:' + youtube_id)
            path = 'plugin://plugin.video.youtube/?action=play_video&videoid='+youtube_id
        elif filetype == 'blip':
            blip_url = soup.iframe['src']
            addon_log('blip_url: ' + blip_url)
            path = get_blip_location(blip_url)
            addon_log('path: %s' %path)
    except:
        sorry = "Sorry, you must be a Sponsor to see this video."
        if sorry in str(soup):
            xbmc.executebuiltin("XBMC.Notification(%s,%s,5000,%s)"
                                %(language(30000), language(30003), icon))
            addon_log(sorry)
            return
        else:
            addon_log('addonException: %s' %format_exc())
            return
    return path


def get_blip_location(blip_url):
    blip_data = make_request(blip_url, True)
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
        add_dir('%s :  %s' %(i['title'], i['description']),
                i['link'], 6, iconimage, i['itunes:duration'], False, False)


def resolve_podcast_url(episode_url):
    soup = get_soup(episode_url)
    is_video = soup('embed')
    blip_id = None
    if is_video:
        if 'swf#' in soup.embed['src']:
            blip_id = soup.embed['src'].split('swf#')[1]
    if blip_id:
        resolved = get_blip_location('http://blip.tv/play/' + blip_id)
        if resolved:
            return resolved

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


def add_dir(name, url, mode, iconimage, duration=None, season=False, isfolder=True):
    params = {'name': name, 'url': url, 'mode': mode, 'iconimage': iconimage, 'season': season}
    url = '%s?%s' %(sys.argv[0], urllib.urlencode(params))
    listitem = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    listitem.setProperty( "Fanart_Image", fanart )
    infolabels = {"Title": name}
    if not isfolder:
        listitem.setProperty('IsPlayable', 'true')
        if duration:
            infolabels['Duration'] = get_duration(duration)
    listitem.setInfo(type="Video", infoLabels=infolabels)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isfolder)


params = get_params()

try:
    mode = int(params['mode'])
except:
    mode = None

addon_log(repr(params))

if mode == None:
    add_dir(language(30008), 'get_latest', 8, icon)
    add_dir(language(30005), 'get_podcasts', 4, icon)
    shows = eval(cache.cacheFunction(cache_shows))
    get_shows(shows['active'])
    add_dir(language(30007), 'get_retired_shows', 7, icon)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 1:
    soup = get_soup(params['url'])
    seasons = get_seasons(soup, params['iconimage'])
    if not seasons:
        index(soup, False)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 2:
    soup = get_soup(params['url'])
    index(soup, params['season'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 3:
    set_resolved_url(resolve_url(params['url']))

elif mode == 4:
    get_podcasts()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 5:
    get_podcasts_episodes(params['url'], params['iconimage'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 6:
    set_resolved_url(resolve_podcast_url(params['url']))

elif mode == 7:
    shows = eval(cache.cacheFunction(cache_shows))
    get_shows(shows['retired'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 8:
    soup = get_soup('http://roosterteeth.com/archive/?sid=rvb&v=newest')
    index(soup, False)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
