import urllib
import urllib2
import os
import json
import base64
import cookielib
import time
from datetime import datetime
from traceback import format_exc
from urlparse import urlparse, parse_qs

import StorageServer
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs

addon = xbmcaddon.Addon()
addon_version = addon.getAddonInfo('version')
addon_id = addon.getAddonInfo('id')
addon_path = xbmc.translatePath(addon.getAddonInfo('path'))
addon_profile = xbmc.translatePath(addon.getAddonInfo('profile'))
icon = os.path.join(addon_path, 'resources', '4x3_icon.png')
fanart = addon.getAddonInfo('fanart')
cache = StorageServer.StorageServer("theblaze", 24)
base_url = 'http://www.video.theblaze.com'
cookie_file = os.path.join(addon_profile, 'cookie_file')
cookie_jar = cookielib.LWPCookieJar(cookie_file)
language = addon.getLocalizedString


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log: %s' %format_exc()
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message), level=xbmc.LOGDEBUG)


def make_request(url, data=None, headers=None):
    addon_log('Request URL: %s' %url)
    if not xbmcvfs.exists(cookie_file):
        addon_log('Creating cookie_file!')
        cookie_jar.save()
    if headers is None:
        headers = {
            'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:25.0) Gecko/20100101 Firefox/25.0',
            'Referer': base_url
            }
    cookie_jar.load(cookie_file, ignore_discard=True, ignore_expires=True)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    urllib2.install_opener(opener)
    try:
        req = urllib2.Request(url,data,headers)
        response = urllib2.urlopen(req)
        data = response.read()
        cookie_jar.save(cookie_file, ignore_discard=True, ignore_expires=True)
        response.close()
        addon_log(str(response.info()))
        if response.geturl() != url:
            addon_log('Redirect URL: %s' %response.geturl())
    except urllib2.URLError, e:
        addon_log('We failed to open "%s".' %url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: '+ str(e.reason))
        elif hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' % e.code)
        data = None
    return data


def cache_shows():
    soup = BeautifulSoup(make_request(base_url + '/video'))
    content = soup.find('div', attrs={'class': 'secondary-content'})
    shows = []
    shows_tag = content('div', attrs={'id': 'secondaryPlaylist_1'})[0]('div', attrs={'class': 'page topic item'})
    shows_tag += content('div', attrs={'id': 'secondaryPlaylist_2'})[0]('div', attrs={'class': 'page topic item'})
    for i in shows_tag:
        items = i('a')
        for item in items:
            shows.append({'name': item.img['alt'], 'thumb': item.img['data-lazy-src'], 'url': item['href']})
    return shows


def display_shows():
    if addon.getSetting('prem_content') == 'true':
        add_dir(language(30013), 'live_shows', icon, 'get_live_shows')
    data = cache.cacheFunction(cache_shows)
    for i in data:
        add_dir(i['name'], i['url'], i['thumb'], 'get_show')


def display_show(show_url):
    current_show = show_url.split('=')[1]
    q1_hits = ['80', '0']
    q2_hits = ['0', '160']
    search_data = {
            "result_format": "json",
            "sort": "desc",
            "sort_type" : "date",
            "q1_query": current_show,
            "q1_gbtax_key": current_show,
            "q1_hitsPerPage": q1_hits[0],
            "q1_op" : "AND",
            "q1_gbtax" : "highlight",
            "q2_query": current_show,
            "q2_gbtax_key": current_show,
            "q2_event_category" : "show",
            "q2_hitsPerPage" : q2_hits[0],
            "bypass" : "y",
            "ns" : 43,
            "q2_op" : "AND" 
        }
    highlights_url = base_url + '/ws/search/merge?' + urllib.urlencode(search_data)
    search_data['q1_hitsPerPage'] = q1_hits[1]
    search_data['q2_hitsPerPage'] = q2_hits[1]
    episodes_url = base_url + '/ws/search/merge?' + urllib.urlencode(search_data)
    highlights = parse_video_search(highlights_url)
    episodes = parse_video_search(episodes_url)
    
    if addon.getSetting('prem_content') == 'false':
        if len(highlights) > 0:
            for i in highlights:
                add_dir(i[0]['title'], i[1], i[2], 'resolve_url', i[0])
        else:
            notify(language(30016))
    elif addon.getSetting('hide_highlights') == 'true':
        for i in episodes:
            add_dir(i[0]['title'], i[1], i[2], 'resolve_episode_url', i[0], i[3])
    else:
        cache.set('highlights_dict', repr({'highlights': highlights}))
        cache.set('episodes_dict', repr({'episodes': episodes}))
        add_dir(language(30014), 'get_cached_episodes', icon, 'get_show_list')
        if len(highlights) > 0:
            add_dir(language(30015), 'get_cached_highlights', icon, 'get_show_list')

    
def parse_video_search(search_url):
    data = json.loads(make_request(search_url))
    videos = []
    if data.has_key('mediaContent'):
        for i in data['mediaContent']:
            info = {}
            item_ids = {}
            thumb = None
            xml_url = i['url']
            for t in i['thumbnails']:
                if t['type'] == '1000' or t['type'] == '13':
                    thumb = t['src']
                    break
            if thumb is None:
                thumb = i['thumbnails'][0]['src']
            if not thumb.startswith('http'):
                thumb = base_url + thumb
            info['title'] = i['blurb']
            if i.has_key('bigBlurb') and i['bigBlurb']:
                info['plot'] = i['bigBlurb']
            if i.has_key('duration') and i['duration']:
                info['duration'] = get_length_in_minutes(i['duration'])
            if i.has_key('featureContext'):
                item_ids['content'] = i['contentId']
                for event in i['keywords']:
                    if event['type'] == 'calendar_event_id':
                        item_ids['event'] = event['keyword']
                        break
            videos.append((info, xml_url, thumb, item_ids))
    return videos

def display_show_list(name):
    if 'highlights' in name:
        for i in eval(cache.get("highlights_dict"))['highlights']:
            add_dir(i[0]['title'], i[1], i[2], 'resolve_url', i[0])
    else:
        for i in eval(cache.get("episodes_dict"))['episodes']:
            add_dir(i[0]['title'], i[1], i[2], 'resolve_episode_url', i[0], i[3])


def resolve_url(url):
    senario_types = {
        '0': 'FLASH_1200K_640X360',
        '1': 'FLASH_600K_400X224',
        '2': 'HTTP_CLOUD_MOBILE',
        '3': 'HTTP_CLOUD_TABLET',
        '4': 'HTTP_CLOUD_WIRED'
        }
    soup = BeautifulStoneSoup(make_request(url),
                              convertEntities=BeautifulStoneSoup.XML_ENTITIES)
    resolved_url = None
    play_scenario = senario_types[addon.getSetting('scenario')]
    for i in soup('url'):
        if play_scenario == i['playback_scenario']:
            resolved_url = i.string
            break
    if resolved_url is None:
        resolved_url = soup.url.string
    addon_log('Resolved URL: %s' %resolved_url)
    return resolved_url


def live_show_calendar(url=None):
    if url is None:
        url = 'http://www.video.theblaze.com/schedule/index.jsp'
    data = make_request(url)
    soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
    date_tag = soup.find('div', attrs={'id': 'date_container'})
    date_string = date_tag.h2.string
    calendar = {'date_string': date_tag.h2.string}
    calendar['items'] = [
        {'name': i.string, 'url': i['href'],
         'date_format': '%s/%s/%s'
         %(i['href'].split('=')[1][:4],
           i['href'].split('=')[1][4:6],
           i['href'].split('=')[1][6:])} for
            i in date_tag('a') if i['href'] != '#'
        ]
    cache.set('calendar', repr(calendar))
    return calendar


def select_calendar():
    calendar = eval(cache.get('calendar'))
    dialog = xbmcgui.Dialog()
    ret = dialog.select('Choose', [i['name'] for i in calendar['items']])
    if ret > -1:
        return display_live_shows(calendar['items'][ret]['url'],
                                  calendar['items'][ret]['date_format'])


def display_live_shows(calendar_url=None, date_format=None):
    if calendar_url is None:
        calendar = live_show_calendar()
        date_format = [i['date_format'] for i in calendar['items'] if
                i['name'] == 'Go to Today'][0]
    else:
        calendar = live_show_calendar(base_url + calendar_url)
    add_dir(calendar['date_string'], 'calendar', icon, 'select_calendar')
    json_url = 'http://www.video.theblaze.com/gen/hb/video/%s/linear_grid.json'
    data = json.loads(make_request(json_url %date_format))
    items = data['shows']['show']
    for i in items:
        info = {}
        media = i['show_media']['homebase']['media']
        info['title'] = media['header']
        info['plot'] = media['bigblurb']
        item_ids = {'event': i['calendar_event_id'],
                    'content': media['id']}
        media_state = i['media_state']
        if media_state == 'MEDIA_ON':
            title = '[COLOR=orange]%s[/COLOR]' %media['header']
            start_time = ' - Live Now'
            mode = 'resolve_episode_url'
        else:
            title = info['title']
            mode = 'pass'
            try:
                date_time = datetime(*(time.strptime(i['local_start_time'], '%Y-%m-%dT%H:%M:%S-0500')[0:6]))
                start_time = ' - %s' %datetime.strftime(date_time, '%I:%M %p ET').lstrip('0')
            except ValueError:
                try:
                    date_time = datetime(*(time.strptime(i['local_start_time'], '%Y-%m-%dT%H:%M:%S-0400')[0:6]))
                    start_time = ' - %s' %datetime.strftime(date_time, '%I:%M %p ET').lstrip('0')
                except:
                    addon_log(format_exc())
                    start_time = ' - %s' %media_state

        thumbnails = media['thumbnails']['thumbnail']
        try:
            thumb = [thumbnails[i]['url'] for i in range(len(thumbnails)) if
                    thumbnails[i]['type'] == '1000'][0]
        except IndexError:
            try:
                thumb = [thumbnails[i]['url'] for i in range(len(thumbnails)) if
                        thumbnails[i]['type'] == '13'][0]
            except IndexError:
                try:
                    thumb = [thumbnails[i]['url'] for i in range(len(thumbnails)) if
                            thumbnails[i]['type'] == '15'][0]
                except IndexError:
                    thumb = thumbnails[0]['url']
        thumbnail = base_url + thumb
        add_dir(title + start_time, 'live_show', thumbnail, mode, info, item_ids)


def do_login():
    # Check if cookies have expired.
    cookie_jar.load(cookie_file, ignore_discard=True, ignore_expires=False)
    cookies = {}
    addon_log('These are the cookies we have in the cookie file:')
    for i in cookie_jar:
        cookies[i.name] = i.value
        addon_log('%s: %s' %(i.name, i.value))
    if cookies.has_key('ipid') and cookies.has_key('fprt'):
        return cookies
    else:
        addon_log('Login to get cookies!')
        # Get the cookie first
        login_url = ('https://secure.video.theblaze.com/enterworkflow.do?'
                     'flowId=registration.migrate&forwardUrl=/account/home.jsp&platform=WEB')
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:26.0) Gecko/20100101 Firefox/26.0',
                   'Referer' : 'http://www.theblaze.com/user/?redirect_to=http%3A%2F%2Fwww.theblaze.com%2F'}
        loggingin = make_request(login_url, None, headers)

        # Now login
        login_url = 'https://secure.video.theblaze.com/authenticate.do'
        headers = {
            'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:26.0) Gecko/20100101 Firefox/26.0',
            'Referer': 'https://secure.video.theblaze.com/enterworkflow.do?'
                       'flowId=registration.migrate&forwardUrl=/account/home.jsp&platform=WEB'
            }
        values = {'uri' : '/account/login_register.jsp',
                  'registrationAction' : 'identify',
                  'emailAddress' : addon.getSetting('email'),
                  'password' : addon.getSetting('password'),
                  'submit' : 'Login'}

        loggingin = make_request(login_url,urllib.urlencode(values),headers)
        cookie_jar.load(cookie_file, ignore_discard=True, ignore_expires=False)
        cookies = {}
        addon_log('These are the cookies we have received so far :')
        for i in cookie_jar:
            cookies[i.name] = i.value
            addon_log('%s: %s' %(i.name, i.value))

        soup = BeautifulSoup(loggingin)
        if soup.title.string == 'TheBlaze.com: Account: Account Management - My Subscriptions':
            addon_log("Logged in successfully!")
        else:
            try:
                addon_log('html <title> : %' %soup.title.string)
            except:
                addon_log(format_exc())
                pass
            addon_log('Login Failed')
            notify(language(30017))
        if cookies.has_key('ipid') and cookies.has_key('fprt'):
            return cookies
        else:
            addon_log('We did not recive the required cookies!')


