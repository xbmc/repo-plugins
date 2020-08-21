#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import str
import urllib.request, urllib.parse, urllib.error
import xbmcplugin
import xbmcgui
import sys
import xbmcaddon
import xbmc
import os
import re
import requests
import json
from bs4 import BeautifulSoup

ADDON = "plugin.video.101barz"
SETTINGS = xbmcaddon.Addon(id=ADDON)
LANGUAGE = SETTINGS.getLocalizedString
IMAGES_PATH = os.path.join(xbmcaddon.Addon(id=ADDON).getAddonInfo('path'), 'resources', 'images')
PLUGIN_HANDLE = int(sys.argv[1])
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10115) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
COOKIES = {}
DATE = "2020-08-20"
VERSION = "1.1.1"

APIURL = "https://api.bnnvara.nl/bff/graphql"
HEADERSJSON = {'content-type': 'application/json'}
BASEURL  = "https://www.bnnvara.nl"
VIDEOURL = "https://www.bnnvara.nl/101barz/tags/video?limit=" + str(SETTINGS.getSetting('numberofvideosshown'))


def list_videos(video_page_url):

    log("video_page_url", video_page_url)

    # add search video_page_url
    add_dir(LANGUAGE(30001), APIURL, 'search', "")

    html_source = get_url(video_page_url)

    # log(html_source, html_source)

    # Parse response
    soup = getSoup(html_source)

    #<a href="/101barz/artikelen/wintersessie-josbros-2" class="tjcu1e-1 jDMFxC"><div class="sc-114vwi2-0 hkkNSo"><div class="j1n9w9-0 bczuOc"><img src="https://d2hpleul9br1of.cloudfront.net/w_500,h_500/s3-101barz/e3aad92c-8281-4b83-8d92-a5c3244d4ac6.jpg" alt="Afbeelding van Wintersessie: Josbros" class="j1n9w9-1 HiXpC"></div><div class="kyune6-1 bHNiuC"><svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" aria-label="artikel" class="sc-7guewg-0 jlynrr"><path fill="#FFF" fill-rule="evenodd" d="M3,4 L19,4 L19,7 L3,7 L3,4 Z M3,10 L21,10 L21,13 L3,13 L3,10 Z M3,16 L17,16 L17,19 L3,19 L3,16 Z"></path></svg></div><div class="j1n9w9-2 dzFFRu"><div class="sc-1ablp01-0 hHPbhp"><h2>Wintersessie: Josbros</h2></div><div class="sc-13rhqs6-0 hokqIi">Gisteren</div></div></div></a>
    items = soup.findAll('a', attrs={'href': re.compile("^" + "/101barz/")})

    log("len(items)", len(items))

    for item in items:

        log("item", item)

        # skips items that have the role "link"
        if str(item).find('role="link"') >= 0:

            log("skipping link item", item)

            continue

        title_and_date = item.select('div')[0].get_text(strip=True)

        # determine the length of the date field. date field is f.e. "2 jan 2020" or "21 jan 2020"
        testdate = convertToUnicodeString(title_and_date[(len(title_and_date)-11):])
        if testdate[0:2].isnumeric():
            if testdate[0:1] == "1":
                date_length = 11
            elif testdate[0:1] == "2":
                date_length = 11
            else:
                date_length = 10
        else:
            date_length = 10

        date = title_and_date[(len(title_and_date)-date_length):]
        title = title_and_date[0:(len(title_and_date)-date_length)]

        thumbnail_image_url = item.img['src']

        video_page_url = item['href']
        video_page_url = BASEURL + video_page_url

        log("title_and_date", title_and_date)
        log("date", date)
        log("title", title)
        log("thumbnail_image_url", thumbnail_image_url)
        log("video_page_url", video_page_url)

        desc = ""
        length = ""

        add_link(title, video_page_url, 'play_video', thumbnail_image_url, date + "\n" + desc, length)

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)


def search():
    keyboard = xbmc.Keyboard('', LANGUAGE(30008))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        html_source = post_url(APIURL, 0, 500, search_string)
        list_videos_json(html_source)


def post_url(url, start_index, size, query):
    start_index = int(start_index)
    size = int(size)

    body = {"operationName":"SearchQuery","variables":{"from":start_index,"size":size,"query":query},"query":"query SearchQuery($query: String!, $from: Int = 0, $size: Int = 10) {\n  search(keyword: $query, from: $from, size: $size) {\n    hits\n    results {\n      type\n      mediaType\n      title\n      uri\n      brand {\n        name\n        __typename\n      }\n      image {\n        title\n        url\n        __typename\n      }\n      publishDate\n      __typename\n    }\n    __typename\n  }\n}\n"}

    response = requests.post(url, data=json.dumps(body), headers=HEADERSJSON)
    json_source = response.text
    json_source = convertToUnicodeString(json_source)

    # log("json_source", json_source)

    return json_source


