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
debug = addon.getSetting('debug')
if debug == 'true':
    cache.dbg = True


def addon_log(string):
    if debug == 'true':
        try:
            log_message = string.encode('utf-8', 'ignore')
        except:
            log_message = 'addonException: addon_log: %s' %format_exc()
        xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message), level=xbmc.LOGNOTICE)


def make_request(url, data=None, headers=None):
    addon_log('Request URL: %s' %url)
    if headers is None:
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0',
                   'Referer' : 'http://www.nfl.com/videos'}
    try:
        req = urllib2.Request(url, data, headers)
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


def categories():
    add_dir(language(30000), 'play_featured', 8, addon_icon, None, None, False)
    try:
        data = eval(cache.get('categories'))
    except:
        addon_log('categories is not cached')
        data = cache_cats()
    get_cats('videos')
    for i in data.keys():
        if i == 'videos': continue
        add_dir(i.title(), '', 2, addon_icon)
    add_dir(language(30001),'search',6,os.path.join(addon_path, 'resources','icons','search.png'))


def cache_cats():
    url = 'http://www.nfl.com/widgets/navigation/header-2012/header-includes.html'
    soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
    video_items = soup.find('div', text='videos').findNext('ul')('a')
    show_items = soup.find('div', text='shows').findNext('ul')('a')
    show_items += soup.find('div', text='NFL.com/LIVE').findNext('ul')('a')
    channel_items = soup.find('div', text='channels').findNext('ul')('a')
    event_items = soup.find('div', text='events').findNext('ul')('a')
    teams_items = soup.find('div', attrs={'class': 'teams'}).findAll('a')
    categories = {'videos': [(i.string, i['href']) for i in video_items if i.string],
                  'shows': [(i.string, i['href']) for i in show_items if i.string],
                  'channels':[(i.string, i['href']) for i in channel_items if i.string],
                  'events': [(i.string, i['href']) for i in event_items if i.string],
                  'teams': [(i.string, i['href']) for i in teams_items if i.string]}
    cache.set('categories', repr(categories))
    return categories


def get_cats(name):
    data = eval(cache.get('categories'))
    name = name.lower()
    items = data[name]
    name_list = []
    for i in items:
        i_name = i[0]
        url = i[1]
        if name == 'teams':
            # we need a different url
            url = 'http://www.nfl.com/videos/%s' %i_name.lower().replace('.', '').replace(' ', '-')
        mode = 1
        if i_name in name_list: continue
        if i_name == 'NFL Now': continue
        if i_name == 'The Season': continue  # need a new function for this channel
        if i_name == 'Top 100 Players':
            mode = 12
        if i_name == 'Big Play Highlights':
            mode = 10
        add_dir(i_name, url, mode, addon_icon)
        name_list.append(i_name)


def resolve_feed_url(url, name):
    if name == 'Video Home':
        return get_featured_videos()
    channel_id = url.split('/')[-1]
    get_videos_feed('http://www.nfl.com/feeds-rs/videos/byChannel/%s.json?limit=16' %channel_id)


def cache_featured_videos():
    url = 'http://www.nfl.com/feeds-rs/videos/byRanking/widget_video_fv.json'
    data = json.loads(make_request(url))
    featured = {}
    index = 0
    for i in data['videos']:
        duration = get_duration_in_minutes(i['runTime'])
        featured[index] = (i['headline'], i['videoBitRates'], i['mediumImageUrl'], duration, i['caption'])
        index += 1
    return featured


def get_top_players(url):
    soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
    items = soup.findAll('div', attrs={'class': "top100-video-thumb"})[:100]
    for i in items:
        name = '%s - %s' %(i('span', attrs={'class': 'player-rank'})[0].string, i('span', attrs={'class': 'brand'})[0].string)
        video_id = [x['data-ecmid'] for x in i('a', attrs={'class': 'play-button'})][0]
        thumb = i.img['src']
        print (name, video_id, thumb)
        add_dir(name, video_id, 3, i.img['src'], duration=None, description=None, isfolder=False)



def get_highlights(href=None, selected=None):
    nav = Navigation()
    if href is None:
        page_url = 'http://www.nfl.com/big-play-highlights'
    else:
        page_url = 'http://www.nfl.com' + href
    nav_dict = nav.get_navigation(make_request(page_url))
    feed_url = nav.get_feed_url(href)
    addon_log('feed_url: %s' %feed_url)
    cache.set('navigation', repr(nav_dict))
    dir_name = '[COLOR=orange]| '
    for i in [nav.season, nav.season_type, nav.week, nav.team, nav.game]:
        if i:
            dir_name += '%s | ' %i
    dir_name += '[/COLOR] %s' %language(30005)
    add_dir(dir_name, 'display_nav', 9, addon_icon)
    get_videos_feed(feed_url)


