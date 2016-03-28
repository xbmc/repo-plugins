import urllib
import urllib2
import re
import os
import json
import time
from traceback import format_exc
from urlparse import urlparse, parse_qs

from BeautifulSoup import BeautifulSoup
import StorageServer

import xbmcplugin
import xbmcgui
import xbmcaddon

base_url = 'http://on.aol.com'
cache = StorageServer.StorageServer("onaol", 1)
addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_version = addon.getAddonInfo('version')
addon_fanart = addon.getAddonInfo('fanart')
addon_icon = addon.getAddonInfo('icon')
addon_path = xbmc.translatePath(addon.getAddonInfo('path')
    ).encode('utf-8')
language = addon.getLocalizedString
next_png = os.path.join(addon_path, 'resources', 'next.png')


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


def get_cat_page(url):
    soup = BeautifulSoup(make_request(url),
                         convertEntities=BeautifulSoup.HTML_ENTITIES)
    page_dict = {}
    modules_tag = soup('div', attrs={'class': 'module'})
    page_dict['video_modules'] = get_videos(modules_tag)
    grids_tag = soup('div', attrs={'class': 'grid'})
    page_dict['video_grids'] = get_videos(grids_tag)
    if url == base_url:
        cat_tag = soup.find('ul',
                attrs={'class': 'nav layout-hidewhenmobile'})('li')
        cat_list = []
        for i in cat_tag:
            if i.a.div.string:
                c_dict = {'name': i.a.div.string,
                          'href': i.a['href']}
                cat_list.append(c_dict)
        page_dict['categories'] = cat_list
        channels_tag = soup.find('div', attrs={'class': 'menuParent'})('li')
        page_dict['channels'] = [{'name': i.div.contents[1],
                                  'href': i.a['href']} for i in channels_tag]
        page_dict['partners'] = get_partners(modules_tag[-1]
                ('div', attrs={'class': 'video videoItem'}))
    return page_dict


def get_partners(soup_list):
    partner_list = []
    for i in soup_list:
        p_dict = {}
        p_dict['title'] = i.find('meta', attrs={'name': 'title'}
                )['content'].encode('utf-8')
        p_dict['id'] = i.find('meta', attrs={'name': 'id'})['content']
        p_dict['href'] = base_url + i.a['href']
        p_dict['thumb'] = i.img['src']
        partner_list.append(p_dict)
    return partner_list


def get_videos(soup_tag):
    videos_list = []
    for i in soup_tag:
        v_dict = {}
        videos_tag = i('div', attrs={'class': 'video videoItem'})
        if not videos_tag:
            continue
        try:
            videos_name = unescape(i.h3.string.strip()).encode('utf-8')
            v_dict['name'] = videos_name.split(' (')[0]
        except:
            title_tag = i.find('div', attrs={'class': 'partner-header-title'})
            if title_tag:
                videos_name = unescape(title_tag.string).encode('utf-8')
                v_dict['name'] = videos_name.split(' (')[0]
            else:
                continue
        if 'Channels' in v_dict['name']:
            v_dict['partners'] = get_partners(videos_tag)
        else:
            v_dict['videos'] = get_video_items(videos_tag)
        more_pages = i.find('div', attrs={'class': 'add-more-button'})
        if more_pages and 'MORE VIDEOS' in more_pages.string:
            v_dict['pages'] = 'true'
        videos_list.append(v_dict)
    return videos_list


def get_video_items(soup_list):
    item_list = []
    for i in soup_list:
        vid = {}
        try:
            vid['thumb'] = i['data-img-mobile']
        except:
            try:
                vid['thumb'] = i('img')[1]['src']
            except:
                addon_log(format_exc())
                continue
        meta = {}
        for x in i('meta'):
            meta[x['name']] = x['content']
        vid['title'] = meta['title'].encode('utf-8')
        vid['id'] = meta['id']
        vid['info'] = {
                'plot': meta['videoDescription'].encode('utf-8'),
                'duration': duration_to_seconds(meta['duration']),
                'aired': format_date(meta['published'])}
        item_list.append(vid)
    return item_list


