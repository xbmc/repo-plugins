import urllib
import urllib2
import re
import json
from operator import itemgetter
from urlparse import urlparse, parse_qs
from traceback import format_exc

import StorageServer
import SimpleDownloader as downloader
from bs4 import BeautifulSoup

import xbmcplugin
import xbmcgui
import xbmcaddon

addon = xbmcaddon.Addon()
language = addon.getLocalizedString
addon_id = addon.getAddonInfo('id')
icon = addon.getAddonInfo('icon')
fanart = addon.getAddonInfo('fanart')
base_url = 'http://www.archive.org'
cache = StorageServer.StorageServer("archiveorg", 6)
addon_version = addon.getAddonInfo('version')


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log: %s' %format_exc()
        print string
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message), level=xbmc.LOGDEBUG)


def make_request(url):
    addon_log('Request URL: %s' %url)
    try:
        req = urllib2.Request(url)
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
    return BeautifulSoup(data, 'html.parser')


def get_category_page(url, iconimage):
    soup = get_soup(url)
    if 'etree' in url:
        thumb = 'http://ia600202.us.archive.org/17/items/etree/lma.jpg'
    else:
        thumb = iconimage

    spotlight = soup.find('div', attrs={'id': "spotlight"})
    if spotlight:
        try:
            spotlight_url = spotlight('a')[1]['href']
        except:
            try:
                spotlight_url = spotlight('a')[0]['href']
            except:
                spotlight = None
    if spotlight:
        try:
            spotlight_name = spotlight('a')[1].string.encode('utf-8')
        except:
            try:
                spotlight_name = spotlight('a')[0].string.encode('utf-8')
            except:
                spotlight_name = 'Unknown'
        try:
            spotlight_thumb = spotlight.img['src']
        except:
            spotlight_thumb = thumb
        try:
            spotlight_desc = spotlight.get_text().encode('utf-8')
        except:
            addon_log(format_exc())
            spotlight_desc = ''
        add_dir('[COLOR=cyan]Spotlight Item:[/COLOR] %s' %spotlight_name,
                base_url + spotlight_url, spotlight_thumb.split('?')[0], 'get_media_details',
                ('video', {'plot': spotlight_desc}))

    # get search
    collection_tag = soup.find('select', attrs={'name': 'mediatype'}).find('option', selected='selected')
    if collection_tag:
        try:
            collection = collection_tag['value'].split('.')[1]
        except:
            collection = collection_tag['value']
        addon_log('Collection: %s' %collection)
        add_dir(language(30006), collection, thumb, 'search')

    # get filters
    filter_names = [
        'All items',
        'Browse by Subject / Keywords',
        'Browse by Language',
        'Browse All Artists with Recordings in the Live Music Archive',
        'Grateful Dead'
        ]
    for i in range(len(filter_names)):
        item = soup.find('a', text=re.compile(filter_names[i]))
        if item:
            name = filter_names[i]
            item_url = item['href']
            if item_url in url:
                continue
            if not item_url.startswith('http'):
                item_url = base_url + item_url
            if i == 0:
                mode = 'get_search_results'
            elif i == 1:
                mode = 'browse_keyword'
            elif i == 2:
                mode = 'browse_language'
            elif i == 3:
                mode = 'browse_by_artist'
            elif i == 4:
                if url != base_url + '/details/audio':
                    continue
                mode = 'get_category_page'
            add_dir(name, item_url, thumb, mode)
    if soup('div', attrs={'id' : "browseauthor"}):
        add_dir(language(30003), url, thumb, 'browse_by_author')
    if soup('div', attrs={'id' : "browsetitle"}):
        add_dir(language(30004), url, thumb, 'browse_by_title')

    # get subcollections
    subcollections = soup.find('div', attrs={'id' : 'subcollections'})
    if subcollections:
        for i in subcollections('tr'):
            count = i.nobr.string.encode('utf-8')
            if len(count) >= 1:
                try:
                    name = i('a')[1].string.encode('utf-8')
                except:
                    try:
                        name = i('a')[0].string.encode('utf-8')
                    except:
                        name = 'Unknown'
                url = base_url + i.a['href']
                try:
                    thumb = base_url + i.img['src']
                except:
                    pass
                desc = i.get_text().encode('utf-8')
                add_dir('%s (%s)' %(name, count), url, thumb, 'get_category_page',
                        ('video', {'plot': desc}))


