import urllib
import urllib2
import re
import os
from urlparse import urlparse, parse_qs

import StorageServer
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

import xbmcplugin
import xbmcgui
import xbmcaddon

base_url = 'http://www.foodnetwork.com'
addon = xbmcaddon.Addon()
addon_version = addon.getAddonInfo('version')
addon_id = addon.getAddonInfo('id')
cache = StorageServer.StorageServer("foodnetwork", 6)
home = xbmc.translatePath(addon.getAddonInfo('path'))
icon = addon.getAddonInfo('icon')
language = addon.getLocalizedString
debug = addon.getSetting('debug')


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log'
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message),level=xbmc.LOGDEBUG)
    
    
def make_request(url):
    addon_log('Request URL: ' + url)
    try:
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0',
                   'Referer' : base_url}
        req = urllib2.Request(url,None,headers)
        response = urllib2.urlopen(req)
        data = response.read()
        addon_log('ResponseInfo: %s' %response.info())
        response.close()
        return data
    except urllib2.URLError, e:
        addon_log('We failed to open "%s".' %url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' %e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' %e.code)


def cache_shows():
    cat = {
        'videos': {'url': base_url+'/food-network-top-food-videos/videos/index.html'},
        'episodes': {'url': base_url+'/food-network-full-episodes/videos/index.html'}
        }
    for i in cat.keys():
        soup = BeautifulSoup(make_request(cat[i]['url']), convertEntities=BeautifulSoup.HTML_ENTITIES)
        play_lists = []
        playlists = soup.find('ul', attrs={'class': 'playlists'})('li')
        for p in playlists:
            play_lists.append((p.a.string, p['data-channel'], p.a['href']))
        cat[i]['playlists'] = play_lists
        if not cat.has_key('most_popular'):
            most_popular = soup.find('h4', text='Videos').findNext('ul', attrs={'class': 'media'})('a')
            video_list = []
            for m in most_popular:
                video_list.append((m.string, m['href']))
            cat['most_popular'] = video_list
    return cat


def get_categories():
    add_dir(language(30000), 'episodes', 1, icon)
    add_dir(language(30001), 'videos', 1, icon)
    add_dir(language(30002), 'most_popular', 1, icon)
    add_dir(language(30003), 'all_shows', 5, icon)


def get_cat(url):
    if url == 'most_popular':
        items = cache.cacheFunction(cache_shows)[url]
        for i in items:
            add_dir(i[0], i[1], 3, icon, {}, False)
    else:
        items = cache.cacheFunction(cache_shows)[url]['playlists']
        for i in items:
            title = i[0]
            if title.endswith('Full Episodes'):
                title = title.replace('Full Episodes','').replace(' - ','')
            add_dir(title, i[2], 2, icon)


def get_all_shows():
    show_file = os.path.join(home, 'resources', 'show_list')
    show_list = eval(open(show_file, 'r').read())
    for i in show_list:
        if i.has_key('video_href'):
            if i.has_key('thumb'): thumb = i['thumb']
            else: thumb = icon
            add_dir(i['name'], i['video_href'], 6, thumb)


