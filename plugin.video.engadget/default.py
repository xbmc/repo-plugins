__author__ = "divingmule, and Hans van den Bogert"
__copyright__ = "Copyright 2015"
__license__ = "GPL"
__version__ = "2"
__maintainer__ = "Hans van den Bogert"
__email__ = "hansbogert@gmail.com"

import os
import urllib
import urllib2
import re
import json
import StorageServer
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
from urlparse import parse_qs, parse_qsl
from traceback import format_exc
import sys

addon = xbmcaddon.Addon()
addon_profile = xbmc.translatePath(addon.getAddonInfo('profile'))
addon_version = addon.getAddonInfo('version')
addon_id = addon.getAddonInfo('id')
addon_dir = xbmc.translatePath(addon.getAddonInfo('path'))
sys.path.append(os.path.join(addon_dir, 'resources', 'lib'))

# Do extra imports including from local addon dir
from bs4 import BeautifulSoup

cache = StorageServer.StorageServer("engadget", 1)
icon = addon.getAddonInfo('icon')
language = addon.getLocalizedString
base_url = 'http://www.engadget.com'


def addon_log(string):

    """

    :type string: string
    """
    try:
        log_message = string.encode('utf-8', 'ignore')
    except UnicodeEncodeError:
        log_message = 'addonException: addon_log'
    xbmc.log("[%s-%s]: %s" % (addon_id, addon_version, log_message), level=xbmc.LOGDEBUG)


def make_request(url):
    addon_log('Request URL: %s' % url)
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0',
        'Referer': base_url
        }
    try:
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data
    except urllib2.URLError, e:
        addon_log('We failed to open "%s".' % url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' % e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' % e.code)


def cache_categories():
    soup = BeautifulSoup(make_request(base_url + '/videos/'), 'html.parser')
    cat_items = soup.find('ul', class_='tab-nav')('a')
    cats = [{'name': i.string, 'href': i['href']} for i in cat_items]
    return cats


def display_categories():
    cats = cache.cacheFunction(cache_categories)
    for i in cats:
        add_dir(i['name'], i['href'], icon, 'get_category')


def display_category(url):
    page_url = base_url + url
    addon_log("Display items for page_url: " + page_url)
    html = make_request(page_url)
    soup = BeautifulSoup(html, 'html5lib')
    items = soup('div', {'class': 'video-listing'})
    for i in items:
        title = i('a', {'class': 'video-link'})[1].h3.string.encode('utf-8')
        link = i('a', {'class': 'video-link'})[1]['href']
        img = i('a', {'class': 'video-link'})[0].img['src']
        add_dir(title, link, img, 'resolve_url', False)

    next_page = soup.find('li', class_='older').a['href']
    add_dir(language(30008), next_page, icon, 'get_category')

    addon_log("Setting cache for page_url: " + page_url)
    cache.set('page_url', page_url)


def resolve_url(url):
    settings = {
        0: [16, 128],
        1: [32, 2, 1],
        2: [64, 4],
        3: [8]
        }
    preferred = int(addon.getSetting('preferred'))
    video_id = url.split('/')[-1]
    addon_log('video ID: {0}'.format(video_id))

    # TODO Caching should not be the concern of the function itself.
    try:
        link_cache = eval(cache.get('link_cache'))
        addon_log('Link cache loaded')
    except SyntaxError:
        link_cache = {}
        addon_log('addonException: %s' % format_exc())

    if video_id not in link_cache:
        addon_log("video id not in cache, re-caching")
        cache_playlist(video_id)
        link_cache = eval(cache.get('link_cache'))

    cached_item = link_cache[video_id]

    if cached_item:
        stream_url = urllib.unquote(cached_item['url'])
        addon_log('preferred setting: %s' % settings[preferred])
        resolved_url = None
        while (preferred >= 0) and not resolved_url:
            try:
                ren_id, ren_type = [
                    (i['ID'], i['RenditionType']) for i in cached_item['ren'] if i['ID'] in settings[preferred]][0]
                # Adhere to 5min's format, their base URL is always an MP4, but depending on the rendition type you
                # need the following to get an actual working URL
                resolved_url = stream_url.replace(".mp4", "_{0}.{1}".format(ren_id, ren_type))
                addon_log('Resolved: %s' % resolved_url)
            except IndexError:  # Assume that if we couldn't access [0], it isn't available
                addon_log('addonException: %s' % format_exc())
                addon_log('Setting unavailable: %s' % settings[preferred])
                preferred -= 1
        return resolved_url


