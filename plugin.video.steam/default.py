import urllib
import urllib2
import cookielib
import re
from urlparse import urlparse, parse_qs
from traceback import format_exc

import StorageServer
from bs4 import BeautifulSoup

import xbmcplugin
import xbmcgui
import xbmcaddon

addon = xbmcaddon.Addon()
addon_version = addon.getAddonInfo('version')
addon_id = addon.getAddonInfo('id')
icon = addon.getAddonInfo('icon')
language = addon.getLocalizedString
fanart = 'http://www.deviantart.com/download/245134540/steam_logo_by_thegreatjug-d41y30s.png'
cache = StorageServer.StorageServer("Steam", 1)
cookie_jar = cookielib.LWPCookieJar()


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log'
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message), level=xbmc.LOGDEBUG)


def make_request(url, data=None, headers=None):
    addon_log('Request URL: %s' %url)
    if headers is None:
        headers = {
            'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:25.0) Gecko/20100101 Firefox/25.0',
            'Referer': 'http://store.steampowered.com'
            }
    try:
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
        urllib2.install_opener(opener)
        req = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(req)
        data = response.read()
        # addon_log(str(response.info()))
        response.close()
        return data
    except urllib2.URLError, e:
        addon_log('We failed to open "%s".' %url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' %e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' %e.code)


def get_soup(url):
    data = make_request(url)
    if data:
        return BeautifulSoup(data, 'html.parser')


def cache_homepage():
    soup = get_soup('http://store.steampowered.com/freestuff/videos')
    genre_tag = soup.find('div', attrs={'id': 'genre_flyout'})
    genre_items = genre_tag('div', class_='popup_body')[0]('a')
    genres = [{'name': i.string.strip().encode('utf-8'),
               'url': i['href']} for i in genre_items]

    most_watched_items = soup.find('div', class_='block_content')('div', class_='top_video_capsule')
    most_watched_list = [{'desc': '\n'.join([y.string.strip() for y in i('p')]),
                          'thumb': i.img['src'],
                          'title': i('a')[-1].string.encode('utf-8'),
                          'url': i.a['href']} for i in most_watched_items]

    try:
        page_tag = soup.find('div', attrs={'id': "tab_NewVideos_next"}).a['href']
        page_pattern = re.compile(
            'javascript:PageTab\(\'(.+?)\', (.+?), .+?, '
            '{"cc":"(.+?)","l":"(.+?)","style":".+?","navcontext":"(.+?)"}\)')
        match = page_pattern.findall(page_tag)
        params = {'tab':  match[0][0],
                  'start':  int(match[0][1]) + 10,
                  'cc':  match[0][2],
                  'l':  match[0][3],
                  'navcontext':  match[0][4],
                  'style': 'video',
                  'count': 10}
        page_url = 'http://store.steampowered.com/search/tab?' + urllib.urlencode(params)
    except:
        addon_log('addonException page_url: %s' %format_exc())
        page_url = None

    video_list = get_new_videos(soup)

    homepage_dict = {'most_watched': most_watched_list,
                     'new_videos': video_list,
                     'genres': genres,
                     'next_video_page': page_url}
    return homepage_dict


def get_new_videos(soup):
    video_items = soup.find_all('div', attrs={'id': re.compile('tab_row_NewVideos')})
    video_list = [{'desc': '\n'.join([y.string.encode('utf-8') for
                            y in i.find('div', class_='tab_video_desc')('p')]),
                   'thumb': i.find('img', class_='movie_cap_img')['src'],
                   'title': i.find('div', class_='tab_video_desc').a.string.encode('utf-8'),
                   'url': i.find('div', class_='tab_video_desc').a['href']} for i in video_items]
    return video_list


def display_categories():
    add_dir(language(30001), 'new_videos', icon, 'get_new_videos')
    add_dir(language(30002), 'by_genre', icon, 'get_by_genre')
    add_dir(language(30003), 'most_watched', icon, 'get_most_watched')
    add_dir(language(30004), 'search', icon, 'search')