def get_videos_feed(url):
    data = json.loads(make_request(url))
    for i in data['videos']:
        if not i['videoBitRates']:
            if i.has_key('videoFileUrl'):
                i['videoBitRates'] = [{'bitrate': 700000, 'videoPath': i['videoFileUrl']}]
            else:
                addon_log('No videoBitRates: %s' %i)
                continue
        add_dir(i['headline'], select_bitrate(i['videoBitRates']), 3, i['mediumImageUrl'], i['runTime'], i['caption'], False)
    if data['total'] > (data['offset'] + 20):
        page_url = url.split('?')[0] + '?limit=20&offset=' + str(data['offset'] + data['limit'])
        add_dir(language(30003), page_url, 11, addon_icon)


def display_highlights_nav(selected=None):
    dialog = xbmcgui.Dialog()
    nav = eval(cache.get('navigation'))
    if selected:
        addon_log('Selected: %s' %selected)
        ret = dialog.select(language(30005), [i['label'] for i in nav[selected]])
        if ret > -1:
            addon_log('Selected URL: %s' %nav[selected][ret]['href'])
            get_highlights(nav[selected][ret]['href'], selected)
    else:
        ret = dialog.select(language(30005), [i.title() for i in nav.keys()])
        if ret > -1:
            addon_log('Selected: %s' %nav.keys()[ret])
            display_highlights_nav(nav.keys()[ret])


def get_featured_videos(play=False):
    data = cache.cacheFunction(cache_featured_videos)
    if play:
        playlist = xbmc.PlayList(1)
        playlist.clear()
    for i in range(len(data)):
        url = select_bitrate(data[i][1])
        listitem = xbmcgui.ListItem(data[i][0], iconImage=data[i][2], thumbnailImage=data[i][2])
        listitem.setInfo(type="Video", infoLabels={"Title": data[i][0], "Plot": data[i][4], "Duration": data[i][3]})
        listitem.setProperty("Fanart_Image", fanart)
        if play:
            playlist.add(url, listitem)
        else:
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, False)
    if play:
        xbmc.executebuiltin('playlist.playoffset(video,0)')
    else:
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def search():
    searchStr = ''
    keyboard = xbmc.Keyboard(searchStr,'Search')
    keyboard.doModal()
    if (keyboard.isConfirmed() == False):
        return
    newStr = keyboard.getText().replace(' ','+')
    if len(newStr) == 0:
        return
    url = 'http://search.nfl.com/videos/search-results?quickSearch='+newStr
    soup = BeautifulSoup(make_request(url))
    for i in soup('li'):
        try:
            name = i('a')[0]['title']
            vid_id = [x for x in i('a')[0]['href'].split('/') if x.startswith('0ap')][0]
            thumb = i('a')[0]('img')[0]['src'].split('_video_')[0]+'_video_rhr_210.jpg'
            desc = i('p')[0].string
            duration = i('p')[1].string
            add_dir(name, vid_id, 3, thumb, duration, desc, False)
        except:
            addon_log(format_exc())


def get_video_url(url):
    url = 'http://www.nfl.com/static/embeddablevideo/'+url+'.json'
    data = json.loads(make_request(url))
    if data['status'] == 'EXPIRED':
        xbmc.executebuiltin("XBMC.Notification(NFL.com,%s,5000,%s)" %(language(30004), addon_icon))
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


def get_duration_in_minutes(duration):
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


def add_dir(name, url, mode, iconimage, duration=None, description=None, isfolder=True):
    params = {'name': name, 'url': url, 'mode': mode}
    url = '%s?%s' %(sys.argv[0], urllib.urlencode(params))
    listitem = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    if not isfolder:
        # mode 4 and 8 adds a playlist
        if not mode == 4 and not mode == 8:
            listitem.setProperty('IsPlayable', 'true')
            duration = get_duration_in_minutes(duration)
        listitem.setInfo(type="Video", infoLabels={"Title": name, "duration": duration, "Plot": description})
    else:
        listitem.setInfo(type="Video", infoLabels={"Title": name})
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
    mode = int(params['mode'])
except:
    mode = None

if mode == None:
    categories()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 1:
    resolve_feed_url(params['url'], params['name'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 2:
    get_cats(params['name'])
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 3:
    set_url(params['url'])

elif mode == 4:
    pass

elif mode == 5:
    get_page_3(params['url'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 6:
    search()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 7:
    get_featured_videos()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 8:
    get_featured_videos(True)

elif mode == 9:
    display_highlights_nav()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 10:
    get_highlights()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 11:
    get_videos_feed(params['url'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 12:
    get_top_players(params['url'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))