def get_movies(url):
    soup = BeautifulSoup(make_request(url),
                         convertEntities=BeautifulSoup.HTML_ENTITIES)
    all_movies_tab = soup('div', attrs={'class': 'video itemLarge'})
    # this html seems to come and go
    if all_movies_tab:
        movie_list = []
        for i in all_movies_tab:
            item = {'info': {}}
            layout_tag = i('div', attrs={'class': re.compile('save-r')})[0]
            item['id'] = layout_tag['data-id']
            title = i('div', attrs={'class':
                    'movie-show-title-name title'})[0]
            item['title'] = unescape(title.string.strip()).encode('utf-8')
            item['thumb'] = i('img', attrs={'class': 'poster'})[0]['src']
            item['fanart'] = i('img', attrs={'class': 'landscape'})[0]['src']
            item['info']['duration'] = layout_tag['data-duration']
            cast_tag = i.p('strong', text='Starring:')
            if cast_tag:
                cast = cast_tag[0].next.strip().encode('utf-8')
                item['info']['cast'] = cast.split(',')
            director = i('p')[1]('strong', text='Directors:')[0].next.strip()
            item['info']['director'] = director.encode('utf-8')
            item['info']['mpaa'] = i('div', attrs={'class': 'pg'})[0].string
            year = i('div', attrs={'class': 'year'})[0].string.strip('()')
            item['info']['year'] = year.encode('utf-8')
            plot = i.find('div', attrs={'class': 'desc'}).string
            item['info']['plot'] = unescape(plot).encode('utf-8')
            movie_list.append(item)
        return movie_list
    else:
        addon_log('Not All Movies')
        return get_video_items(
                soup('div', attrs={'class': 'video videoItem'}))



def get_shows():
    soup = BeautifulSoup(make_request(base_url + '/showAll/DEFAULT'),
            convertEntities=BeautifulSoup.HTML_ENTITIES)
    module_tag = soup.find('div', attrs={'class': 'module', 'index': '2'})
    items = module_tag('div', attrs={'class': 'video itemLarge'})
    show_list = []
    for i in items:
        item = {}
        href = i.find('div', attrs={'class': 'flipper'}).a['href']
        show_id = href.split('-shw')[1].split('?')[0]
        item['url'] = 'http://on.aol.com/showAll/episodes-SHW%s' %show_id
        desc = unescape(i('div', attrs={'class': 'desc'})[0].string
                ).encode('utf-8')
        item['info'] = {'plot':  '%s\n%s' %(i('div', attrs={'class': 'year'}
                )[0].string.encode('utf-8'), desc)}
        item['thumb'] = i.img['src']
        item['title'] = unescape(i.h1.string).encode('utf-8')
        show_list.append(item)
    return show_list


def display_page(url):
    data = cache.cacheFunction(get_cat_page, url)
    if len(data['video_grids']) < 1 and len(data['video_modules']) == 1:
        return display_module(data['video_modules'][0]['name'], url)
    elif len(data['video_grids']) == 1 and len(data['video_modules']) == 0:
        return display_module(data['video_grids'][0]['name'], url)
    if url == base_url:
        for i in data['categories']:
            add_dir(i['name'], i['href'], 'category', addon_icon)
    for i in data['video_modules']:
        add_dir(i['name'], url, 'module', addon_icon)
    for i in data['video_grids']:
        add_dir(i['name'], url, 'video_grid', addon_icon)


def display_category(name, url):
    if name == 'Channels':
        data = cache.cacheFunction(get_cat_page, base_url)
        items = data['channels']
        dialog = xbmcgui.Dialog()
        ret = dialog.select('Channels', [i['name'] for i in items])
        if ret >= 0:
            display_page(base_url + items[ret]['href'])
    if name == 'Movies':
        for i in cache.cacheFunction(get_movies, base_url + url):
            if i.has_key('fanart'):
                fanart = i['fanart']
            else:
                fanart = i['thumb']
            add_dir(i['title'], i['id'], 'video', i['thumb'],
                    i['info'], fanart)
    if name == 'Shows':
         data = cache.cacheFunction(get_shows)
         for i in data:
            add_dir(i['title'], i['url'], 'show', i['thumb'], i['info'])


def display_video_grid(name, url):
    data = cache.cacheFunction(get_cat_page, url)
    items = [i['videos'] for i in data['video_grids'] if i['name'] == name][0]
    for i in items:
        add_dir(i['title'], i['id'], 'video', i['thumb'], i['info'])


def display_module(name, url):
    data = cache.cacheFunction(get_cat_page, url)
    if 'Featured Partners' in name:
        for i in data['partners']:
            add_dir(i['title'], i['href'], 'partner', i['thumb'])
    elif 'Channels' in name:
        items = [i['partners'] for i in data['video_modules'] if
                i['name'] == name][0]
        for i in items:
            add_dir(i['title'], i['href'], 'partner', i['thumb'])
    else:
        items = [i for i in data['video_modules'] if
                i['name'] == name][0]
        for i in items['videos']:
            add_dir(i['title'], i['id'], 'video', i['thumb'], i['info'])
        if name.endswith(' All'):
            if items.has_key('pages'):
                add_dir(language(30007), url, 'get_all', next_png)


def display_episodes(show_url):
    soup = BeautifulSoup(make_request(show_url),
            convertEntities=BeautifulSoup.HTML_ENTITIES)
    grid_tag = soup.find('div', attrs={'class': 'grid carouselParent'})
    items = grid_tag('div', attrs={'class': 'video videoItem'})
    for i in items:
        meta = {}
        for x in i('meta'):
            meta[x['name']] = x['content']
        thumb = i['data-img-mobile']
        title = unescape(meta['episodeTitle'])
        info = {'season': int(meta['season']),
                'episode': int(meta['episode']),
                'duration': duration_to_seconds(meta['duration']),
                'aired': format_date(meta['published']),
                'plot': meta['videoDescription'].encode('utf-8')}
        add_dir(title.encode('utf-8'), meta['id'], 'video', thumb, info)