def display_new_videos(url):
    if url == 'new_videos':
        data = cache.cacheFunction(cache_homepage)
        items = data['new_videos']
        page_url = data['next_video_page']
    else:
        soup = get_soup(url)
        items = get_new_videos(soup)
        try:
            p = url.split('?')[1]
            params = {'tab': p.split('tab=')[1].split('&')[0],
                      'start': int(p.split('start=')[1].split('&')[0]) + 10,
                      'cc': p.split('cc=')[1].split('&')[0],
                      'l':  p.split('l=')[1].split('&')[0],
                      'navcontext': p.split('navcontext=')[1].split('&')[0],
                      'count': 10,
                      'style': 'video'}
            page_url = 'http://store.steampowered.com/search/tab?' + urllib.urlencode(params)
        except:
            addon_log('addonException page_url: %s' %format_exc())
            page_url = None

    for i in items:
        add_dir(i['title'], i['url'], i['thumb'], 'resolve_url', {'plot': i['desc']})
    if page_url:
        add_dir(language(30005), page_url, icon, 'get_new_videos')


def display_most_watched():
    data = cache.cacheFunction(cache_homepage)
    for i in data['most_watched']:
        add_dir(i['title'], i['url'], i['thumb'], 'resolve_url', {'plot': i['desc']})


def display_genres():
    data = cache.cacheFunction(cache_homepage)
    item_url = 'http://store.steampowered.com/search/?genre=%s&category1=999'
    for i in data['genres']:
        add_dir(i['name'], item_url %(urllib.quote(i['name'])), icon, 'get_videos')


def display_videos(url):
    soup = get_soup(url)
    items = soup.find('div', attrs={'id': "search_result_container"})('a')
    for i in items:
        if re.search('video', i['href']):
            name = i.h4.string.encode('utf-8')
            thumb = i('img')[1]['src'].rsplit('/', 1)[0]+'/header.jpg'
            desc = i.p.string.strip().encode('utf-8')
            add_dir(name, i['href'], thumb, 'resolve_url', {'Plot': desc})

    try:
        page_items = soup.find('div', class_="search_pagination_right")('a')
        for i in page_items:
            if i.string.encode('iso-8859-1') == '>>':
                add_dir(language(30005), i['href'], icon, 'get_videos')
    except:
        addon_log(format_exc())


def search():
    keyboard = xbmc.Keyboard('','Search')
    keyboard.doModal()
    if (keyboard.isConfirmed() == False):
        return
    search_string = keyboard.getText()
    if len(search_string) == 0:
        return
    url = 'http://store.steampowered.com/search/?term='
    url += urllib.quote_plus(search_string)
    return display_videos(url)


def resolve_url(url):
    resolved_url = None
    data = make_request(url)
    if re.search('<h2>Please enter your birth date to continue:</h2>', data):
        addon_log('AGE CHECK')
        agecheck_params = '/?ageDay=1&ageMonth=January&ageYear=1980&snr=1_agecheck_agecheck__age-gate'
        if '/app/' in url:
            url = url.replace('/app/','/agecheck/app/').split('?')[0] + agecheck_params
        elif '/video/' in url:
            url = url.replace('/video/','/agecheck/video/').split('?')[0] + agecheck_params
        data = make_request(url)
    filenames = re.findall('FILENAME: "(.+?)"', data)
    video_id = url.split('?')[0].split('/')[-1]
    files = []
    for i in filenames:
        if video_id in i:
            resolved_url = i
            break
        else:
            files.append(i)
    if not resolved_url:
        if len(files) > 0:
            addon_log('video_id not in file')
            resolved_url = files[0]
    return resolved_url


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


def add_dir(name, url, iconimage, mode, info={}):
    params = {'name': name, 'url': url, 'mode': mode}
    url = '%s?%s' %(sys.argv[0], urllib.urlencode(params))
    listitem = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    isfolder = True
    if mode == 'resolve_url':
        isfolder = False
        listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty("Fanart_Image", fanart)
    listitem.setInfo(type="Video", infoLabels=info)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isfolder)


def set_view_mode():
    view_modes = {
        '0': '502',
        '1': '51',
        '2': '500',
        '3': '504',
        '4': '503',
        '5': '515'
        }
    view_mode = addon.getSetting('view_mode')
    if view_mode == '6':
        return
    xbmc.executebuiltin('Container.SetViewMode(%s)' %view_modes[view_mode])



params = get_params()

addon_log(repr(params))

try:
    mode = params['mode']
except:
    mode = None

if mode == None:
    display_categories()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_new_videos':
    display_new_videos(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_most_watched':
    display_most_watched()
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_by_genre':
    display_genres()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'search':
    search()
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_videos':
    display_videos(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
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
