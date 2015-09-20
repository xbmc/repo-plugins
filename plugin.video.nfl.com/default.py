import urllib
import urllib2
import re
import os
import json
from traceback import format_exc
from urlparse import urlparse, parse_qs

import xbmcplugin
import xbmcgui
import xbmcaddon

import StorageServer
from BeautifulSoup import BeautifulSoup
from resources.highlights import Navigation


addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_icon = addon.getAddonInfo('icon')
fanart = addon.getAddonInfo('fanart')
addon_version = addon.getAddonInfo('version')
addon_path = xbmc.translatePath(addon.getAddonInfo('path'))
next_icon = os.path.join(addon_path, 'resources','icons','next.png')
cache = StorageServer.StorageServer("nfl_com", 1)
bitrate = addon.getSetting('bitrate')
language = addon.getLocalizedString
base_url = 'http://www.nfl.com'


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log: %s' %format_exc()
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message),
        level=xbmc.LOGDEBUG)


def make_request(url):
    addon_log('Request URL: %s' %url)
    headers = {
        'User-agent' : ('Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0)'
                        ' Gecko/20100101 Firefox/40.0'),
        'Referer' : base_url + '/videos'}
    try:
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)
        data = response.read()
        addon_log(str(response.info()))
        redirect_url = response.geturl()
        response.close()
        if redirect_url != url:
            addon_log('Redirect URL: %s' %redirect_url)
        return data
    except urllib2.URLError, e:
        addon_log('We failed to open "%s".' %url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' %e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' %e.code)


def cache_cats():
    ''' cache a dict of the main categories '''
    url = base_url + '/widgets/navigation/header-2012/header-includes.html'
    soup = BeautifulSoup(make_request(url),
        convertEntities=BeautifulSoup.HTML_ENTITIES)
    video_items = soup.find('div', text='videos').findNext('ul')('a')
    show_items = soup.find('div', text='shows').findNext('ul')('a')
    show_items += soup.find('div', text='NFL.com/LIVE').findNext('ul')('a')
    channel_items = soup.find('div', text='channels').findNext('ul')('a')
    event_items = soup.find('div', text='events').findNext('ul')('a')
    teams_items = soup.find('div', attrs={'class': 'teams'}).findAll('a')
    categories = {
        'videos': [(i.string, i['href']) for i in video_items if i.string],
        'shows': [(i.string, i['href']) for i in show_items if i.string],
        'channels':[(i.string, i['href']) for i in channel_items if i.string],
        'events': [(i.string, i['href']) for i in event_items if i.string],
        'teams': [(i.string, i['href']) for i in teams_items if i.string]}
    cache.set('categories', repr(categories))
    return categories


def categories():
    ''' display the main directory '''
    search_icon = os.path.join(addon_path, 'resources','icons','search.png')
    add_dir(language(30000), 'play_featured', 'play_featured_videos',
            addon_icon, {}, False)
    try:
        data = eval(cache.get('categories'))
    except:
        addon_log('categories is not cached')
        data = cache_cats()
    get_cats('videos')
    for i in data.keys():
        if i == 'videos': continue
        add_dir(i.title(), '', 'get_cats', addon_icon)
    add_dir(language(30001), 'search', 'search', search_icon)


def get_cats(name):
    ''' display sub-category directories '''
    data = eval(cache.get('categories'))
    name = name.lower()
    items = data[name]
    name_list = []
    for i in items:
        i_name = i[0]
        url = i[1]
        if name == 'teams':
            # we need a different url
            url = '%s/videos/%s' %(base_url,
                i_name.lower().replace('.', '').replace(' ', '-'))
        mode = 'resolve_feed_url'
        if i_name in name_list: continue
        if i_name == 'NFL Now': continue
        if i_name == 'The Season': continue
        if i_name == 'Big Play Highlights':
            mode = 'get_highlights'
        add_dir(i_name, url, mode, addon_icon)
        name_list.append(i_name)