def get_search_results(url, iconimage):
    soup = get_soup(url)
    try:
        items = soup('table', class_='resultsTable')[0]('tr')
    except IndexError:
        search_is_down_str = 'Search engine returned invalid information or was unresponsive'
        search_is_down = soup.find('b', text=search_is_down_str)
        if search_is_down:
            addon_log('archive search engine is down')
        return

    filter_items = soup('div', class_='box well well-sm')
    filters = []
    current_filter = ''
    pattern = re.compile('> (.+?) ')
    for i in filter_items:
        name = i.h4.string.encode('utf-8').strip(':')
        if name == 'Options': continue
        item_text = i.get_text(' | ')
        current = pattern.findall(item_text)
        if current:
            if current[0] == 'Average':
                current[0] = 'Rating'
            current_filter += '| %s %s ' %(item_text.split(' | ')[0], current[0])
        item_dict = {'name': name,
                     'items': [{'name': x.string.encode('utf-8'),
                                'url': x['href']} for x in i('a')]}
        filters.append(item_dict)
    cache.set('search_filters', repr(filters))
    if filters:
        add_dir('[COLOR=orange]Current Filters[/COLOR] ' + current_filter,
                'get_filters', iconimage, 'select_filters')

    for i in items:
        try:
            item_url = i.a['href']
        except:
            addon_log('No URL')
            print soup.prettify()
            continue
        if len(i.a.contents) > 1:
            name_list = []
            for n in i.a.contents:
                name_ = n.string
                if name_:
                    name_list.append(name_.encode('utf-8'))
            name = ''.join(name_list)
        else:
            name = i.a.string.encode('utf-8')
        desc = i.get_text('\n').split('Keywords:')[0].encode('utf-8')
        try:
            add_dir(name, base_url + item_url, iconimage, 'get_media_details', ('video', {'plot': desc}))
        except:
            addon_log('There was an error adding show Directory')
            addon_log(format_exc())

    try:
        page_url = soup.find('td', class_='pageRow')('a', text='Next')[0]['href']
        add_dir(language(30007), base_url + page_url, iconimage, 'get_search_results')
    except:
        addon_log('addonException page_url: %s' %format_exc())


def select_filters(iconimage):
    filters = eval(cache.get('search_filters'))
    dialog = xbmcgui.Dialog()
    filter_type = dialog.select('Choose Filter Type', [i['name'] for i in filters])
    if filter_type > -1:
        ret = dialog.select('Choose Filter', [i['name'] for i in filters[filter_type]['items']])
        if ret > -1:
            url = base_url + filters[filter_type]['items'][ret]['url']
            return get_search_results(url, iconimage)


def get_media_details(url, title, iconimage):
    if '[/COLOR]' in title:
        title = title.split('[/COLOR]')[1]
    data_url = url + '&output=json'
    response = make_request(data_url)
    try:
        data = json.loads(response)
    except ValueError:
        if response.startswith('<!DOCTYPE html>'):
            return get_category_page(url, iconimage)
        return
    desc = '\n'.join(['%s: %s' %(i.title().encode('utf-8'),
                        data['metadata'][i][0].encode('utf-8')) for
            i in data['metadata']])
    path = 'http://%s%s' %(data['server'], data['dir'])
    files_dict = {'item_url': url, 'item_type': data['misc']['css'],
                  'formats': {}, 'description': desc}
    for i in data['files'].iteritems():
        format_type = i[1]['format']
        i[1]['url'] = path + i[0]
        if not files_dict['formats'].has_key(format_type):
            files_dict['formats'][format_type] = []
        files_dict['formats'][format_type].append(i[1])
    cache.set('media_files', repr(files_dict))
    try:
        thumb = files_dict['Thumbnail'][0]['url']
    except:
        try:
            thumb = data['misc']['image']
        except:
            addon_log('addonException thumb: %s' %format_exc())
            thumb = iconimage
    playable_formats = [
        'VBR M3U', 'VBR ZIP', 'h.264', 'h.264 720P', 'DivX', 'HTTPS', 'VBR MP3', 'Ogg Vorbis',
        'QuickTime', 'Ogg Video', 'CD/DVD', 'MPEG1', 'MPEG4', '512Kb MPEG4', 'Shockwave Flash',
        'HiRes MPEG4', 'MPEG2', '64Kb MPEG4', '256Kb MPEG4', 'Cinepack', 'Windows Media', 'Flac',
        '128Kbps MP3', '64Kbps MP3', 'WAVE', '320Kbps MP3'
        ]
    other_formats = []
    item_type = files_dict['item_type']
    for i in files_dict['formats'].keys():
        if i in playable_formats:
            if len(files_dict['formats'][i]) == 1:
                item = files_dict['formats'][i][0]
                info = get_info(item, item_type, title)
                if item_type != 'audio':
                    info[1]['plot'] = desc
                add_dir('%s - %s' %(i.encode('utf-8'), info[1]['title']), item['url'], thumb, 'play', info)
            else:
                add_dir('%s - %s' %(i.encode('utf-8'), title), i, thumb, 'get_playable_items')
        else:
            other_formats.append(i)
    addon_log('None playable formats: %s' %other_formats)
    add_dir(language(30008), 'get_downloads', thumb, 'get_downloads')