def resolve_prem_url(ids_dict, retry=False):
    SOAPCODES = {
        "1"    : "OK",
        "-1000": "Requested Media Not Found",
        "-1500": "Other Undocumented Error",
        "-2000": "Authentication Error",
        "-2500": "Blackout Error",
        "-3000": "Identity Error",
        "-3500": "Sign-on Restriction Error",
        "-4000": "System Error"
        }

    senario_types = {
        '0': 'FLASH_2400K_940X560',
        '1': 'FLASH_1800K_800X448',
        '2': 'FLASH_1200K_800X448',
        '3': 'FLASH_800K_400X448',
        '4': 'FLASH_500K_400X224'
        }

    event_id = ids_dict['event']
    # content_id = ids_dict['content']
    cookies = do_login()
    if cookies is None:
        addon_log('There seems to be an auth problem')
        return

    fprt = urllib.unquote(cookies['fprt'])
    ipid = cookies['ipid']
    values = {
        'eventId': urllib.quote(event_id),
        'fingerprint': fprt,
        'identityPointId': ipid,
        'subject': urllib.quote('LIVE_EVENT_COVERAGE'),
        'platform': urllib.quote('WEB_MEDIAPLAYER'),
        'sessionKey': '',
        'streamSelection': 'linear'
        }

    event_url = ('https://ws-mf.video.theblaze.com'
                 '/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3?')
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:26.0) Gecko/20100101 Firefox/26.0',
        'Referer': 'http://www.video.theblaze.com/shared/flash/mediaplayer/v4.4/R10/MediaPlayer4.swf'
        }
    data = make_request(event_url + urllib.urlencode(values), None, headers)
    addon_log('Response Data: %s' %data)
    soup = BeautifulStoneSoup(data, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
    status_code = soup('status-code')[0].string
    if status_code != "1":
        addon_log('server returned unsuccessful status_code: %s' %status_code)
        try:
            addon_log('SOAPCODE : %s' %SOAPCODES[status_code])
        except:
            addon_log(format_exc())
            pass
        # this usually is caused by invalid cookies
        if not retry:
            addon_log('clearing cookies')
            cookie_jar.clear()
            cookie_jar.save()
            return resolve_prem_url(ids_dict, True)
        else:
            try:
                status_message = soup('status-message')[0].string
                if status_message:
                    addon_log('Status Message: %s' %status_message)
                    notify(status_message)
                    return
                else:
                    raise
            except:
                addon_log(format_exc())
                notify(language(30018))
                return
    try:
        event_id = soup('event-id')[0].string
    except:
        addon_log(format_exc())
        pass
    session_key = soup('session-key')[0].string
    playback_scenario = None
    preffered_scenario = addon.getSetting('prem_scenario')
    scenarios = [i('playback-scenario')[0].string for i in soup('media-item') if
            i('playback-scenario') and i('playback-scenario')[0].string and
                i.find('cdn-name')]
    if 'FMS_CLOUD' in scenarios:
        playback_scenario = 'FMS_CLOUD'
    elif senario_types[preffered_scenario] in scenarios:
        playback_scenario = senario_types[preffered_scenario]
    else:
        if preffered_scenario == '0':
            # max bitrate for ondemand(not live) is 1800k, 1200k for some shows
            try:
                playback_scenario = [i for i in scenarios if 'FLASH_1800K' in i][0]
            except:
                try:
                    playback_scenario = [i for i in scenarios if 'FLASH_1200K' in i][0]
                except:
                    addon_log('playback scenario not foud')
                    addon_log('scenarios: %s' %scenarios)
        if not playback_scenario:
            playback_scenario = [i for i in scenarios if 'FLASH' in i][0]

    values = {
        'eventId': urllib.quote(event_id),
        'fingerprint': fprt,
        'identityPointId': ipid,
        'subject': urllib.quote('LIVE_EVENT_COVERAGE'),
        'platform': urllib.quote('WEB_MEDIAPLAYER'),
        'playbackScenario': urllib.quote(playback_scenario),
        'sessionKey': session_key,
        'streamSelection': 'linear'
        }
    data = make_request(event_url + urllib.urlencode(values), None, headers)
    addon_log('Response Data:')
    addon_log(str(data))
    soup = BeautifulStoneSoup(data, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
    try:
        stream_url = soup.url.string
        if not stream_url:
            raise
        addon_log('Returned URL: %s' %stream_url)
    except:
        addon_log('stream_url was not returned')
        try:
            status_message = soup('status-message')[0].string
            if status_message:
                addon_log('Status Message: %s' %status_message)
                notify(status_message)
                return
            else:
                raise
        except:
            addon_log(format_exc())
            notify('Unknown Error - Check Log')
            return
    # if playback_scenario == 'HTTP_CLOUD_WIRED':
        # hls = base64.decodestring(stream_url)
        # addon_log('HLS URL: %s' %hls)
    # else:
    pageurl = (' pageUrl=http://www.video.theblaze.com/shared/flash/mediaplayer/v4.4/R10/MP4.jsp?'
               'calendar_event_id=' + event_id + '&content_id=&media_id=&view_key=&'
               'media_type=video&source=THEBLAZE&sponsor=THEBLAZE&clickOrigin=&affiliateId=')
    swf = ' swfUrl=http://www.video.theblaze.com/shared/flash/mediaplayer/v4.4/R10/MediaPlayer4.swf swfVfy=1'
    if stream_url.startswith('http'):
        smil_url, auth = stream_url.split('?', 1)
        smil_soup = BeautifulStoneSoup(make_request(smil_url))
        bitrate_values = {
            '5': '300000',
            '4': '500000',
            '3': '800000',
            '2': '1200000',
            '1': '1800000',
            '0': '2400000'
            }
        rtmp_base = smil_soup.meta['base']
        for i in smil_soup('video'):
            if i['system-bitrate'] == bitrate_values[preffered_scenario]:
                path = i['src']
                break
            else:
                path = i['src']
        playpath = ' Playpath=%s?%s' %(path, auth)
        if 'ondemand' in rtmp_base:
            auth_string = '?_fcs_vhost=cp133280.edgefcs.net&akmfv=1.6&' + auth
            app = ' app=ondemand' + auth_string
        elif 'live' in rtmp_base:
            auth_string = '?_fcs_vhost=cp133278.live.edgefcs.net&akmfv=1.6&' + auth
            app = ' app=live' + auth_string
            swf += ' live=1'
        rtmp_url = rtmp_base[:-1] + auth_string
    else:
        if 'ondemand/' in stream_url:
            playpath = ' Playpath=' + stream_url.split('ondemand/')[1]
        elif 'live/' in stream_url:
            playpath = ' Playpath=' + stream_url.split('live/')[1]
            swf += ' live=1'
        app = ''
        rtmp_url = stream_url

    resolved_url = rtmp_url + app + playpath + pageurl + swf
    return resolved_url


def set_resolved_url(resolved_url):
    success = False
    if resolved_url:
        success = True
    else:
        resolved_url = ''
    item = xbmcgui.ListItem(path=resolved_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)


def notify(message):
    xbmc.executebuiltin("XBMC.Notification(%s, %s, 10000, %s)"
                        %('Addon Notification', message, icon))


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


def get_length_in_minutes(length):
    l_split = length.split(':')
    minutes = int(l_split[-2])
    if int(l_split[-1]) >= 30:
        minutes += 1
    if len(l_split) == 3:
        minutes += (int(l_split[0]) * 60)
    if minutes < 1:
        minutes = 1
    return minutes


def add_dir(name, url, iconimage, mode, info={}, ids={}):
    isfolder = True
    params = {'name': name, 'url': url, 'mode': mode, 'ids': ids}
    url = '%s?%s' %(sys.argv[0], urllib.urlencode(params))
    listitem = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    listitem.setProperty("Fanart_Image", fanart)
    if mode in ['resolve_url', 'resolve_episode_url', 'pass']:
        isfolder = False
        if mode != 'pass':
            listitem.setProperty('IsPlayable', 'true')
    listitem.setInfo('video', infoLabels=info)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isfolder)


# check if dir exists, needed to save cookies to file
if not xbmcvfs.exists(addon_profile):
    xbmcvfs.mkdir(addon_profile)

params = get_params()
addon_log(repr(params))
try:
    mode = params['mode']
except:
    mode = None

if mode == None:
    display_shows()
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_show':
    display_show(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_show_list':
    display_show_list(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'get_live_shows':
    display_live_shows()
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'select_calendar':
    select_calendar()
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'resolve_episode_url':
    set_resolved_url(resolve_prem_url(eval(params['ids'])))

elif mode == 'resolve_url':
    set_resolved_url(resolve_url(params['url']))

elif mode == 'pass':
    pass