def get_videos_feed(url):
    ''' display videos from a feed_url '''
    data = json.loads(make_request(url))
    for i in data['videos']:
        info = {}
        if not i['videoBitRates']:
            if i.has_key('videoFileUrl'):
                i['videoBitRates'] = [{'bitrate': 700000,
                                       'videoPath': i['videoFileUrl']}]
            else:
                addon_log('No videoBitRates: %s' %i)
                continue
        info['duration'] = hms_to_seconds(i['runTime'])
        info['plot'] = i['caption']
        add_dir(i['headline'], select_bitrate(i['videoBitRates']), 'set_url',
                    i['mediumImageUrl'], info, False)
    if data.has_key('total') and data['total'] > (data['offset'] + 20):
        page_url = '%s?limit=20&offset=%s' %(
            url.split('?')[0], str(data['offset'] + data['limit']))
        add_dir(language(30003), page_url, 'get_videos_feed', addon_icon)


def resolve_feed_url(url, name):
    if name == 'Video Home' or name == 'Most Popular':
        return get_featured_videos()
    else:
        channel_id = url.split('/')[-1]
        feed_url = ('%s/feeds-rs/videos/byChannel/%s.json?limit=16' %
            (base_url, channel_id))
    get_videos_feed(feed_url)


def cache_featured_videos():
    ''' cacheFunction for get_featured_videos '''
    url = base_url + '/feeds-rs/videos/byRanking/widget_video_fv.json'
    data = json.loads(make_request(url))
    featured = {}
    index = 0
    for i in data['videos']:
        info = {
           'duration': hms_to_seconds(i['runTime']),
           'plot': i['caption']}
        featured[index] = (i['headline'], i['videoBitRates'],
                           i['mediumImageUrl'], info)
        index += 1
    return featured


def get_featured_videos(play=False):
    data = cache.cacheFunction(cache_featured_videos)
    if play:
        playlist = xbmc.PlayList(1)
        playlist.clear()
    for i in range(len(data)):
        url = select_bitrate(data[i][1])
        listitem = xbmcgui.ListItem(data[i][0], iconImage=data[i][2],
                thumbnailImage=data[i][2])
        listitem.setInfo(type="Video",
            infoLabels={"Title": data[i][0],
                        "Plot": data[i][3]['plot'],
                        "Duration": data[i][3]['duration']})
        listitem.setProperty("Fanart_Image", fanart)
        if play:
            playlist.add(url, listitem)
        else:
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, False)
    if play:
        xbmc.executebuiltin('playlist.playoffset(video,0)')



def get_highlights(href=None, selected=None):
    ''' display 'Big Play Highlights' and filters '''
    nav = Navigation()
    if href is None:
        page_url = base_url + '/big-play-highlights'
    else:
        page_url = base_url + href
    nav_dict = nav.get_navigation(make_request(page_url))
    feed_url = nav.get_feed_url(href)
    cache.set('navigation', repr(nav_dict))
    dir_name = '[COLOR=orange]| '
    for i in [nav.season, nav.season_type, nav.week, nav.team, nav.game]:
        if i:
            dir_name += '%s | ' %i
    dir_name += '[/COLOR] %s' %language(30005)
    add_dir(dir_name, 'display_nav', 'highlights_nav', addon_icon)
    get_videos_feed(feed_url)


def display_highlights_nav(selected=None):
    ''' changes filter options for 'Big Play Highlights' '''
    dialog = xbmcgui.Dialog()
    nav = eval(cache.get('navigation'))
    if selected:
        addon_log('Selected: %s' %selected)
        ret = dialog.select(language(30005),
                [i['label'] for i in nav[selected]])
        if ret > -1:
            addon_log('Selected URL: %s' %nav[selected][ret]['href'])
            get_highlights(nav[selected][ret]['href'], selected)
    else:
        ret = dialog.select(language(30005), [i.title() for i in nav.keys()])
        if ret > -1:
            addon_log('Selected: %s' %nav.keys()[ret])
            display_highlights_nav(nav.keys()[ret])


def get_video_url(video_id):
    ''' resolve playable url from video ID '''
    url = '%s/static/embeddablevideo/%s.json' %(base_url, video_id)
    data = json.loads(make_request(url))
    if data['status'] == 'EXPIRED':
        xbmc.executebuiltin("XBMC.Notification(NFL.com,%s,5000,%s)" %(
            language(30004), addon_icon))
        return
    bitrate_list = data['cdnData']['bitrateInfo']
    if len(bitrate_list) > 0:
        return select_bitrate(bitrate_list)
    else:
        addon_log('No bitrateInfo: %s' %url)