def get_playable_items(files_dict_key, iconimage, title):
    if ' - ' in title:
        title = title.split(' - ', 1)[1]
    files_dict = eval(cache.get('media_files'))
    item_type = files_dict['item_type']
    items = files_dict['formats'][files_dict_key]
    if items[0].has_key('track'):
        sorted_items = sorted(items, key=itemgetter('track'))
    # elif items[0].has_key('title'):
        # sorted_items = sorted(items, key=itemgetter('title'))
    else:
        sorted_items = sorted(items, key=itemgetter('url'))
    for i in sorted_items:
        info = get_info(i, item_type, title)
        if item_type != 'audio':
            info[1]['plot'] = files_dict['description']
        add_dir(info[1]['title'], i['url'], iconimage, 'play', info)


def get_info(item_dict, item_type, title):
    size = int(item_dict['size'])
    try:
        item_title = item_dict['title']
    except:
        item_title = title
    if item_type != 'audio':
        info = ('video', {'title': item_title, 'size': size})
    else:
        track = ''
        artist = ''
        album = ''
        if item_dict.has_key('track'):
            track = item_dict['track']
        if 'Live at' in item_title:
            artist = title.split(' Live at')[0]
            album = title.split(artist)[1].strip()
        else:
            if item_dict.has_key('artist'):
                artist = item_dict['artist']
            elif item_dict.has_key('creator'):
                artist = item_dict['creator']
            if item_dict.has_key('album'):
                album = item_dict['album']
            elif artist and title.split(artist) > 1:
                try:
                    album = title.split(artist)[1].strip()
                except:
                    pass
        info = ('music', {'title': item_title, 'album': album, 'size': size,
                          'tracknumber': track, 'artist': artist})
    addon_log(repr(info))
    return info


def display_downloads():
    files_dict = eval(cache.get('media_files'))
    if files_dict['item_type'] == 'audio':
        zip_items = get_zip_files(files_dict['item_url'])
        if zip_items:
            for i in zip_items:
                url = i[1]
                if not url.startswith('http'):
                    url = base_url + url
                add_dir(i[0], url, icon, 'download')
    for i in files_dict['formats'].keys():
        for x in files_dict['formats'][i]:
            url = x['url']
            size = None
            if x.has_key('size'):
                size = x['size']
            if x.has_key('title'):
                item_title = x['title']
            else:
                item_title = url.split('/')[-1]
            if x['format'] == 'Thumbnail':
                iconimage = url
            else:
                iconimage = icon
            title = '%s - %s' %(x['format'], item_title)
            add_dir(title, url, iconimage, 'download', ('video', {'size': size}))


def get_zip_files(url):
    soup = get_soup(url)
    downloads = []
    try:
        items = soup.find('div', class_='box')('p', class_='content')
        for i in items:
            downloads.append((i.a.string, i.a['href']))
    except:
        addon_log('addonException get_zip_files: %s' %format_exc())
    if downloads:
        return downloads


def add_dir(name, url, iconimage, mode, info=[]):
    isfolder = True
    params = {'name': name, 'url': url, 'mode': mode, 'iconimage': iconimage}
    if mode in ['play', 'download']:
        isfolder = False
    if mode != 'play':
        url = '%s?%s' %(sys.argv[0], urllib.urlencode(params))
    listitem = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    listitem.setProperty("Fanart_Image", fanart)
    if info:
        listitem.setInfo(info[0], info[1])
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isfolder)


def browse_keyword(url, iconimage):
    soup = get_soup(url)
    add_items = [
        add_dir('%s %s' %(i.a.string.encode('utf-8'), i.contents[1].strip().encode('utf-8')),
                base_url + i.a['href'], icon, 'get_search_results') for
            i in soup.find('tr', valign='top')('li') if i.a.string
        ]


def browse_by_title(url, iconimage):
    soup = get_soup(url)
    items = soup('div', attrs={'id' : "browsetitle"})[0]('a')
    addon_log('Items: %s' %len(items))
    for i in items:
        try:
            name = i.string.encode('utf-8')
            href = i['href'].replace(' ', '%20')
            add_dir(name, base_url + href, iconimage, 'get_search_results')
        except:
            addon_log('There was an error adding Directory')


