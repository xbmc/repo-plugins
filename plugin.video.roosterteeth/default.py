import urllib
import urllib2
import cookielib
import re
import os
import json
import time
from datetime import datetime
from urlparse import urlparse, parse_qs
from traceback import format_exc

import xmltodict
import StorageServer
from bs4 import BeautifulSoup

import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs

cache = StorageServer.StorageServer("roosterteeth", 6)
addon = xbmcaddon.Addon()
addon_profile = xbmc.translatePath(addon.getAddonInfo('profile'))
addon_version = addon.getAddonInfo('version')
addon_id = addon.getAddonInfo('id')
home = addon.getAddonInfo('path')
icon = addon.getAddonInfo('icon')
fanart = addon.getAddonInfo('fanart')
language = addon.getLocalizedString
cookie_file = os.path.join(addon_profile, 'cookie_file')
cookie_jar = cookielib.LWPCookieJar(cookie_file)
base = 'http://roosterteeth.com'
debug = addon.getSetting('debug')

__addon__       = "plugin.video.roosterteeth"
__settings__    = xbmcaddon.Addon(id=__addon__ )
__language__    = __settings__.getLocalizedString
__images_path__ = os.path.join( xbmcaddon.Addon(id=__addon__ ).getAddonInfo('path'), 'resources', 'images' )
__date__        = "11 November 2014"
__version__     = "0.1.1"

def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log'
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message),level=xbmc.LOGDEBUG)


def notify(message):
    xbmc.executebuiltin("XBMC.Notification(%s, %s, 10000, %s)" %(language(30001), message, icon))


def make_request(url, data=None, location=False):
    if not xbmcvfs.exists(cookie_file):
        cookie_jar.save()
    cookie_jar.load(cookie_file, ignore_discard=True, ignore_expires=True)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    urllib2.install_opener(opener)
    addon_log('Request URL: %s' %url)
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0',
        'Referer': 'http://roosterteeth.com'
        }
    try:
        req = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(req)
        response_url = urllib.unquote_plus(response.geturl())
        data = response.read()
        cookie_jar.save(cookie_file, ignore_discard=False, ignore_expires=False)
        response.close()
        if location:
            return (response_url, data)
        else:
            return data
    except urllib2.URLError, e:
        addon_log('We failed to open "%s".' % url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' %e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' % e.code)


def get_soup(data):
    if data:
        if data.startswith('http'):
            data = make_request(data)
        try:
            bs = BeautifulSoup(data, 'html.parser')
        except:
#           Mangle the html source so hopefully the python parser can parse it 
            data = mangle_html(data)
#           Let's try again            
            try:
                bs = BeautifulSoup(data, 'html.parser')
#          :( giving up!
            except:
                bs = "Parse Error" 
        return bs

    
#The html parser of python <= 2.7.2 kinda sucks :(
#Patch for python <= 2.7.2 (windows: xbmc 12 and older, OS: current xbmc (xbmc 14) and older))
def mangle_html(data):
    print 'Python Version: ' + sys.version
    if (debug) == 'true':
        xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s " % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "mangling html!" ), xbmc.LOGNOTICE )
#    print "DEBUG info, str(data) before mangling it:" + str(data)
    data = re.sub(r'</scri["\']', '', data)
    data = re.sub(r"<scrip'", "", data)
    data = re.sub(r"</scrip'", "", data)
    data = re.sub(r"<!", "<script><!", data)
#    print "DEBUG info, str(data) after mangling it:" + str(data)    
    return data


def cache_active_rt_shows():

    def filter_items(item_list):
         parsed = []
         for i in item_list:
             try:
                 show = (i.b.string, i.a['href'], i.img['src'],
                         i('a')[2].b.string.split()[0], i.span.string)
                 if not show in parsed:
                     parsed.append(show)
             except:
                 addon_log('addonException: %s' %format_exc())
                 continue
         return parsed

    rt_url = 'http://roosterteeth.com/archive/series.php'
    soup = get_soup(rt_url)
    items = soup('table', class_="border boxBorder")[0].table('tr')
    
    if (debug) == 'true':
        xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "len(items)", str(len(items)) ), xbmc.LOGNOTICE )
    
    return filter_items(items)


