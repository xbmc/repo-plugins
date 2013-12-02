import re
import urllib
import urllib2
from urlparse import urlparse, parse_qs
from traceback import format_exc

import StorageServer
import xmltodict
from bs4 import BeautifulSoup

import xbmcplugin
import xbmcgui
import xbmcaddon

addon = xbmcaddon.Addon()
addon_version = addon.getAddonInfo('version')
addon_id = addon.getAddonInfo('id')
cache = StorageServer.StorageServer("zapiks", 24)
icon = addon.getAddonInfo('icon')
fanart = addon.getAddonInfo('fanart')
language = addon.getLocalizedString
base_url = 'http://www.zapiks.com'


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log'
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message), level=xbmc.LOGDEBUG)


def make_request(url, post_data=None):
    addon_log('Request URL: %s' %url)
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0',
        'Referer': base_url
        }
    try:
        req = urllib2.Request(url, post_data, headers)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data
    except urllib2.URLError, e:
        addon_log( 'We failed to open "%s".' % url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' %e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' %e.code)


def cache_categories():
    soup = BeautifulSoup(make_request(base_url), 'html.parser')
    items = soup('ul', attrs={'id' : "sports_navigation"})[0]('a')
    cats = [{'name': i.string.encode('utf-8'), 'url': i['href']} for i in items if i.string]
    return cats


def cache_pro_categories():
    label_list = ['marques', 'events', 'prods', 'riders', 'crews', 'media']
    label_dict = {}
    index = 30001
    for i in range(len(label_list)):
        index += 1
        label_dict[label_list[i]] = language(index)
    soup = BeautifulSoup(make_request('http://www.zapiks.com/pro/'), 'html.parser')
    pro_list = [{'label': label_dict[i.h2['class'][1].split('-')[1]],
                 'items': [{'title': x.a['title'].encode('utf-8'),
                            'url': x.a['href'],
                            'thumb': x.img['src']} for
            x in i('div', class_='pro-preview')]} for i in soup('div', class_='pro-type-bloc')]
    return pro_list


def display_pro_categories():
    for i in range(30002, 30008):
        add_dir(language(i), 'pro_cat', icon, 'get_pro_cat')


def display_pro_category(cat_name):
    cat_list = cache.cacheFunction(cache_pro_categories)
    items = [i['items'] for i in cat_list if i['label'] == cat_name][0]
    for i in items:
        add_dir(i['title'], i['url'], i['thumb'], 'get_category')


def display_categories():
    add_dir(language(30000), None, icon, 'get_partners')
    items = cache.cacheFunction(cache_categories)
    for i in items:
        add_dir(i['name'].title(), i['url'], icon, 'get_category')


def display_category(url):
    if url.endswith('_/'):
        nav = get_navigation(base_url + url)
        dir_name = 'Filters - '
        for i in nav['filters']:
            dir_name += '%s | ' %i['name']
        add_dir(dir_name, 'filter', icon, 'select_filter')
        soup = BeautifulSoup(make_request(base_url + nav['url']), 'html.parser')
    else:
        soup = BeautifulSoup(make_request(base_url + url), 'html.parser')
    if '/pro/' in url:
        items = soup('div', class_='media_thumbnail')
    else:
        items = soup.find('div', attrs={'id': 'list-media'})('div', class_='media_thumbnail')
    thumb_data = soup.find('style', attrs={'type': 'text/css'})
    thumb_items = thumb_data.get_text().replace(' ', '').split('@media')
    id_pattern = re.compile('thumbnail_container.(.+?){')
    url_pattern = re.compile("background-image:url\('(.+?)'\);")
    thumb_dict = {}
    for i in thumb_items:
        thumb_dict[id_pattern.findall(i)[0]] = url_pattern.findall(i)[0]
    for i in items:
        try:
            title = i.a['title'].encode('utf-8')
            thumb_id = i.div['class'][1]
            add_dir(title, base_url + i.a['href'], thumb_dict[thumb_id], 'resolve_url')
        except:
            addon_log('addonException display_category: %s' %format_exc())

    try:
        page_url = soup.find('h4', class_='page_navigator')('a', class_='next')[0]['href']
        if page_url and page_url != url:
            add_dir(language(30001), page_url, icon, 'get_category')
    except:
        pass


def get_navigation(url):
    soup = BeautifulSoup(make_request(url), 'html.parser')
    nav_tags = soup('div', class_='top-videos-block')
    page_url = soup.find('div', attrs={'id': 'central_block'}).a['href']
    nav = {'url': page_url,
           'filters': [{'name': i.a['title'].encode('utf-8').title(),
                        'url': i.a['href']} for
                            i in nav_tags]}
    cache.set('navigation', repr(nav))
    addon_log(repr(nav))
    return nav


def select_filter():
    nav = eval(cache.get('navigation'))
    dialog = xbmcgui.Dialog()
    ret = dialog.select(language(30009), [i['name'] for i in nav['filters']])
    if ret > -1:
        return display_category(nav['filters'][ret]['url'])


def resolve_url(url, thumb):
    video_id = thumb.split('/')[-1].split('-')[0]
    data_url = 'http://www.zapiks.fr/view/index.php'
    params = {
        'file': video_id,
        'lang': 'en',
        'referer': urllib.quote(url)
        }
    data = xmltodict.parse(make_request(data_url, urllib.urlencode(params)))
    if addon.getSetting('enable_hd') == 'true':
        try:
            return data['config']['hd.file']
        except:
            addon_log('addonException: hd.file: %s' %format_exc())
            pass
    return data['config']['file']


def add_dir(name, url, iconimage, mode):
    params = {'name': name, 'url': url, 'mode': mode, 'thumb': iconimage}
    url = '%s?%s' %(sys.argv[0], urllib.urlencode(params))
    listitem = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    isfolder = True
    if mode == 'resolve_url':
        isfolder = False
        listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty("Fanart_Image", fanart)
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

if mode == None:
    display_categories()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_category':
    display_category(params['url'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'resolve_url':
    success = False
    resolved_url = resolve_url(params['url'], params['thumb'])
    if resolved_url:
        success = True
    else:
        resolved_url = ''
    item = xbmcgui.ListItem(path=resolved_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)

elif mode == 'select_filter':
    select_filter()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_partners':
    display_pro_categories()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_pro_cat':
    display_pro_category(params['name'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))