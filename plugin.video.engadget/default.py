__author__ = "divingmule, and Hans van den Bogert"
__copyright__ = "Copyright 2013"
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
import xbmcplugin
import xbmcgui
import xbmcaddon
from urlparse import urlparse, parse_qs
from traceback import format_exc

addon = xbmcaddon.Addon()
addon_profile = xbmc.translatePath(addon.getAddonInfo('profile'))
addon_version = addon.getAddonInfo('version')
addon_id = addon.getAddonInfo('id')
addon_dir = xbmc.translatePath(addon.getAddonInfo('path'))
sys.path.append(os.path.join(addon_dir, 'resources', 'lib'))

# Do extra imports including html5lib from local addon dir
import html5lib
from bs4 import BeautifulSoup

cache = StorageServer.StorageServer("engadget", 24)
icon = addon.getAddonInfo('icon')
language = addon.getLocalizedString
base_url = 'http://www.engadget.com'


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
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
    soup = BeautifulSoup(make_request(base_url + '/videos'), 'html.parser')
    cat_items = soup.find('ul', class_='tab-nav')('a')
    cats = [{'name': i.string, 'href': i['href']} for i in cat_items]
    return cats


def display_categories():
    cats = cache.cacheFunction(cache_categories)
    for i in cats:
        add_dir(i['name'], i['href'], icon, 'get_category')


def display_category(url):
    page_url = base_url + url
    html = make_request(page_url)
    soup = BeautifulSoup(html, 'html5lib')
    items = soup('div', {'class': 'video-listing'})[0]('div', {'class': 'video'})
    for i in items:
        title = i('a', {'class': 'video-link'})[1].h3.string.encode('utf-8')
        link = i('a', {'class': 'video-link'})[1]['href']
        img = i('a', {'class': 'video-link'})[0].img['src']
        add_dir(title, link, img, 'resolve_url', False)
    try:
        next_page = soup.find('li', class_='older').a['href']
        add_dir(language(30008), next_page, icon, 'get_category')
    except:
        pass
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

    try:
        link_cache = eval(cache.get('link_cache'))
        item = [(i[video_id]['url'], i[video_id]['ren']) for i in link_cache if video_id in i][0]
        addon_log('return item from cache')
    except:
        addon_log('addonException: %s' % format_exc())
        item = cache_playlist(video_id)
    if item:
        extension_format = '_%s.%s?cat=Tech&subcat=Web'
        stream_url = urllib.unquote(item[0]).split('.mp4')[0]
        addon_log('preferred setting: %s' % settings[preferred])
        resolved_url = None
        while (preferred >= 0) and not resolved_url:
            try:
                ren_id, ren_type = [
                    (i['ID'], i['RenditionType']) for i in item[1] if i['ID'] in settings[preferred]][0]
                resolved_url = stream_url + extension_format % (ren_id, ren_type)
                addon_log('Resolved: %s' % resolved_url)
            except:
                addon_log('addonException: %s' % format_exc())
                addon_log('Setting unavailabel: %s' % settings[preferred])
                preferred -= 1
        return resolved_url


def cache_playlist(video_id):
    url = 'http://syn.5min.com/handlers/SenseHandler.ashx?'
    script_url = 'http://www.engadget.com/embed-5min/?playList=%s&autoStart=true' % video_id
    script_html = make_request(script_url)
    # workaround: soup dies on the script tag
    script_html2 = script_html.replace('</scr" + "ipt>"', "")
    script_soup = BeautifulSoup(script_html2, 'html.parser')
    script = script_soup.script.get_text()
    # FIXME: There is a security risk in eval() because the originating text stems from the server
    # Why the original author ever wanted to include a javascript snippet, which happens to be valid
    # python syntax, is beyond me
    script_params = eval((script[5:].replace('\r\n', '').split(';')[0]))
    params = {
        'ExposureType': 'PlayerSeed',
        'autoStart': script_params['autoStart'],
        'cbCount': '3',
        'cbCustomID': script_params['cbCustomID'],
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
    data = json.loads(make_request(url + urllib.urlencode(params)), 'utf-8')
    items = data['binding']
    pattern = re.compile('videoUrl=(.+?)&')
    try:
        link_cache = eval(cache.get('link_cache'))
        if len(link_cache) > 300:
            del link_cache[:100]
    except:
        addon_log('addonException: %s' % format_exc())
        link_cache = []
    for i in items:
        match = pattern.findall(i['EmbededURL'])
        try:
            item_dict = {str(i['ID']): {'url': match[0],
                                        'ren': i['Renditions']}}
            link_cache.append(item_dict)
        except:
            addon_log('addonException: %s' % format_exc())
    cache.set('link_cache', repr(link_cache))
    addon_log('link_cache items %s' % len(link_cache))
    try:
        return [(i[video_id]['url'], i[video_id]['ren']) for i in link_cache if video_id in i][0]
    except:
        addon_log('addonException: %s' % format_exc())


def add_dir(name, url, iconimage, mode, isfolder=True):
    params = {'name': name, 'url': url, 'mode': mode}
    url = '%s?%s' % (sys.argv[0], urllib.urlencode(params))
    listitem = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if not isfolder:
        listitem.setProperty('IsPlayable', 'true')
    listitem.setInfo(type="Video", infoLabels={'Title': name})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isfolder)


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


params = get_params()
addon_log(repr(params))

try:
    mode = params['mode']
except:
    mode = None

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