def cache_playlist(video_id):
    url = 'http://syn.5min.com/handlers/SenseHandler.ashx?'
    script_url = 'http://www.engadget.com/embed-5min/?playList=%s&autoStart=true' % video_id
    addon_log("Get script: " + script_url)
    script_html = make_request(script_url)
    script_soup = BeautifulSoup(script_html, 'html.parser')
    param_list = parse_qsl(script_soup.script.attrs['src'].split("?")[1])
    script_params = dict(param_list)
    url_params = {
        'ExposureType': 'PlayerSeed',
        'autoStart': script_params['autoStart'],
        'cbCount': '3',
        # 'cbCustomID': script_params['cbCustomID'], ## No longer included
        'colorPallet': script_params['colorPallet'],
        'counter': '0',
        'filterString': '',
        'func': 'GetResults',
        'hasCompanion': script_params['hasCompanion'],
        'isPlayerSeed': 'true',
        'playlist': video_id,
        'relatedMode': script_params['relatedMode'],
        'sid': script_params['sid'],
        'url': urllib.quote(cache.get('page_url')),
        'videoCount': '50',
        'videoGroupID': script_params['videoGroupID']
    }
    addon_log("Cache for page_url was: " + cache.get('page_url'))
    addon_log("complete url: " + url + urllib.urlencode(url_params))
    data = json.loads(make_request(url + urllib.urlencode(url_params)), 'utf-8')
    items = data['binding']
    pattern = re.compile('videoUrl=(.+?)&')
    #   TODO Again, the caching - should not be here. This function should just get the file
    try:
        link_cache = eval(cache.get('link_cache'))
    except SyntaxError:
        # Cache is empty
        link_cache = {}

    if not isinstance(link_cache, dict):
        link_cache = {}

    if len(link_cache) > 300:
        addon_log("cache too full, clearing older items")
        link_cache.clear()

    for i in items:
        match = pattern.findall(i['EmbededURL'])
        addon_log("Regexp matches for videoUrl: " + match[0])
        try:
            item_dict = {str(i['ID']): {'url': match[0],
                                        'ren': i['Renditions']}}
            link_cache.update(item_dict)
        except (KeyError, IndexError):
            addon_log('addonException: %s' % format_exc())
    cache.set('link_cache', repr(link_cache))
    addon_log('link_cache items %s' % len(link_cache))


def add_dir(name, url, icon_image, dir_mode, is_folder=True):
    dir_params = {'name': name, 'url': url, 'mode': dir_mode}
    url = '%s?%s' % (sys.argv[0], urllib.urlencode(dir_params))
    list_item = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=icon_image)
    if not is_folder:
        list_item.setProperty('IsPlayable', 'true')
    list_item.setInfo(type="Video", infoLabels={'Title': name})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, is_folder)


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


def main():
    params = get_params()
    addon_log(repr(params))

    mode = params.get('mode')

    if mode is None:
        display_categories()
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    elif mode == 'get_category':
        display_category(params['url'])
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
    elif mode == 'resolve_url':
        success = False
        resolved_url = resolve_url(params['url'])
        if resolved_url:
            success = True
        else:
            resolved_url = ''
        item = xbmcgui.ListItem(path=resolved_url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)

if __name__ == "__main__":
    main()