def cache_active_ah_shows():

    def filter_items(item_list):
         parsed = []
         for i in item_list:
             try:
                 show = (i.b.string, i.a['href'], i.img['src'],
                         i('a')[2].b.string.split()[0], i.span.string)
                 if not show in parsed:
                     parsed.append(show)
             except:
                 addon_log('addonException: %s' %format_exc())
                 continue
         return parsed

    ah_url = 'http://ah.roosterteeth.com/archive/series.php'
    ah_soup = get_soup(ah_url)
    items = ah_soup('table', class_="border boxBorder")[0].table('tr')
    return filter_items(items)
 
 
def cache_retired_rt_shows():

    def filter_items(item_list):
         parsed = []
         for i in item_list:
             try:
                 show = (i.b.string, i.a['href'], i.img['src'],
                         i('a')[2].b.string.split()[0], i.span.string)
                 if not show in parsed:
                     parsed.append(show)
             except:
                 addon_log('addonException: %s' %format_exc())
                 continue
         return parsed

    rt_url = 'http://roosterteeth.com/archive/series.php'
    soup = get_soup(rt_url)
    retired_items = soup('table', class_="border boxBorder")[1].table('tr')
    return filter_items(retired_items)

    
def cache_retired_ah_shows():

    def filter_items(item_list):
         parsed = []
         for i in item_list:
             try:
                 show = (i.b.string, i.a['href'], i.img['src'],
                         i('a')[2].b.string.split()[0], i.span.string)
                 if not show in parsed:
                     parsed.append(show)
             except:
                 addon_log('addonException: %s' %format_exc())
                 continue
         return parsed

    ah_url = 'http://ah.roosterteeth.com/archive/series.php'
    ah_soup = get_soup(ah_url)
    retired_items = ah_soup('table', class_="border boxBorder")[1].table('tr')
    return filter_items(retired_items)
       
       
def get_shows(shows):
    for i in shows:
        if 'v=trending' in i[1]:
            i[1] = i[1].replace('v=trending','v=more')
        plot = ''
        if i[4]:
            plot = i[4]
        add_dir(i[0], base+i[1], 1, i[2], {'Episode': int(i[3]), 'Plot': plot})


def get_seasons(soup, iconimage):
    try:
        items = soup('td', class_="seasonsBox")[0]('a')
        if len(items) < 1:
            raise
    except IndexError:
        addon_log('Seasons Exception: %s' %format_exc())
        return False
    for i in items:
        name = i.string.encode('utf-8')
        try:
            meta = {'Season': int(name.split(':')[0].split()[1])}
        except:
            meta = {}
        add_dir(name, base+i['href'], 2, iconimage, meta, True)
    return True


def index(soup, season=True):
    episode_patterns = [re.compile('Episode (.+?):'), re.compile('Episode (.+?) -'),
                        re.compile('Volume (.+?):'), re.compile('#(.+?):')]
    if season:
        items = soup('div', attrs={'id' : "profileAjaxContent"})[0]('table')[1]('a')
    else:
        items = soup('div', attrs={'id' : "profileAjaxContent"})[0]('table')[0]('a')
    for i in items:
        href = i['href']
        item_id = href.split('id=')[1].split('&')[0]
        try:
            thumb = i.img['src']
        except:
            thumb = icon
        name = i('span')[0].string
        if name is None:
            name = i('span')[0].contents[0]
        try:
            if (not i('span')[1].string is None) and (not i('span')[1].string in name):
                name += ': ' + i('span')[1].string
        except:
            pass
        name = name.encode('utf-8', 'ignore')
        meta = {}
        duration = i.td.string
        if duration:
            meta['Duration'] = get_duration(duration)
        for i in episode_patterns:
            try:
                meta['Episode'] = int(i.findall(name)[0])
                break
            except:
                pass
        add_dir(name, item_id, 3, thumb, meta, False, False)
    try:
        next_page = soup('a', attrs={'id' : "streamLoadMore"})[0]['href']
        add_dir(language(30002), base + next_page, 2, icon, {}, season)
    except:
        addon_log("Didn't find next page!")



def check_sorry(soup):
    sorry = ['Video recordings and live broadcasts of the podcast are only available for Sponsors.',
             'Sorry, you must be a Sponsor to see this video.']
    for i in sorry:
        pattern = re.compile(i)
        if pattern.findall(str(soup)):
            notify(language(30003))
            addon_log(i)
            return True


