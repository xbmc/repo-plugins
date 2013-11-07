import urllib
import urllib2
import re
import xbmcplugin
import xbmcgui
import xbmcaddon
import StorageServer
from bs4 import BeautifulSoup
from urlparse import urlparse, parse_qs
from traceback import format_exc


addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_version = addon.getAddonInfo('version')
cache = StorageServer.StorageServer("diynetwork", 6)
base_url = 'http://www.diynetwork.com'


def addon_log(string):
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, string), level=xbmc.LOGNOTICE)


def make_request(url):
    addon_log('Request URL: %s' %url)
    headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:17.0) Gecko/20100101 Firefox/17.0',
               'Referer' : base_url}
    try:
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)
        data = response.read()
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
    if url.startswith('/'):
        url = base_url + url
    try:
        soup = BeautifulSoup(make_request(url), "html.parser")
        return soup
    except:
        addon_log('failed to parse the soup')


def cache_shows():
    soup = get_soup('/full-episodes/package/index.html')
    shows = []
    show_items = soup.find_all('ul', class_='show-index')
    for i in show_items:
        shows.extend(i('li'))
    show_dict = {}
    for i in shows:
        name = i('img')[0]['alt'].lstrip()
        if show_dict.has_key(name):
            continue
        show_dict[name] = {
            'url': i('a', class_='button')[0]['href'],
            'thumbnail': i('img')[0]['src'].strip(),
            'description': i.p.string}
    return show_dict


def display_shows():
    shows = cache.cacheFunction(cache_shows)
    for i in shows.keys():
        add_dir(i, shows[i]['url'], shows[i]['description'], shows[i]['thumbnail'], 1)


def display_show(url, iconimage, videos=False):
    soup = get_soup(url)
    if not soup:
        if '/show/' in url:
            soup = get_soup(url.replace('/show/index', '/videos/index'))
            if not soup:
                return
        else: return
    cats = index(soup, iconimage)
    current = None
    if videos:
        current = get_playlist(soup, 'videos')
    else:
        current = get_playlist(soup, True)

    if current is None and not videos:
        try:
            show_href = soup.find('ul', class_='button-nav')('a', text='FULL EPISODES')[0]['href']
            if show_href:
                return display_show(show_href, iconimage)
            else: raise
        except:
            addon_log('did not find current playlist')
    elif current is None:
        try:
            show_href = soup.find('ul', class_='button-nav')('a', text='Videos')[0]['href']
            if show_href:
                return display_show(show_href, iconimage, True)
            else: raise
        except:
            addon_log('did not find current playlist')

    if len(cats['directories']) > 1:
        if current:
            add_dir(current, 'cache_current', '', iconimage, 3)
        for i in cats['directories']:
            add_dir(i[0], i[1], '', i[2], 4)
        xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
        xbmc.executebuiltin('Container.SetViewMode(503)')
    else:
        if current:
            if videos:
                add_episodes(eval(cache.get('videos_base')))
            else:
                add_episodes(eval(cache.get('current_base')))
    if not videos:
        if cats['has_videos']:
            add_dir('Videos', cats['has_videos'][0], '', cats['has_videos'][1], 5)


def index(soup, iconimage):
    items = []
    try:
        videos_soup = soup('div', class_= 'pod crsl-we')
        if videos_soup:
            for i in videos_soup:
                name = i.find_previous('h4').string.replace('Full Episodes', '')
                href = i.a['href']
                items.append((name, href, iconimage))
    except:
        addon_log(format_exc())

    try:
        videos_href = soup.find('li', class_='hub-vid').a['href']
        videos = (videos_href, iconimage)
    except:
        videos = None

    return {'directories': items, 'has_videos': videos}


def get_playlist(soup, base=False):
    show_id = re.compile("var snap = new SNI.DIY.Player.FullSize\(\'.+?','(.+?)', '.+?'\);").findall(str(soup))
    if len(show_id) < 1:
        addon_log('Houston we have a problem!')
    else:
        url = '%s/diy/channel/xml/0,,%s,00.xml' %(base_url, show_id[0])
        videos_soup = get_soup(url)
        parsed = [(i.clipname.string, i.videourl.string, i.abstract.string, i.thumbnailurl.string, i.length.string)
                   for i in videos_soup('video')]
        if base == 'videos':
            cache.set('videos_base', repr(parsed))
            return videos_soup.title.string
        elif base:
            cache.set('current_base', repr(parsed))
            dir_title = videos_soup.title.string
            if dir_title != 'Full Episodes':
                dir_title = dir_title.replace('Full Episodes', '')
            return dir_title
        else:
            return parsed


def add_episodes(items):
    if not isinstance(items, list):
        item_list = [items]
        items = item_list
    for i in items:
        path = i[1].replace('http://wms.scrippsnetworks.com','').replace('.wmv','')
        add_dir(i[0], path, i[2], i[3], 2, get_duration(i[4]), False)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmc.executebuiltin('Container.SetViewMode(503)')


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


def set_resolved_url(path):
    video_url = ('rtmp://flash.scrippsnetworks.com:1935/ondemand?ovpfv=1.1 '
                 'swfUrl=http://common.scrippsnetworks.com/common/snap/snap-3.0.3.swf playpath=%s' %path)
    return video_url


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


def add_dir(name, url, description, iconimage, mode, duration=None, isfolder=True):
    params = {'name': name, 'url': url, 'mode': mode, 'iconimage': iconimage}
    url = '%s?%s' %(sys.argv[0], urllib.urlencode(params))
    listitem=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    info_labels = {"Title": name, "Plot":description, "Genre": 'Home and Garden'}
    if not isfolder:
        info_labels['Duration'] = duration
        listitem.setProperty('isPlayable', 'true')
    listitem.setInfo(type="Video", infoLabels=info_labels)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isfolder)


params = get_params()

try:
    mode = int(params['mode'])
except:
    mode = None

addon_log(params)

if mode == None:
    display_shows()
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 1:
    display_show(params['url'], params['iconimage'])
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 2:
    item = xbmcgui.ListItem(path=set_resolved_url(params['url']))
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

elif mode == 3:
    add_episodes(eval(cache.get('current_base')))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 4:
    soup = get_soup(params['url'])
    add_episodes(get_playlist(soup))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 5:
    display_show(params['url'], params['iconimage'], True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
