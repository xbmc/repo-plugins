#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import StorageServer
import os
import re
import urllib
import urllib2
import xbmcaddon
import xbmcgui
import xbmcplugin
import xmltodict
from bs4 import BeautifulSoup
from urlparse import parse_qs

cache = StorageServer.StorageServer("cnetpodcasts", 6)
addon = xbmcaddon.Addon()
addon_version = addon.getAddonInfo('version')
addon_id = addon.getAddonInfo('id')
icon = addon.getAddonInfo('icon')
language = addon.getLocalizedString
latest_videos_href = 'http://feeds2.feedburner.com/cnet/allhdpodcast'


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log'
    xbmc.log("[%s-%s]: %s" % (addon_id, addon_version, log_message), level=xbmc.LOGDEBUG)


def make_request(url, post_data=None):
    addon_log('Request URL: %s' % url)
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0',
        'Referer': 'http://www.cnet.com'
    }
    try:
        req = urllib2.Request(url, post_data, headers)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data
    except urllib2.URLError, e:
        addon_log('We failed to open "%s".' % url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' % e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' % e.code)


def cache_categories():
    # url = 'http://www.cnet.com/podcasts/'
    url = 'http://www.cnet.com/cnet-podcasts/'
    soup = BeautifulSoup(make_request(url), 'html.parser')
    items = soup.find_all('a', attrs={'href': re.compile("hd.xml$")})
    cats = [{'thumb': '',
             'name': i['href'],
             'desc': '',
             'links': i['href']} for
            i in items]
    return cats


def display_categories():
    cats = cache.cacheFunction(cache_categories)
    previous_name = ''

    # add a category
    name = 'Latest Videos'
    add_dir(name, latest_videos_href, 'category', '', {'Plot': ''})

    for i in cats:
        name = str(i['name'])
        name = name.replace("http://feed.cnet.com/feed/podcast/", "")
        name = name.replace("-", " ")
        name = name.replace("/", " ")
        name = name.replace("hd.xml", "")
        name = name.capitalize()

        # skip name if it is the same as the previous name
        if name == previous_name:
            pass
        else:
            previous_name = name
            add_dir(name, i['links'], 'category', i['thumb'], {'Plot': i['desc']})