def get_video_xml(url, show=False):
    video_id = None
    try:
        if int(eval(url)):
            video_id = eval(url)
    except: pass
    if not video_id:
        if url.startswith('/'):
            url = base_url+url
        data = make_request(url)
        if show:
            playlists = None
            soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
            try:
                playlists = soup.find('ul', attrs={'class': "playlists"})('li')
            except: pass
            if playlists:
                for i in playlists:
                    add_dir(i.a.string, i.a['href'], 2, icon)
                xbmcplugin.endOfDirectory(int(sys.argv[1]))
                return
        try:
            video_id = re.findall('var snap = new SNI.Food.Player.VideoAsset\(.+?, (.+?)\);', data)[0]
        except:
            try:
                video_id = re.findall('var snap = new SNI.Food.Player.FullSize\(.+?, (.+?)\);', data)[0]
            except:
                try:
                    video_id = re.findall('var snap = new SNI.Food.Player.FullSizeNoPlaylist\(.+?, (.+?)\);', data)[0]
                except:
                    addon_log('Unable to find video_id')
    if video_id:
        xml_url = 'http://www.foodnetwork.com/food/channel/xml/0,,%s,00.xml' %video_id
        soup = BeautifulStoneSoup(make_request(xml_url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        if show:
            for i in soup('video'):
                add_dir(i.clipname.string, i.videourl.string, 4, i.thumbnailurl.string,
                        {'Plot': i.abstract.string, 'Duration': get_length_in_minutes(i.length.string)}, False)
            xbmcplugin.endOfDirectory(int(sys.argv[1]))
        else:
            resolve_url(soup.video.videourl.string)


def get_playlist(url, name):
    if not name == language(30005):
        playlist_url = url.rsplit(',', 1)[0].rsplit('/', 1)[1]
    else: playlist_url = url
    json_url = '%s/food/feeds/channel-video/%s_RA,00.json' %(base_url, playlist_url)
    items = eval(make_request(json_url).split('var snapTravelingLib = ')[1])[0]
    for i in items['videos']:
        add_dir(i['label'], i['videoURL'], 4, i['thumbnailURL'],
                {'Plot': i['description'], 'Duration': get_length_in_minutes(i['length'])}, False)
    if items['last'] < items['total']:
        page_items = playlist_url.rsplit('_', 2)
        page_url = '%s_%s_%s' %(page_items[0], (int(page_items[1])+1), page_items[2])
        add_dir(language(30005), page_url, 2, icon)


def resolve_url(url):
    playpath = url.replace('http://wms.scrippsnetworks.com','').replace('.wmv','')
    final_url = (
        'rtmp://flash.scrippsnetworks.com:1935/ondemand?ovpfv=1.1 '
        'swfUrl=http://common.scrippsnetworks.com/common/snap/snap-3.2.17.swf '
        'playpath=' + playpath
        )
    item = xbmcgui.ListItem(path=final_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def cache_all_shows():
    url = 'http://www.foodnetwork.com/shows/index.html'
    soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
    items = soup.find('div', attrs={'class': "list-wrap"})('li')
    show_list = []
    for i in items:
        show = {}
        show['name'] = i.a.string
        show['page_href'] = i.a['href']
        show_list.append(show)

    dialog = xbmcgui.Dialog()
    ok = dialog.yesno(
        language(30011),
        language(30009),
        language(30010)
        )
    if ok:
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        for i in show_list:
            data = make_request(base_url+i['page_href'])
            if data:
                s_soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
                item = s_soup.find('span', attrs={'class': "lgbtn-text"}, text='videos')
                if not item:
                    item = s_soup.find('span', attrs={'class': "lgbtn-text"}, text='VIDEOS')
                if item:
                    i['video_href'] = item.findPrevious('a')['href']
                else:
                    try:
                        item = re.findall('var snap = new SNI.Food.Player.VideoAsset\(.+?, (.+?)\);', data)[0]
                    except:
                        try:
                            item = re.findall('var snap = new SNI.Food.Player.FullSize\(.+?, (.+?)\);', data)[0]
                        except:
                            try:
                                item = re.findall('var snap = new SNI.Food.Player.FullSizeNoPlaylist\(.+?, (.+?)\);', data)[0]
                            except:
                                addon_log('Unable to find video_id')
                                item = None
                    if item:
                        i['video_href'] = item
                try:
                    ok = i['video_href']
                    addon_log('Videos: True: %s' %i['name'])
                except:
                    addon_log('Videos: False: %s' %i['name'])
                    addon_log('Removing %s From Show List'  %i['name'])
                    for index in range(len(show_list)):
                        if show_list[index]['name'] == i['name']:
                                del show_list[index]
                                break
                    continue
                thumb = None
                try: thumb = re.findall('background: url\((.+?)\)', data)[0]
                except:
                    try: thumb = s_soup.find('div', attrs={'id': "main-bd"}).img['src']
                    except: pass
                if thumb:
                    i['thumb'] = thumb
            else:
                addon_log('No Data')
            xbmc.sleep(500)
        show_file = os.path.join(home, 'resources', 'show_list')
        w = open(show_file, 'w')
        w.write(repr(show_list))
        w.close()
        addon_log('%s Shows with videos in Show List' %len(show_list))
        xbmc.executebuiltin("Dialog.Close(busydialog)")


def get_length_in_minutes(length):
    if not isinstance(length, str):
        if ':' in str(length):
            length = str(length)
        elif isinstance(length, int):
            return length
    if ':' in length:
        l_split = length.split(':')
        minutes = int(l_split[-2])
        if int(l_split[-1]) >= 30:
            minutes += 1
        if len(l_split) == 3:
            minutes += (int(l_split[0]) * 60)
        if minutes < 1:
            minutes = 1
        return minutes


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


def add_dir(name, url, mode, iconimage, infolabels={}, isfolder=True):
    params = {'name': name, 'url': url, 'mode': mode}
    infolabels['Title'] = name
    url = '%s?%s' %(sys.argv[0], urllib.urlencode(params))
    listitem = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if not isfolder:
        listitem.setProperty('IsPlayable', 'true')
    listitem.setInfo(type="Video", infoLabels=infolabels)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isfolder)


params = get_params()

try:
    mode = int(params['mode'])
except:
    mode = None

addon_log(repr(params))

if mode == None:
    get_categories()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 1:
    get_cat(params['url'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 2:
    get_playlist(params['url'], params['name'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 3:
    get_video_xml(params['url'])

elif mode == 4:
    resolve_url(params['url'])

elif mode == 5:
    get_all_shows()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 6:
    get_video_xml(params['url'], True)

elif mode == 7:
    cache_all_shows()