def get_blip_location(blip_url):
    blip_data = make_request(blip_url, location=True)
    pattern = re.compile('http://blip.tv/rss/flash/(.+?)&')
    try:
        feed_id = pattern.findall(blip_data[0])[0]
    except IndexError:
        patterns = [re.compile('config.id = "(.+?)";'),
                    re.compile('data-episode-id="(.+?)"')]
        for i in patterns:
            try:
                feed_id = i.findall(blip_data[1])[0]
            except IndexError:
                feed_id = None
                pass
            if feed_id:
                break
        if not feed_id:
            addon_log('Did not find the feed ID')
            return
    blip_xml = 'http://blip.tv/rss/flash/' + feed_id
    media_content = []
    try:
        blip_dict = xmltodict.parse(make_request(blip_xml))
        items = blip_dict['rss']['channel']['item']['media:group'][u'media:content']
        # if only one result items will be a dict
        if isinstance(items, dict):
            try:
                return items['@url']
            except:
                raise
        media_content = [i for i in items if i.has_key('@blip:role')]
    except:
        addon_log('addonException: %s' %format_exc())
        return
    if len(media_content) < 1:
        addon_log('Did not find media content')
        return
    url = None
    default = None
    preferred_quality = addon.getSetting('quality')
    if preferred_quality == '0':
        try:
            items = [{'type': i['@blip:role'], 'url': i['@url']} for i in media_content if
                     '720' in i['@blip:role'] or 'Source' in i['@blip:role']]
            if len(items) == 1:
                return items[0]['url']
            else:
                try:
                    return [i['url'] for i in items if '720' in i['type']][0]
                except:
                    return [i['url'] for i in items if 'Source' in i['type']][0]
        except IndexError:
            addon_log('Preffered setting not found')
    elif preferred_quality == '1':
        try:
            url = [i['@url'] for i in media_content if
                   'Blip SD' in i['@blip:role'] or 'web' in i['@blip:role']][0]
            return url
        except IndexError:
            addon_log('Preffered setting not found')
    elif preferred_quality == '2':
        try:
            url = [i['@url'] for i in media_content if
                   'Blip LD' in i['@blip:role'] or 'Portable' in i['@blip:role']][0]
            return url
        except IndexError:
            addon_log('Preffered setting not found')
    elif preferred_quality == '3':
        try:
            dialog = xbmcgui.Dialog()
            ret = dialog.select(language(30006), [i['@blip:role'] for i in media_content])
            if ret > -1:
                return media_content[ret]['@url']
        except:
            addon_log('addonException: select stream: %s' %format_exc())
            return
    try:
        url = [i['@url'] for i in media_content if
               i.has_key('@isDefault') and i['@isDefault'] == 'true'][0]
        return url
    except IndexError:
        addon_log('addonException: did not find a default type')
        return media_content[0]['@url']


def get_podcasts():
    podcast_path = 'http://s3.roosterteeth.com/podcasts/'
    add_dir('RT Podcast', podcast_path + 'index.xml', 5, podcast_path + 'rtpodcast.jpg')
    add_dir('The Patch', podcast_path + 'gaming-index.xml', 5, podcast_path + 'gamingpodcast.jpg')
    add_dir('Spoilercast', podcast_path + 'spoiler-index.xml', 5, podcast_path + 'spoilercast_black.jpg')


def get_podcasts_episodes(url, iconimage):
    data = make_request(url)
    pod_dict = xmltodict.parse(data)
    items = pod_dict['rss']['channel']['item']
    for i in items:
        title = i['title'].encode('utf-8')
        date_time = datetime(*(time.strptime(i['pubDate'], '%a, %d %b %Y %H:%M:%S GMT')[0:6]))
        meta = {'Duration': get_duration(i['itunes:duration']),
                'Date': date_time.strftime('%d.%m.%Y'),
                'Premiered': date_time.strftime('%d-%m-%Y'),
                'Episode': title.split('#')[1]}
        add_dir('%s :  %s' %(title, i['description']),
                i['link'], 6, iconimage, meta, False, False)


def resolve_url(item_id, retry=False):
    url = 'http://roosterteeth.com/archive/new/_loadEpisode.php?id=%s&v=morev' %item_id
    data = json.loads(make_request(url))
 
    if len(data) <= 10:
#      trying a different resolve method
       path = resolve_url_youtube_bliptv(item_id)
       if path == "":
