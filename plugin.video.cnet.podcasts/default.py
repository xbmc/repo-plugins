#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import StorageServer
import os
import re
import urllib
import requests
from time import strptime
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmc
import sys
from bs4 import BeautifulSoup
from urlparse import parse_qs

ADDON = "plugin.video.cnet.podcasts"
SETTINGS = xbmcaddon.Addon()
LANGUAGE = SETTINGS.getLocalizedString
IMAGES_PATH = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'images')
HEADERS = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0','Referer': 'http://www.cnet.com'}
CACHE = StorageServer.StorageServer("cnetpodcasts", 6)
BASE_URL = 'http://www.cnet.com/cnet-podcasts/'
DATE = "2017-07-12"
VERSION = "1.0.4"


def cache_categories():
    html_source = requests.get(BASE_URL, headers=HEADERS).text
    soup = BeautifulSoup(html_source)
    items = soup.find_all('a', attrs={'href': re.compile("hd.xml$")})
    cats = [{'thumb': '',
             'name': i['href'],
             'desc': '',
             'links': i['href']} for
            i in items]
    return cats


def display_categories():
    cats = CACHE.cacheFunction(cache_categories)
    previous_name = ''

    for i in cats:

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "cat", str(i)), xbmc.LOGDEBUG)

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

    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
        ADDON, VERSION, DATE, "url", str(url)), xbmc.LOGDEBUG)

    html_source = requests.get(url, headers=HEADERS).text
    soup = BeautifulSoup(html_source)

    # xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
    #     ADDON, VERSION, DATE, "soup", str(soup)), xbmc.LOGDEBUG)

    items = soup.find_all('item')

    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
        ADDON, VERSION, DATE, "len(items)", str(len(items))), xbmc.LOGDEBUG)

    # <item>
    # <title><![CDATA[This TV has Amazon Alexa built-in, but it's not what you think]]></title>
    # <link>http://dw.cbsi.com/redir/FL_amazon_tv_1353763_2696.mp4?destUrl=http://download.cnettv.com.edgesuite.net/21923/mpx/2017/07/12/994479171622/FL_amazon_tv_1353763_2696.mp4</link>
    # <author>feedback-cnettv@cnet.com (CNETTV)</author>
    # <description><![CDATA[The Element Amazon Fire TV Edition features thousands of apps and Alexa Voice control. So what's the catch?]]></description>
    # <itunes:subtitle><![CDATA[The Element Amazon Fire TV Edition features thousands of apps and Alexa Voice control. So what's the catch?]]></itunes:subtitle>
    # <itunes:summary><![CDATA[The Element Amazon Fire TV Edition features thousands of apps and Alexa Voice control. So what's the catch?]]></itunes:summary>
    # <itunes:explicit>no</itunes:explicit>
    # <itunes:author>CNET.com</itunes:author>
    # <guid ispermalink="false">a18291b5-2122-48a8-a42c-9cde4c6d3951</guid>
    # <itunes:duration></itunes:duration>
    # <itunes:keywords>
    #                     CNET
    #                     CNETTV
    #                     TVs
    #                 </itunes:keywords>
    # <enclosure length="0" type="video/mp4" url="http://dw.cbsi.com/redir/FL_amazon_tv_1353763_2696.mp4?destUrl=http://download.cnettv.com.edgesuite.net/21923/mpx/2017/07/12/994479171622/FL_amazon_tv_1353763_2696.mp4"></enclosure>
    # <category>Technology</category>
    # <pubdate>Fri, 14 Jul 2017 14:57:27 PDT</pubdate>
    # </item>

    for item in items:

        # xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
        #     ADDON, VERSION, DATE, "item", str(item)), xbmc.LOGDEBUG)

        # <enclosure url="http://dw.cbsi.com/redir/AB445_1164934_2696.mp4?destUrl=http://download.cnettv.com.edgesuite.net/21923/mpx/2017/07/12/994592835973/AB445_1164934_2696.mp4" length="0" type="video/mp4"/>
        # get the url of the video
        url = item.link.string

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "url", str(url)), xbmc.LOGDEBUG)

        # Get title
        title = item.title.string

        try:
            title = title.encode('utf-8')
        except:
            pass

        title = title.replace('-', ' ')
        title = title.replace('/', ' ')
        title = title.replace(' i ', ' I ')
        title = title.replace(' ii ', ' II ')
        title = title.replace(' iii ', ' III ')
        title = title.replace(' iv ', ' IV ')
        title = title.replace(' v ', ' V ')
        title = title.replace(' vi ', ' VI ')
        title = title.replace(' vii ', ' VII ')
        title = title.replace(' viii ', ' VIII ')
        title = title.replace(' ix ', ' IX ')
        title = title.replace(' x ', ' X ')
        title = title.replace(' xi ', ' XI ')
        title = title.replace(' xii ', ' XII ')
        title = title.replace(' xiii ', ' XIII ')
        title = title.replace(' xiv ', ' XIV ')
        title = title.replace(' xv ', ' XV ')
        title = title.replace(' xvi ', ' XVI ')
        title = title.replace(' xvii ', ' XVII ')
        title = title.replace(' xviii ', ' XVIII ')
        title = title.replace(' xix ', ' XIX ')
        title = title.replace(' xx ', ' XXX ')
        title = title.replace(' xxi ', ' XXI ')
        title = title.replace(' xxii ', ' XXII ')
        title = title.replace(' xxiii ', ' XXIII ')
        title = title.replace(' xxiv ', ' XXIV ')
        title = title.replace(' xxv ', ' XXV ')
        title = title.replace(' xxvi ', ' XXVI ')
        title = title.replace(' xxvii ', ' XXVII ')
        title = title.replace(' xxviii ', ' XXVIII ')
        title = title.replace(' xxix ', ' XXIX ')
        title = title.replace(' xxx ', ' XXX ')
        title = title.replace('  ', ' ')
        # in the title of the item a single-quote "'" is represented as "&#039;" for some reason . Therefore this replace is needed to fix that.
        title = title.replace("&#039;", "'")

        xbmc.log(
            "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "title", str(title)),
            xbmc.LOGDEBUG)

        context_menu_items = []
        # Add refresh option to context menu
        context_menu_items.append((LANGUAGE(30104), 'Container.Refresh'))
        # Add episode  info to context menu
        context_menu_items.append((LANGUAGE(30105), 'XBMC.Action(Info)'))

        # Get description
        plot_start_pos = str(item).find("itunes:summary><![CDATA[") + len("itunes:summary><![CDATA[")
        plot_end_pos = str(item).find("]", plot_start_pos)
        plot = str(item)[plot_start_pos:plot_end_pos]

        xbmc.log(
            "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "plot", str(plot)),
            xbmc.LOGDEBUG)

        # in the title of the item a single-quote "'" is represented as "&#039;" for some reason . Therefore this replace is needed to fix that.
        try:
            plot = plot.replace("&#039;", "'")
        except:
            plot = title

        # Get pubdate
        pubdate = item.pubdate.string
        # Extract date time fields
        day = pubdate[len('Fri, '):len('Fri, ') + 2]
        month_name = pubdate[len('Fri, 01 '):len('Fri, 01 ') + 3]
        year = pubdate[len('Fri, 01 Mar '):len('Fri, 01 Mar ') + 4]
        hour = pubdate[len('Fri, 01 Mar 2016 '):len('Fri, 01 Mar 2016 ') + 2]
        minute = pubdate[len('Fri, 01 Mar 2016 17:'):len('Fri, 01 Mar 2016 17:') + 2]
        second = pubdate[len('Fri, 01 Mar 2016 17:40:'):len('Fri, 01 Mar 2016 17:40:') + 2]

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "extracted pubdate",
            str(day + '/' + month_name + '/' + year + '/' + hour + '/' + minute + '/' + second)), xbmc.LOGDEBUG)

        month_numeric = strptime(month_name, '%b').tm_mon

        xbmc.log(
            "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "month_numeric", str(month_numeric)),
            xbmc.LOGDEBUG)

        if len(str(month_numeric)) == 1:
            month = '0' + str(month_numeric)
        else:
            month = str(month_numeric)

        # Dateadded has this form: 2009-04-05 23:16:04
        dateadded = year + '-' + month + '-' + day + ' ' + hour + ':' + minute + ':' + second

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "dateadded", str(dateadded)),
                 xbmc.LOGDEBUG)

        meta = {'plot': plot,
                'duration': '',
                'year': year,
                'dateadded': dateadded}

        add_dir(title, url, 'resolve', 'Defaultvideo.png', meta, False)