def get_all_partner(url):
    base = 'http://on.aol.com/search/partner'
    try:
        parsed_url = parse_qs(url.split('?')[1], keep_blank_values=1)
    except:
        partner_id = url.split('/')[-1]
        p_params = {'studioId': partner_id,
                    'limit': '24',
                    'sortOrder': 'most_recent',
                    'offset': '24',
                    'term': ''}
        url = '%s?%s' %(base, urllib.urlencode(p_params))
        parsed_url = parse_qs(url.split('?')[1], keep_blank_values=1)
    soup = BeautifulSoup(make_request(url),
                         convertEntities=BeautifulSoup.HTML_ENTITIES)
    grid_tag = soup('div', attrs={'class': 'partner-grid'})[0]
    items = grid_tag('div', attrs={'class': 'video videoItem'})
    for i in items:
        meta = {}
        for x in i('meta'):
            meta[x['name']] = x['content']
        thumb = i('img')[1]['src']
        add_dir(meta['title'].encode('utf-8'), meta['id'], 'video', thumb,
                {'plot': meta['videoDescription'].encode('utf-8'),
                 'aired': format_date(meta['published']),
                 'duration': duration_to_seconds(meta['duration'])})
    if len(items) >= 24:
        p_params = {}
        for i in parsed_url.keys():
            p_params[i] = parsed_url[i][0]
        p_params['offset'] = int(p_params['offset']) + 24
        page_url = '%s?%s' %(base, urllib.urlencode(p_params))
        add_dir(language(30007), page_url, 'partner', next_png)


def add_dir(name, url, mode, iconimage, info={}, fanart=None):
    item_params = {'name': name, 'url': url, 'mode': mode}
    plugin_url = '%s?%s' %(sys.argv[0], urllib.urlencode(item_params))
    listitem = xbmcgui.ListItem(name, iconImage=iconimage,
                                thumbnailImage=iconimage)
    isfolder = True
    if mode == 'video':
        isfolder = False
        listitem.setProperty('IsPlayable', 'true')
    if fanart is None:
        fanart = addon_fanart
    listitem.setProperty('Fanart_Image', fanart)
    listitem.setInfo(type = 'video', infoLabels = info)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), plugin_url,
                                listitem, isfolder)


def resolve_url(video_id):
    resolved_url = ''
    success = False
    quality_types = {'0': 'LD', '1': 'SD', '2': 'HD'}
    j_url = 'http://feedapi.b2c.on.aol.com/v1.0/app/videos/aolon/%s/details'
    data = json.loads(make_request(j_url %video_id))
    renditions = data['response']['data']['renditions']
    if renditions:
        for i in renditions:
            if quality_types[addon.getSetting('qual')] in i['quality']:
                resolved_url = i['url']
                break
        if not resolved_url:
            hd = [i['url'] for i in renditions if 'HD' in i['quality']]
            sd = [i['url'] for i in renditions if 'SD' in i['quality']]
            ld = [i['url'] for i in renditions if 'LD' in i['quality']]
            if sd:
                resolved_url = sd[0]
            elif hd:
                resolved_url = hd[0]
            elif ld:
                resolved_url = ld[0]
            else:
                try:
                    resolved_url = renditions[0]['url']
                except:
                    pass
    if resolved_url:
        success = True
    item = xbmcgui.ListItem(path=resolved_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)


def duration_to_seconds(duration):
    if ':' in duration:
        d = duration.split(':')
        if len(d) == 2:
            return(int(d[0]) * 60) + int(d[1])
        elif len(d) == 3:
            return((int(d[0]) * 60) + int(d[1]) * 60) + int(d[2])
    else:
        return duration


def format_date(date_string):
    time_object = time.strptime(date_string, '%m/%d/%Y')
    return time.strftime('%Y/%m/%d', time_object)


## Thanks to Fredrik Lundh for this function -
## http://effbot.org/zone/re-sub.htm#unescape-html
def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


params = get_params()

mode = None

try:
    mode = params['mode']
    addon_log('Mode: %s, Name: %s, URL: %s' %
              (params['mode'], params['name'], params['url']))
except:
    addon_log('Get root directory')

if mode is None:
    display_page(base_url)
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'category':
    display_category(params['name'], params['url'])
    if params['name'] == 'Movies':
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    else:
        xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'video_grid':
    display_video_grid(params['name'], params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'module':
    display_module(params['name'], params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'partner':
    display_page(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'show':
    display_episodes(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_all':
    get_all_partner(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'video':
    resolve_url(params['url'])