#      trying yet another resolve method
            path = resolve_url_cloudfront(item_id)
            if path == "":
                if retry:
                    addon_log('retryException: %s' %format_exc())
                    notify(language(30024))
                    xbmc.sleep(3000)
                else:
                    if addon.getSetting('is_sponsor') == 'true':
                        logged_in = check_login()
                        if not logged_in:
                            logged_in = login()
                            if logged_in:
                                return resolve_url(item_id, True)
                            else:
                                notify(language(30025))
                                xbmc.sleep(3000)
                        else:
                            notify(language(30003))
                            xbmc.sleep(3000)        
                    else:
                        notify(language(30003))
                        xbmc.sleep(3000)
            else:
                return path    
       else:            
            return path
    else:
        soup = get_soup(data['embed']['html'])
        try:
            filetype = soup.div['data-filetype']
            if filetype == 'youtube':
                youtube_id = soup.iframe['src'].split('/')[-1].split('?')[0]
                addon_log('youtube id:' + youtube_id)
                path = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' %youtube_id
            elif filetype == 'blip':
                blip_url = soup.iframe['src']
                addon_log('blip_url: ' + blip_url)
                path = get_blip_location(blip_url)
                addon_log('path: %s' %path)
            return path
        except:
            if retry:
                addon_log('retryException: %s' %format_exc())
                sorry = check_sorry(soup)
            elif addon.getSetting('is_sponsor') == 'true':
                logged_in = check_login()
                if not logged_in:
                    logged_in = login()
                    if logged_in:
                        return resolve_url(item_id, True)
                    notify(language(30025))
                    xbmc.sleep(5000)
                sorry = check_sorry(soup)
            else:
                sorry = check_sorry(soup)
            if not sorry:
                notify(language(30024))
                addon_log('addonException: resolve_url')


def resolve_url_youtube_bliptv(item_id):
    url = 'http://roosterteeth.com/archive/?id=%s' %item_id
    
    if (debug) == 'true':
        xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "url1", str(url) ), xbmc.LOGNOTICE )
    
    data = make_request(url)
    data = str(data)    

#search for embedded youtube vid    
#<div id="nowPlayingEmbed" data-filetype="youtube"><iframe id="ytIframe" width="720" height="405" src="http://www.youtube.com/embed/qad_VTlD9PE?enablejsapi=1&rel=0&modestbranding=1&showsearch=0&autohide=1&iv_load_policy=1&wmode=transparent" frameborder="0" allowfullscreen></iframe></div>
    start_pos_youtubeid = data.find("http://www.youtube.com/embed/")
    if start_pos_youtubeid == -1:
#search for blip.tv vid    
#<iframe src="http://blip.tv/play/hO4bg7G0TAA.html?p=1&autostart=true" width="720" height="435" frameborder="0" allowfullscreen>
        start_pos_blipid_url = data.find("http://blip.tv/play/")
        if start_pos_blipid_url == -1:
            path = ""
        else:
            end_pos_blipid_url = data.find("?",start_pos_blipid_url + 1)
            blipid_url = str(data[start_pos_blipid_url:end_pos_blipid_url]) + ".html"
            path = get_blip_location(blipid_url)
    else:
        start_pos_youtubeid = start_pos_youtubeid + len ("http://www.youtube.com/embed/")
        end_pos_youtubeid = data.find("?",start_pos_youtubeid + 1)
        youtubeid = str(data[start_pos_youtubeid:end_pos_youtubeid])
        path = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' %youtubeid
   
    if (debug) == 'true':
        xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "path1", str(path) ), xbmc.LOGNOTICE )
        
    return path