def add_dir(name, url, modus, iconimage, meta=None, isfolder=True):
    add_sort_methods()

    context_menu_items = []
    # Add refresh option to context menu
    context_menu_items.append((LANGUAGE(30104), 'Container.Refresh'))
    # Add episode  info to context menu
    context_menu_items.append((LANGUAGE(30105), 'XBMC.Action(Info)'))

    if meta is None:
        meta = {}
    parameters = {'name': name, 'url': url, 'mode': modus}
    url = '%s?%s' % (sys.argv[0], urllib.urlencode(parameters))
    list_item = xbmcgui.ListItem(name, thumbnailImage=iconimage)
    if isfolder:
        list_item.setProperty('IsPlayable', 'false')
    else:
        list_item.setProperty('IsPlayable', 'true')
    list_item.setProperty('Fanart_Image', os.path.join(IMAGES_PATH, 'fanart-blur.jpg'))
    list_item.setInfo("mediatype", "video")
    list_item.setInfo("video", meta)
    # Adding context menu items to context menu
    list_item.addContextMenuItems(context_menu_items, replaceItems=False)
    # Add our item to directory
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, isfolder)


def add_sort_methods():
    sort_methods = [xbmcplugin.SORT_METHOD_UNSORTED,xbmcplugin.SORT_METHOD_LABEL,xbmcplugin.SORT_METHOD_DATE,xbmcplugin.SORT_METHOD_DURATION,xbmcplugin.SORT_METHOD_EPISODE]
    for method in sort_methods:
        xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod=method)


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
    view_mode = SETTINGS.getSetting('view_mode')
    if view_mode == '6':
        return
    xbmc.executebuiltin('Container.SetViewMode(%s)' % view_modes[view_mode])

params = get_params()

try:
    mode = params['mode']
except:
    mode = None
    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
        ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGDEBUG)

xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
    ADDON, VERSION, DATE, "params", str(params)), xbmc.LOGDEBUG)

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