def select_bitrate(bitrate_list):
    bitrate = int(addon.getSetting('prefered_bitrate'))
    streams = None
    try: streams = [(i['rate'], i['path']) for i in bitrate_list]
    except: streams = [(i['bitrate'], i['videoPath']) for i in bitrate_list]
    if len(streams) < 1:
        addon_log('select_bitrate error')
        return None
    if len(streams) == 1:
        path = streams[0][1]
    elif bitrate == 3:
        path = streams[-1][1]
    elif bitrate == 0:
        path = streams[0][1]
    elif bitrate == 2:
        if len(streams) > 3:
            if int(streams[-1][0]) <= 3000000:
                path = streams[-1][1]
            else:
                path = streams[-2][1]
        else:
            pathe = streams[1][1]
    elif bitrate == 1:
        if len(streams) > 3:
            if int(streams[2][0]) <= 1200000:
                path = streams[2][1]
            else:
                path = streams[1][1]
        else:
            pathe = streams[1][1]
    if path.startswith('http'):
        return path
    else:
        return 'http://a.video.nfl.com/' + path


def search(search_url=None):
    if search_url is None:
        search_str = ''
        keyboard = xbmc.Keyboard(search_str, 'Search')
        keyboard.doModal()
        if (keyboard.isConfirmed() == False):
            return
        search_str = keyboard.getText()
        if len(search_str) == 0:
            return
        search_url = ('http://search.nfl.com/search?&query=%s&mediatype=video'
            %urllib.quote_plus(search_str))
        
    soup = BeautifulSoup(make_request(search_url))
    items = soup('li', attrs={'class': re.compile('ez-itemMod-item')})
    for i in items:
        info = {}
        try:
            name = i.a['title']
            vid_id = i.a['href'].split('id=')[1]
            thumb = i.img['src'].split('_video_')[0] + '_video_rhr_210.jpg'
            info['plot'] = i('p', attrs={'class':  'ez-desc'})[0].string
            run_time = i('p', attrs={'class': 'ez-duration ez-icon'})[0].string
            info['duration'] = hms_to_seconds(run_time)
            add_dir(name, vid_id, 'set_url', thumb, info, False)
        except:
            addon_log(format_exc())
    next_link = soup.find('a', attrs={'class': "ez-paginationMod-next"})
    if next_link:
        try:
            location = re.findall("location='(.+?)';", next_link['href'])[0]
            page_url = urllib.unquote(location)
            add_dir(language(30003), page_url, 'search_results', next_icon)
        except:
            addon_log(format_exc())


def set_url(url):
    success = True
    if url.startswith('http'):
        resolved_url = url
    else:
        resolved_url = get_video_url(url)
    if resolved_url is None:
        success = False
        resolved_url = ''
    item = xbmcgui.ListItem(path=resolved_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)


# credit: http://stackoverflow.com/a/10742527
def hms_to_seconds(t):
    try:
        h, m, s = [int(i) for i in t.split(':')[:3]]
        return 3600*h + 60*m + s
    except ValueError:
        m, s = [int(i) for i in t.split(':')]
        return 60*m + s


def add_dir(name, url, mode, iconimage, info={}, isfolder=True):
    params = {'name': name, 'url': url, 'mode': mode}
    url = '%s?%s' %(sys.argv[0], urllib.urlencode(params))
    info['Title'] = name
    listitem = xbmcgui.ListItem(name, iconImage=iconimage,
            thumbnailImage=iconimage)
    if not isfolder:
        if not mode == 'play_featured_videos':
            listitem.setProperty('IsPlayable', 'true')
    listitem.setInfo(type="Video", infoLabels=info)
    listitem.setProperty("Fanart_Image", fanart)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isfolder)


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


params = get_params()
addon_log("params: %s" %params)

try:
    mode = params['mode']
except:
    mode = None

if mode == None:
    categories()
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'resolve_feed_url':
    resolve_feed_url(params['url'], params['name'])
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_cats':
    get_cats(params['name'])
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'set_url':
    set_url(params['url'])

elif mode == 'search':
    search()
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'search_results':
    search(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_featured_videos':
    get_featured_videos()
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'play_featured_videos':
    get_featured_videos(True)

elif mode == 'highlights_nav':
    display_highlights_nav()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_highlights':
    get_highlights()
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_videos_feed':
    get_videos_feed(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