def resolve_url_cloudfront(item_id):
#     <script type='text/javascript'>
#                     jwplayer('video-9902').setup({
#                         image: "http://s3.amazonaws.com/s3.roosterteeth.com/assets/epart/ep9902.jpg",
#                         sources: [
#                             {file: "http://d1gi7itbhq9gjf.cloudfront.net/encoded/9902/RT_54526b494490c6.67517070-480p.mp4", label: "480p SD","default": "true"},
#                             {file: "http://d1gi7itbhq9gjf.cloudfront.net/encoded/9902/RT_54526b494490c6.67517070-720p.mp4", label: "720p HD"},
#                             {file: "http://d1gi7itbhq9gjf.cloudfront.net/encoded/9902/RT_54526b494490c6.67517070-1080p.mp4", label: "1080p HD"},
#                         ],
#                         title: 'RWBY Volume 2, Chapter 12',
#                         width: '590',
#                         height: '405',
#                         aspectratio: '16:9',
#                         sharing: '{}',
#                           advertising: {
#                             client: 'googima',
#                             tag: 'http://googleads.g.doubleclick.net/pagead/ads?ad_type=video&client=ca-video-pub-0196071646901426&description_url=http%3A%2F%2Froosterteeth.com&videoad_start_delay=0&hl=en&max_ad_duration=30000'
#                           }
#                     });
#                 </script>

    url = 'http://roosterteeth.com/archive/?id=%s' %item_id
    
    if (debug) == 'true':
        xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "url2", str(url) ), xbmc.LOGNOTICE )
    
    data = make_request(url)
     
    data = str(data)    
    start_pos_sources = data.find("sources")   
    if start_pos_sources == -1: 
        path = ""
    else:
        start_pos_480p = data.find("{",start_pos_sources)
        end_pos_480p = data.find("}",start_pos_480p + 1)
        string_480p = data[start_pos_480p:end_pos_480p + 1]
        start_pos_480p_file = string_480p.find("http")
        end_pos_480p_file = string_480p.find('"',start_pos_480p_file + 1)
        string_480p_file = string_480p[start_pos_480p_file:end_pos_480p_file]
        
        start_pos_720p = data.find("{",end_pos_480p + 1)
        end_pos_720p = data.find("}",start_pos_720p + 1)
        string_720p = data[start_pos_720p:end_pos_720p + 1]
        start_pos_720p_file = string_720p.find("http")
        end_pos_720p_file = string_720p.find('"',start_pos_720p_file + 1)
        string_720p_file = string_720p[start_pos_720p_file:end_pos_720p_file]
     
        start_pos_1080p = data.find("{",end_pos_720p + 1)
        end_pos_1080p = data.find("}",start_pos_1080p + 1)
        string_1080p = data[start_pos_1080p:end_pos_1080p + 1]
        start_pos_1080p_file = string_1080p.find("http")
        end_pos_1080p_file = string_1080p.find('"',start_pos_1080p_file + 1)
        string_1080p_file = string_1080p[start_pos_1080p_file:end_pos_1080p_file]
       
        preferred_quality = addon.getSetting('quality')
#       high video quality  
        if preferred_quality == '0':
            path = string_1080p_file
#       medium video quality  
        elif preferred_quality == '1':
            path = string_720p_file
#       low video quality          
        else: 
            path = string_480p_file
        
    if (debug) == 'true':
        xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "path2", str(path) ), xbmc.LOGNOTICE )
        
    return path

                
def resolve_podcast_url(episode_url, retry=False):
    soup = get_soup(episode_url)
    if soup == "Parse Error":
        is_video = False
    else:     
        is_video = soup('embed')
        
    if soup == "Parse Error":
        pass
    elif is_video:
        try:
            if 'swf#' in soup.embed['src']:
                blip_id = soup.embed['src'].split('swf#')[1]
                resolved = get_blip_location('http://blip.tv/play/' + blip_id)
                return resolved
        except:
            addon_log('addonException resolve_podcast_url: %s' %format_exc())
    elif retry:
        addon_log('No video embed found')
        sorry = check_sorry(soup)
        if not sorry:
            notify(language(30024))
    elif addon.getSetting('is_sponsor') == 'true':
        logged_in = check_login()
        if not logged_in:
            logged_in = login()
            if logged_in:
                return resolve_podcast_url(episode_url, True)
            notify(language(30025))
            xbmc.sleep(3000)
            sorry = check_sorry(soup)
    else:
        sorry = check_sorry(soup)
    
    if soup == "Parse Error":
        pass
    elif sorry:
        xbmc.sleep(5000)

    if soup == "Parse Error":
        pass
    else:
        try:
            downloads = []
            items = soup.find('div', class_="titleLine", text="DOWNLOAD").findNext('div')('a')
            for i in items:
                downloads.append((i.b.contents[0], i['href']))
            if len(downloads) > 0:
                dialog = xbmcgui.Dialog()
                ret = dialog.select(language(30004), [i[0] for i in downloads])
                if ret > -1:
                    return downloads[ret][1]
        except:
            downloads = []

def set_resolved_url(resolved_url):
    success = False
    if resolved_url:
        success = True
    else:
        resolved_url = ''
    item = xbmcgui.ListItem(path=resolved_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)


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


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


def add_dir(name, url, mode, iconimage, meta={}, season=False, isfolder=True):
    params = {'name': name, 'url': url, 'mode': mode, 'iconimage': iconimage, 'season': season}
    url = '%s?%s' %(sys.argv[0], urllib.urlencode(params))
    listitem = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    listitem.setProperty( "Fanart_Image", fanart )
    meta["Title"] = name
    meta['Genre'] = language(30026)
    if not isfolder:
        listitem.setProperty('IsPlayable', 'true')
    listitem.setInfo(type="Video", infoLabels=meta)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isfolder)