def browse_by_author(url, iconimage):
    soup = get_soup(url)
    items = soup('div', attrs={'id' : "browseauthor"})[0]('a')
    for i in items:
        try:
            name = i.string.encode('utf-8')
            href = i['href'].replace(' ', '%20')
            add_dir(name, base_url + href, iconimage, 'get_search_results')
        except:
            addon_log('There was an error adding Directory')


def browse_language(url, iconimage):
    soup = get_soup(url)
    items = soup('table', attrs={'id' : "browse"})[0]('a')
    for i in items:
        name = i.string.encode('utf-8')
        items = i.next.next[:-1].encode('utf-8')
        href = i['href']
        add_dir(name + items, base_url + i['href'], iconimage, 'get_search_results')


def browse_by_artist(url, iconimage):
    soup = get_soup(url)
    items = soup('table', attrs={'id' : "browse"})[0]('li')
    for i in items:
        name = i('a')[0].string.encode('utf-8')
        shows = i('a')[1].string.encode('utf-8')
        add_dir('%s ( %s )' %(name, shows), base_url + i.a['href'], iconimage, 'get_category_page')


def search(collection, iconimage):
    addon_log('Search collection: %s' %collection)
    keyboard = xbmc.Keyboard('', "Search")
    keyboard.doModal()
    if (keyboard.isConfirmed() == False):
        return
    search_string = keyboard.getText()
    if len(search_string) == 0:
        return
    query = urllib.quote('%s AND collection:%s' %(search_string, collection))
    search_url = 'http://www.archive.org/search.php?query=%s' %query
    get_search_results(search_url, iconimage)


def download_file(url, title):
    path = addon.getSetting('download')
    if path == "":
        xbmc.executebuiltin("XBMC.Notification(%s,%s,10000,%s)"
                %(language(30000), language(30010), icon))
        addon.openSettings()
        path = addon.getSetting('download')
    if path == "":
        return
    addon_log('######### Download #############')
    file_downloader = downloader.SimpleDownloader()
    if ' - ' in title:
        title = title.split(' - ', 1)[1]
    invalid_chars = ['>', '<', '*', '/', '\\', '?', '.']
    for i in invalid_chars:
        title = title.replace(i, '')
    name = title.replace(' ', '_')
    name += url.rsplit('/', 1)[1]
    if not '.' in name:
        if 'zip' in name.lower():
            name += '.zip'
        elif 'm3u' in name.lower():
            name += '.m3u'
        elif 'whole_directory' in name.lower():
            name += '.zip'

    params = {"url": url, "download_path": path, "Title": title}
    addon_log(str(params))
    file_downloader.download(name, params)
    addon_log('################################')


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


params = get_params()

try:
    mode = params['mode']
    addon_log('Mode: %s, Name: %s, URL: %s' %(mode, params['name'], params['url']))
except:
    addon_log('add first directory')
    mode = None

if mode == None:
    audio_url = 'http://www.archive.org/details/audio'
    audio_thumb = 'http://ia600304.us.archive.org/25/items/audio/audio.gif'
    video_url = 'http://www.archive.org/details/movies'
    video_thumb = 'http://ia700303.us.archive.org/0/items/movies/movies.gif'
    if params.has_key('content_type') and params['content_type'] == 'audio':
        get_category_page(audio_url, audio_thumb)
    elif params.has_key('content_type') and params['content_type'] == 'video':
        get_category_page(video_url, video_thumb)
    else:
        add_dir(language(30001), audio_url, audio_thumb, 'get_category_page')
        add_dir(language(30002), video_url, video_thumb, 'get_category_page')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_category_page':
    get_category_page(params['url'], params['iconimage'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_search_results':
    get_search_results(params['url'], params['iconimage'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'select_filters':
    select_filters(params['iconimage'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_media_details':
    get_media_details(params['url'], params['name'], params['iconimage'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'browse_by_author':
    browse_by_author(params['url'], params['iconimage'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'browse_by_title':
    browse_by_title(params['url'], params['iconimage'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'search':
    search(params['url'], params['iconimage'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'browse_keyword':
    browse_keyword(params['url'], params['iconimage'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'browse_language':
    browse_language(params['url'], params['iconimage'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'browse_by_artist':
    addon_log("browse_by_artist")
    browse_by_artist(params['url'], params['iconimage'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_downloads':
    display_downloads()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_playable_items':
    get_playable_items(params['url'], params['iconimage'], params['name'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'download':
    download_file(params['url'], params['name'])
