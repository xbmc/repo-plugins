#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from future import standard_library
standard_library.install_aliases()
from builtins import str
import os
import re
import urllib.request, urllib.parse, urllib.error
import requests
from time import strptime
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmc
import sys
from bs4 import BeautifulSoup
from urllib.parse import parse_qs

ADDON = "plugin.video.cnet.podcasts"
SETTINGS = xbmcaddon.Addon()
LANGUAGE = SETTINGS.getLocalizedString
IMAGES_PATH = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources')
HEADERS = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0','Referer': 'http://www.cnet.com'}
BASE_URL = 'http://www.cnet.com/cnet-podcasts/'
DATE = "2018-01-20"
VERSION = "1.1.6"


def cache_categories():
    response = requests.get(BASE_URL, headers=HEADERS)

    html_source = response.text
    html_source = convertToUnicodeString(html_source)

    # Parse response
    soup = getSoup(html_source)

    items = soup.find_all('a', attrs={'href': re.compile("hd.xml$")})
    cats = [{'thumb': '',
             'name': i['href'],
             'desc': '',
             'links': i['href']} for
            i in items]
    return cats


def display_categories():
    cats = cache_categories()
    previous_name = ''

    for i in cats:

        log("cat", i)

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
            if SETTINGS.getSetting('onlyshowallcategory') == 'true':
                if 'All' in str(name):
                    display_category(str(i['name']))
                    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
                    xbmcplugin.endOfDirectory(int(sys.argv[1]))
                    break
            else:
                add_dir(name, i['links'], 'category', i['thumb'], {'Plot': i['desc']})


def display_category(links_list):
    url = links_list

    log("url", url)

    response = requests.get(url, headers=HEADERS)

    html_source = response.text
    html_source = convertToUnicodeString(html_source)

    # Parse response
    soup = getSoup(html_source)

    # log("soup", soup)

    items = soup.find_all('item')

    log("len(items)", len(items))

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

        log("item", item)

        # <enclosure url="http://dw.cbsi.com/redir/AB445_1164934_2696.mp4?destUrl=http://download.cnettv.com.edgesuite.net/21923/mpx/2017/07/12/994592835973/AB445_1164934_2696.mp4" length="0" type="video/mp4"/>
        # get the url of the video
        url = item.enclosure["url"]

        log("url", url)

        # Get title
        title = item.title.string
        title = title.replace("<![CDATA[", '')
        title = title.replace("]]>", '')

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

        log("title", title)

        context_menu_items = []
        # Add refresh option to context menu
        context_menu_items.append((LANGUAGE(30104), 'Container.Refresh'))
        # Add episode  info to context menu
        context_menu_items.append((LANGUAGE(30105), 'XBMC.Action(Info)'))

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

        log("extracted pubdate", day + '/' + month_name + '/' + year + '/' + hour + '/' + minute + '/' + second)

        month_numeric = strptime(month_name, '%b').tm_mon

        log("month_numeric", month_numeric)

        if len(str(month_numeric)) == 1:
            month = '0' + str(month_numeric)
        else:
            month = str(month_numeric)

        # Dateadded has this form: 2009-04-05 23:16:04
        dateadded = year + '-' + month + '-' + day + ' ' + hour + ':' + minute + ':' + second

        log("dateadded", dateadded)

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
    url = '%s?%s' % (sys.argv[0], urllib.parse.urlencode(parameters))
    list_item = xbmcgui.ListItem(name)
    list_item.setArt({'thumb': iconimage, 'icon': iconimage,
                      'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
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
    for i in list(p.keys()):
        p[i] = p[i][0]
    return p


if sys.version_info[0] > 2:
    unicode = str


def convertToUnicodeString(s, encoding='utf-8'):
    """Safe decode byte strings to Unicode"""
    if isinstance(s, bytes):  # This works in Python 2.7 and 3+
        s = s.decode(encoding)
    return s


def convertToByteString(s, encoding='utf-8'):
    """Safe encode Unicode strings to bytes"""
    if isinstance(s, unicode):
        s = s.encode(encoding)
    return s


def log(name_object, object):
    try:
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, name_object, convertToUnicodeString(object)), xbmc.LOGDEBUG)
    except:
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, name_object, "Unable to log the object due to an error while converting it to an unicode string"), xbmc.LOGDEBUG)


def getSoup(html,default_parser="html5lib"):
    soup = BeautifulSoup(html, default_parser)
    return soup


params = get_params()

try:
    mode = params['mode']
except:
    mode = None

    log("ARGV", repr(sys.argv))

log("params", params)

if not mode:
    display_categories()
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 'category':
    display_category(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 'resolve':
    item = xbmcgui.ListItem(path=params['url'])
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)