def list_videos_json(json_source):
    json_data = json.loads(json_source)

    # log("json_data", json_data)

    #{"data":
    #   {"search":
    #       {"hits":103,
    #       "results":
    #           {"type":"Article","mediaType":null,"title":"#TBT: Heinek'n","uri":"/101barz/artikelen/tbt-heinekn",
    #           "brand":{"name":"101Barz","__typename":"Brand"},
    #           "image":{"title":"Heinie WS","url":"https://d2hpleul9br1of.cloudfront.net/
    #           {format}/s3-101barz/09f92cab-6557-45c6-9323-545529a1fdd1.jpg","__typename":"PlayerImage"},
    #           "publishDate":"2020-01-16T13:00:00.000Z","__typename":"SearchResultItem"},
    #
    #          {"type":"Video","mediaType":"Clip","title":"#TBT: Matthijs danst als Michael Jackson",
    for item in json_data['data']['search']['results']:

        log("item", item)

        title = item['title']

        video_page_url = item['uri']
        video_page_url = BASEURL + video_page_url

        thumbnail_image_url = item['image']['url']
        # set the format of the thumbnail
        thumbnail_image_url = convertToUnicodeString(thumbnail_image_url).replace("{format}","w_500,h_500")

        date = item['publishDate']

        log("date", date)
        log("title", title)
        log("thumbnail_image_url", thumbnail_image_url)
        log("video_page_url", video_page_url)

        desc = ""
        length = ""

        add_link(title, video_page_url, 'play_video', thumbnail_image_url, date + "\n" + desc, length)

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)


def play_video(video_page_url):
    html_source = get_url(video_page_url)

    # YoutubeEmbed","url":"https://www.youtube.com/embed/R1W-BLz7AXY"},"Article:b6ac6bca
    search_term = "https://www.youtube.com/embed/"
    html_source_unicode_string = convertToUnicodeString(html_source)
    start_pos_search_term = html_source_unicode_string.find(search_term)
    youtube_id = ""
    if start_pos_search_term >= 0:
        end_pos = html_source_unicode_string.find('"', start_pos_search_term)
        youtube_id = html_source_unicode_string[start_pos_search_term + len(search_term):end_pos]
        youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id

        log("youtube_url", youtube_url)

    if youtube_id == "":
        show_dialog(LANGUAGE(30611),LANGUAGE(30612))
    else:
        list_item = xbmcgui.ListItem(path=youtube_url)
        return xbmcplugin.setResolvedUrl(PLUGIN_HANDLE, True, list_item)


def show_dialog(title, text):
    dialog = xbmcgui.Dialog()
    dialog.ok(title, text)


def get_url(video_page_url):
    log("video_page_url", video_page_url)

    response = requests.get(video_page_url, headers=HEADERS, cookies=COOKIES)
    html_source = response.text
    html_source = convertToUnicodeString(html_source)

    #log("html_source", html_source)

    return html_source


def parameters_string_to_dict(parameters):
    """ Convert parameters encoded in a URL to a dict. """
    param_dict = {}
    if parameters:
        param_pairs = parameters[1:].split("&")
        for paramsPair in param_pairs:
            param_splits = paramsPair.split('=')
            if (len(param_splits)) == 2:
                param_dict[param_splits[0]] = param_splits[1]
    return param_dict


def add_link(title, url, mode, thumbnail_image_url, desc="", duration=""):
    u = sys.argv[0] + "?video_page_url=" + urllib.parse.quote_plus(url) + "&mode=" + convertToUnicodeString(mode)
    liz = xbmcgui.ListItem(label=title)
    liz.setArt({'thumb': thumbnail_image_url, 'icon': thumbnail_image_url})
    liz.setInfo(type="Video", infoLabels={"Title": title, "Plot": desc, "Duration": duration})
    liz.setProperty('IsPlayable', 'true')
    # let's remove any non-ascii characters from the title, to prevent errors with urllib.parse.parse_qs
    # of the parameters
    title = title.encode('ascii', 'ignore')
    # Add refresh option to context menu
    liz.addContextMenuItems([('Refresh', 'Container.Refresh')])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def add_dir(title, url, mode, thumbnail_image_url, desc=""):
    u = sys.argv[0] + '?video_page_url=' + urllib.parse.quote_plus(url) + '&mode=' + convertToUnicodeString(mode)
    liz = xbmcgui.ListItem(label=title)
    liz.setArt({'thumb': thumbnail_image_url, 'icon': thumbnail_image_url})
    liz.setInfo(type='video', infoLabels={'title': title, 'plot': desc, 'plotoutline': desc})
    # let's remove any non-ascii characters from the title, to prevent errors with urllib.parse.parse_qs
    # of the parameters
    title = title.encode('ascii', 'ignore')
    # Add refresh option to context menu
    liz.addContextMenuItems([('Refresh', 'Container.Refresh')])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


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
        # Let's try and remove any non-ascii stuff first
        object = object.encode('ascii', 'ignore')
    except:
        pass

    try:
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, name_object, convertToUnicodeString(object)), xbmc.LOGDEBUG)
    except:
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, name_object, "Unable to log the object due to an error while converting it to an unicode string"), xbmc.LOGDEBUG)


def getSoup(html, default_parser="html5lib"):
    soup = BeautifulSoup(html, default_parser)
    return soup


params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('video_page_url')

if url is None:
    mode = 'list_videos'
    url = urllib.parse.quote_plus(VIDEOURL)

if mode == 'search':
    search()
elif mode == 'list_videos':
    url = urllib.parse.unquote_plus(url)
    list_videos(url)
elif mode == 'play_video':
    url = urllib.parse.unquote_plus(url)
    play_video(url)
else:
    xbmc.log("[ADDON] %s debug mode, Python Version %s" % (ADDON, convertToUnicodeString(sys.version)), xbmc.LOGDEBUG)
    xbmc.log("[ADDON] %s v%s (%s) debug mode, is starting, ARGV = %s" % (ADDON, VERSION, DATE, repr(sys.argv)), xbmc.LOGDEBUG)