def check_login():
    logged_in = False
#commenting from here fixes the need to delete cookiefile when watching sponsored videos    
#    cookies = {}
#    cookie_jar.load(cookie_file, ignore_discard=False, ignore_expires=False)
#    for i in cookie_jar:
#        cookies[i.name] = i.value
#    if cookies.has_key('rtusername') and cookies['rtusername'] == addon.getSetting('username'):
#        logged_in = True
#        addon_log('Already logged in')
#commenting to here fixes the need to delete cookiefile when watching sponsored videos  
    return logged_in


def login():
    url = 'https://roosterteeth.com/members/signinPost.php'
    username = addon.getSetting('username')
    login_data = {'pass': addon.getSetting('password'),
                  'user': username,
                  'return': '/sponsor/'}
    data = make_request(url, urllib.urlencode(login_data))
    soup = get_soup(data)
    if soup == "Parse Error":
# let's guess that the user is logged in, so the user doesn't get a confusing not-logged-in-error-message
       return True
    else:
        logged_in_tag = soup.find('span', attrs={'id': 'signedInName'})
        if logged_in_tag and username in str(logged_in_tag):
            addon_log('Logged in successfully')
            return True
        else:
            return False


def set_view_mode():
    view_modes = {
        '0': '502',
        '1': '51',
        '2': '3',
        '3': '504',
        '4': '503',
        '5': '515'
        }
    view_mode = addon.getSetting('view_mode')
    if view_mode == '6':
        return
    xbmc.executebuiltin('Container.SetViewMode(%s)' %view_modes[view_mode])


# check if dir exists, needed to save cookies to file
if not xbmcvfs.exists(addon_profile):
    xbmcvfs.mkdir(addon_profile)

params = get_params()

try:
    mode = int(params['mode'])
except:
    mode = None

if (debug) == 'true':
    xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "mode!", str(mode) ), xbmc.LOGNOTICE )
    

addon_log(repr(params))

if mode == None:
    # display main plugin dir
    print 'Python Version: ' + sys.version
    add_dir(language(30008), 'get_latest_rt', 8, icon)
    add_dir(language(30027), 'get_latest_ah', 9, icon)
    add_dir(language(30005), 'get_podcasts', 4, icon)
        
    act_rt_shows = cache_active_rt_shows()
    act_ah_shows = cache_active_ah_shows()

#   mix the shows     
    act_shows = []
    while True:
        try:
            act_shows.append(act_rt_shows.pop(0))
            act_shows.append(act_ah_shows.pop(0))
        except IndexError:
            break

#   add any remaining shows at the end  
    act_shows = act_shows + act_rt_shows + act_ah_shows
    
    get_shows(act_shows)
    add_dir(language(30007), 'get_retired_shows', 7, icon)
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 1:
    # display show, if seasons, else episodes
    soup = get_soup(params['url'])
    seasons = get_seasons(soup, params['iconimage'])
    if seasons:
        xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    else:
        index(soup, False)
        set_view_mode()
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 2:
    # display show episodes
    soup = get_soup(params['url'])
    index(soup, params['season'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 3:
    # resolve show episode
    set_resolved_url(resolve_url(params['url']))
    
elif mode == 4:
    # display podcast dir
    get_podcasts()
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 5:
    # display podcast episodes
    get_podcasts_episodes(params['url'], params['iconimage'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 6:
    # resolve podcast episode
    set_resolved_url(resolve_podcast_url(params['url']))

elif mode == 7:
    # display retired shows
    ret_rt_shows = cache_retired_rt_shows()
    ret_ah_shows = cache_retired_ah_shows()

#   mix the shows     
    ret_shows = []
    while True:
        try:
            ret_shows.append(ret_rt_shows.pop(0))
            ret_shows.append(ret_ah_shows.pop(0))
        except IndexError:
            break
        
#   add any remaining shows at the end  
    ret_shows = ret_shows + ret_rt_shows + ret_ah_shows
 
    get_shows(ret_shows)
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 8:
    # display latest RT episodes
    soup = get_soup('http://roosterteeth.com/archive/?v=newest')
    index(soup, False)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
elif mode == 9:
    # display latest AH episodes
    soup = get_soup('http://ah.roosterteeth.com/archive/?v=newest')
    index(soup, False)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))    