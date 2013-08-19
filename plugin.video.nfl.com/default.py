import urllib
import urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
import StorageServer
import simplejson as json
from traceback import format_exc
from urlparse import urlparse, parse_qs
from BeautifulSoup import BeautifulSoup

addon = xbmcaddon.Addon(id='plugin.video.nfl.com')
addon_version = addon.getAddonInfo('version')
addon_path = xbmc.translatePath(addon.getAddonInfo('path'))
bitrate = addon.getSetting('bitrate')
icon = os.path.join(addon_path, 'icon.png')
next_icon = os.path.join(addon_path, 'resources','icons','next.png')
fanart = os.path.join(addon_path, 'fanart.jpg')
cache = StorageServer.StorageServer("nfl_com", 1)
language = addon.getLocalizedString
debug = addon.getSetting('debug')
if debug == 'true':
    cache.dbg = True


def addon_log(string):
    if debug == 'true':
        xbmc.log("[addon.nfl.com-%s]: %s" %(addon_version, string))


def make_request(url, data=None, headers=None):
    addon_log('Request URL: %s' %url)
    if headers is None:
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0',
                   'Referer' : 'http://www.nfl.com'}
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
    add_dir(language(30000), 'play_featured', 8, icon, None, None, False)
    try:
        data = eval(cache.get('categories'))
    except:
        addon_log('categories is not cached')
        data = cache_cats()
    for i in data.keys():
        add_dir(i.title(), '', 2, icon)
    add_dir(language(30001),'search',6,os.path.join(addon_path, 'resources','icons','search.png'))


def cache_cats():
    url = 'http://www.nfl.com/widgets/navigation/header-2012/header-includes.htmlv'
    soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
    video_items = soup.find('div', text='videos').findNext('ul')('a')
    show_items = soup.find('div', text='shows').findNext('ul')('a')
    show_items += soup.find('div', text='nfl.com/live').findNext('ul')('a')
    channel_items = soup.find('div', text='channels').findNext('ul')('a')
    event_items = soup.find('div', text='events').findNext('ul')('a')
    categories = {'videos': [(i.string, i['href']) for i in video_items if i.string],
                  'shows': [(i.string, i['href']) for i in show_items if i.string],
                  'channels':[(i.string, i['href']) for i in channel_items if i.string],
                  'events': [(i.string, i['href']) for i in event_items if i.string],
                  'teams': []}
    cache.set('categories', repr(categories))
    return categories


def cache_teams():
    url = 'http://www.nfl.com/videos/nfl-videos'
    soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
    data = eval(cache.get('categories'))
    items = soup.findAll('div', attrs={'class': "conf-panel-list"})
    data['teams'] = [(i.string, i['href']) for i in items[0]('a')+items[1]('a')]
    cache.set('categories', repr(data))
    return data['teams']


def get_cats(name):
    data = eval(cache.get('categories'))
    name = name.lower()
    items = data[name]
    if name == 'teams':
        if len(items) == 0:
            items = cache_teams()
    for i in items:
        if i[0] == 'The Season': continue  # need a new function for this channel
        add_dir(i[0], i[1], 1, icon)


def index(url, name):
    if name == 'Video Home':
        return get_featured_videos()
    if not url.startswith('http'):
        url = 'http://www.nfl.com' + url
    soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
    if not 'page=' in url:
        featured_videos = None
        try: featured_videos = soup.find('div', attrs={'id' : "featured-videos-carousel"})('ul')[0]('h3')
        except:
            try: featured_videos = soup.findAll('ul', attrs={'class' : "list-items"})[0]('h3')
            except: pass
        if featured_videos:
            featured = []
            for i in featured_videos:
                featured.append((i('a')[0].string, i('a')[0]['href'].split('/')[3]))
            cache.set('currently_featured', repr(featured))
            add_dir(language(30000), url, 4, icon, None, None, False)
    videos = None
    try:
        videos = soup.find('ul', attrs={'id' : "video-list-items"})('li')
    except:
        addon_log('video_items exception: %s' %format_exc())
    if videos:
        for i in videos:
            name = i('h3')[0]('a')[0].string
            link = i('h3')[0]('a')[0]['href'].split('/')[3]
            thumb = i('img')[0]['src'].split('_video_thumbnail_')[0]+'_video_rhr_210.jpg'
            try:
                desc = i('p')[1].string+' \n  '+i('p')[0].string
            except:
                desc = i('p')[0].string
            duration = i('div')[-1].string.replace('\n','').replace('\t','')
            try:
                add_dir(name,link,3,thumb,duration,desc,False)
            except:
                addon_log('add_dir exception: %s' %format_exc())
        # check for pagenation
        try:
            page = soup.find('div', attrs={'id' : "video-list-pagination"})('a')[-1]['href']
            # video pages switch to ajax after the first few pages
            if page == '?page=3' or page == '?page=7':
                page_url = 'http://www.nfl.com/ajax/videos/v2?batchNum=1&channelId='+url.split('/')[-1].split('?')[0]
                mode = 5
            else:
                page_url = url.split('?')[0]+page
                mode = 1
            add_dir(language(30003), page_url, mode, next_icon)
        except:
            pass


def get_page_3(url):
    data = json.loads(make_request(url))
    videos = data['videos']
    for i in videos:
        vedio_id = i['videoCMSID']
        name = i['briefHeadline']
        thumb = i['xSmallImage'].split('_video_thumbnail_')[0]+'_video_rhr_210.jpg'
        desc = i['captionBlurb']
        duration = i['runTime'][:-3]
        add_dir(name,vedio_id,3,thumb,duration,desc,False)
    batch = data['batch']
    if batch * 50 < data['total']:
        next_url = url.replace('batchNum=%s' %batch, 'batchNum=%s' %(batch + 1))
        add_dir(language(30003), next_url, 5, next_icon)


def get_current_featured_videos():
    videos = eval(cache.get('currently_featured'))
    playlist = xbmc.PlayList(1)
    playlist.clear()
    for i in videos:
        playlist.add(get_video_url(i[1]), xbmcgui.ListItem(i[0]))
    xbmc.executebuiltin('playlist.playoffset(video,0)')


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
        xbmc.executebuiltin("XBMC.Notification(NFL.com,%s,5000,%s)" %(language(30004), icon))
        return
    bitrate_list = data['cdnData']['bitrateInfo']
    if len(bitrate_list) > 0:
        return select_bitrate(bitrate_list)
    else:
        addon_log('No bitrateInfo: %s' %url)


def select_bitrate(bitrate_list):
    addon_log('bitrate list: %s' %bitrate_list)
    bitrate = int(addon.getSetting('prefered_bitrate'))
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
    addon_log('Path: %s' %path)
    if path.startswith('http'):
        return path
    else:
        return 'http://a.video.nfl.com/' + path


def set_url(url):
    success = True
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
    index(params['url'], params['name'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 2:
    get_cats(params['name'])
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 3:
    set_url(params['url'])

elif mode == 4:
    get_current_featured_videos()

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