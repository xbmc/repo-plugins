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
import requests
import json

ADDON = "plugin.video.101barz"
SETTINGS = xbmcaddon.Addon(id=ADDON)
LANGUAGE = SETTINGS.getLocalizedString
IMAGES_PATH = os.path.join(xbmcaddon.Addon(id=ADDON).getAddonInfo('path'), 'resources', 'images')
PLUGIN_HANDLE = int(sys.argv[1])
BASE_URL = "https://101barz.bnnvara.nl/api/video?"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10115) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
COOKIES = {}
DATE = "2019-02-12"
VERSION = "1.0.0"

SEARCHURL = "category=<categorystring>&search=<searchstring>&offset=0&limit=12"
ALLESURL = "category=all&search=&offset=0&limit=12"
STUDIOSESSIONSURL = "category=13&search=&offset=0&limit=12"
VIDEOCLIPZURL = "category=14&search=&offset=0&limit=12"
ROTJOCHLOUNGEURL = "category=25&search=&offset=0&limit=12"
HITMAKERZURL = "category=27&search=&offset=0&limit=12"
BARZ4BARZURL = "category=28&search=&offset=0&limit=12"
TALENTVDMAANDURL = "category=29&search=&offset=0&limit=12"


def index():
    add_dir(LANGUAGE(30002), ALLESURL, 'list_videos', "")
    add_dir(LANGUAGE(30003), STUDIOSESSIONSURL, 'list_videos', "")
    add_dir(LANGUAGE(30004), VIDEOCLIPZURL, 'list_videos', "")
    add_dir(LANGUAGE(30005), ROTJOCHLOUNGEURL, 'list_videos', "")
    add_dir(LANGUAGE(30006), HITMAKERZURL, 'list_videos', "")
    add_dir(LANGUAGE(30007), BARZ4BARZURL, 'list_videos', "")
    add_dir(LANGUAGE(30008), TALENTVDMAANDURL, 'list_videos', "")

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)


def list_videos(url):
    # add category number to search url
    CATEGORY = "category="
    start_pos = convertToUnicodeString(url).find(CATEGORY)
    if start_pos >= 0:
        end_pos = convertToUnicodeString(url).find("&", start_pos)
        category_value = convertToUnicodeString(url)[start_pos + len(CATEGORY):end_pos]
        search_url = convertToUnicodeString(SEARCHURL).replace("<categorystring>", category_value)

        # add search url
        add_dir(LANGUAGE(30001), search_url, 'search', "")

    html_source = get_url(url)
    json_data = json.loads(html_source)

    for item in json_data['video']:

        log("item", item)

        length = ""
        title = item['title']
        desc = item['subtitle']
        date = item['publish_up']
        thumbnail_image_url = item['card_image']
        youtube_id = item['youtube_id']
        youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id

        add_link(title, youtube_url, 'play_video', thumbnail_image_url, date + "\n" + desc, length)

    # add next page url
    url_next = url
    OFFSET = "offset="
    start_pos = convertToUnicodeString(url_next).find(OFFSET)
    if start_pos >= 0:
        end_pos = convertToUnicodeString(url_next).find("&", start_pos)
        old_offset_value = convertToUnicodeString(url_next)[start_pos + len(OFFSET):end_pos]
        old_offset_value = int(old_offset_value)
        new_offset_value = old_offset_value + 12
        old_offset_value = str(old_offset_value)
        new_offset_value = str(new_offset_value)
        url_next = convertToUnicodeString(url_next).replace(OFFSET + convertToUnicodeString(old_offset_value), OFFSET +
                                                            convertToUnicodeString(new_offset_value))

        add_dir(LANGUAGE(30009), url_next, 'list_videos', os.path.join(IMAGES_PATH, 'next-page.png'))

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)


def search(url):
    # decode the url
    url = urllib.parse.unquote_plus(url)

    keyboard = xbmc.Keyboard('', LANGUAGE(30008))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        search_url = BASE_URL + convertToUnicodeString(url).replace("<searchstring>", search_string)
        list_videos(search_url)


def play_video(video_url):
    list_item = xbmcgui.ListItem(path=video_url)
    return xbmcplugin.setResolvedUrl(PLUGIN_HANDLE, True, list_item)


def show_dialog(title, text):
    dialog = xbmcgui.Dialog()
    dialog.ok(title, text)


def get_url(url):
    if convertToUnicodeString(url).find(BASE_URL) >= 0:
        complete_url = url
    else:
        complete_url = BASE_URL + url

    log("complete_url", complete_url)

    response = requests.get(complete_url, headers=HEADERS, cookies=COOKIES)
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
    u = sys.argv[0] + "?url=" + urllib.parse.quote_plus(url) + "&mode=" + convertToUnicodeString(mode)
    liz = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_image_url)
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
    u = sys.argv[0] + '?url=' + urllib.parse.quote_plus(url) + '&mode=' + convertToUnicodeString(mode)
    liz = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_image_url)
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


params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('url')

if url is None:
    if SETTINGS.getSettingBool('onlyshowallvideoscategory'):
        mode = 'list_videos'
        url = urllib.parse.quote_plus(BASE_URL + ALLESURL)

if mode == 'list_videos':
    url = urllib.parse.unquote_plus(url)
    list_videos(url)
elif mode == 'play_video':
    url = urllib.parse.unquote_plus(url)
    play_video(url)
elif mode == 'search':
    search(url)
else:
    xbmc.log("[ADDON] %s debug mode, Python Version %s" % (ADDON, convertToUnicodeString(sys.version)), xbmc.LOGDEBUG)
    xbmc.log("[ADDON] %s v%s (%s) debug mode, is starting, ARGV = %s" % (ADDON, VERSION, DATE, repr(sys.argv)), xbmc.LOGDEBUG)
    index()