def display_category(links_list):
    url = links_list

    soup = BeautifulSoup(make_request(url), 'html.parser')

    # latest videos isn't a real category in CNET, therefore this hardcoded stuff was needed
    if url == latest_videos_href:
        urls = soup.find_all('a', attrs={'href': re.compile("^http://feedproxy.google.com/")})
        # <a href="http://feedproxy.google.com/~r/cnet/allhdpodcast/~3/4RHUa95GiUM/14n041814_walkingpalua_740.mp4">A walk among hidden graves and WWII bombs</a>
        for url in urls:
            title = str(url)
            title = title.replace('</a>', '')
            title = title.replace("&#039;", "'")
            pos_last_greater_than_sign = title.rfind('>')
            title = title[pos_last_greater_than_sign + 1:]

            meta = {'Plot': title,
                    'Duration': '',
                    'Date': '',
                    'Premiered': ''}

            add_dir(title, url['href'], 'resolve', 'Defaultvideo.png', meta, False)
    else:
        #     <item>
        #           <title><![CDATA[Inside Scoop: Will acquiring Nokia devices give Microsoft an edge?]]></title>
        #           <link>http://www.podtrac.com/pts/redirect.mp4/dw.cbsi.com/redir/13n0903_MicrosoftScoop_740.m4v?destUrl=http://download.cnettv.com.edgesuite.net/21923/2013/09/03/13n0903_MicrosoftScoop_740.m4v</link>
        #           <author>feedback-cnettv@cnet.com (CNETTV)</author>
        #           <description><![CDATA[Details of the Microsoft and Nokia deal are now finalized. CNET's Josh Lowensohn discusses the effects the merger could have on customers, Microsoft's sagging market share, and the selection of a new Microsoft CEO.]]></description>
        #           <itunes:subtitle><![CDATA[Details of the Microsoft and Nokia deal are now finalized. CNET's Josh Lowensohn discusses the effects the merger could have on customers, Microsoft's sagging market share, and the selection of a new Microsoft CEO.]]></itunes:subtitle>
        #           <itunes:summary><![CDATA[Details of the Microsoft and Nokia deal are now finalized. CNET's Josh Lowensohn discusses the effects the merger could have on customers, Microsoft's sagging market share, and the selection of a new Microsoft CEO.]]></itunes:summary>
        #           <itunes:explicit>no</itunes:explicit>
        #           <itunes:author>CNET.com</itunes:author>
        #           <guid isPermaLink="false">35ffbba2-67e4-11e3-a665-14feb5ca9861</guid>
        #           <itunes:duration></itunes:duration>
        #           <itunes:keywords>
        #               CNET
        #                CNETTV
        #             Tech Industry
        #           </itunes:keywords>
        #           <enclosure url="http://www.podtrac.com/pts/redirect.mp4/dw.cbsi.com/redir/13n0903_MicrosoftScoop_740.m4v?destUrl=http://download.cnettv.com.edgesuite.net/21923/2013/09/03/13n0903_MicrosoftScoop_740.m4v" length="0" type="video/mp4"/>
        #           <category>Technology</category>
        #           <pubDate>Fri, 21 Feb 2014 19:49:08 PST</pubDate>
        #     </item>
        urls = soup.find_all('enclosure', attrs={'url': re.compile("^http")})

        # skip 2 titles
        title_index = 2

        for url in urls:
            titles = soup.find_all('title')
            title = str(titles[title_index])
            title_index = title_index + 1
            title = title.replace("<title><![CDATA[", "")
            title = title.replace("]]></title>", "")
            title = title.replace("&#039;", "'")

            meta = {'Plot': title,
                    'Duration': '',
                    'Date': '',
                    'Premiered': ''}

            add_dir(title, url['url'], 'resolve', 'Defaultvideo.png', meta, False)


def resolve_url(video_id):
    parameters = {
        'iod': 'images,videoMedia,relatedLink,breadcrumb,relatedAssets,broadcast,lowcache',
        'partTag': 'cntv',
        'players': 'Download,RTMP',
        'showBroadcast': 'true',
        'videoIds': video_id,
        'videoMediaType': 'preferred'
    }
    data = make_request('http://api.cnet.com/restApi/v1.0/videoSearch?' + urllib.urlencode(parameters))
    pod_dict = xmltodict.parse(data)
    media_item = pod_dict['CNETResponse']['Videos']['Video']
    # thumb = [i['ImageURL'] for i in media_item['Images']['Image'] if i['@width'] == '360'][0]
    media_items = media_item['VideoMedias']['VideoMedia']
    stream_urls = [i['DeliveryUrl'] for i in media_items if i['Height'] == '720']
    if stream_urls:
        return stream_urls[0]


def add_dir(name, url, modus, iconimage, meta=None, isfolder=True):
    if meta is None:
        meta = {}
    parameters = {'name': name, 'url': url, 'mode': modus}
    url = '%s?%s' % (sys.argv[0], urllib.urlencode(parameters))
    list_item = xbmcgui.ListItem(name, thumbnailImage=iconimage)
    if isfolder:
        list_item.setProperty('IsPlayable', 'false')
    else:
        list_item.setProperty('IsPlayable', 'true')
    ADDON = "plugin.video.cnet.podcasts"
    IMAGES_PATH = os.path.join(xbmcaddon.Addon(id=ADDON).getAddonInfo('path'), 'resources', 'images')
    list_item.setProperty('Fanart_Image', os.path.join(IMAGES_PATH, 'fanart-blur.jpg'))
    # Add refresh option to context menu
    list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, isfolder)


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


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
    xbmc.executebuiltin('Container.SetViewMode(%s)' % view_modes[view_mode])


params = get_params()

try:
    mode = params['mode']
except:
    mode = None

addon_log(repr(params))

if not mode:
    display_categories()
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'category':
    display_category(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'resolve':
    item = xbmcgui.ListItem(path=params['url'])
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
