#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
from builtins import object
import urllib.request, urllib.parse, urllib.error
import re
import xbmcplugin
import xbmcgui
import sys
import xbmcaddon
import xbmc
import os
import requests

ADDON = "plugin.video.ign_com"
SETTINGS = xbmcaddon.Addon(id=ADDON)
LANGUAGE = SETTINGS.getLocalizedString
IMAGES_PATH = os.path.join(xbmcaddon.Addon(id=ADDON).getAddonInfo('path'), 'resources', 'images')
PLUGIN_HANDLE = int(sys.argv[1])
BASE_URL = "https://www.ign.com"
LATEST_VIDEOS_URL = "/videos?page=1&filter=all"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
COOKIES = {}
DATE = "2019-01-14"
VERSION = "2.3.9"

max_video_quality = SETTINGS.getSetting("maxVideoQualityRes")
force_view_mode = bool(SETTINGS.getSetting("force_view_mode"))
live_stream_setting = bool(SETTINGS.getSetting("LiveStream"))
viewMode = str(SETTINGS.getSetting("viewMode"))

video_height = [360, 480, 540, 720, 1080]
max_video_height = video_height[int(max_video_quality)]
max_video_bitrate = [347000, 724000, 1129000, 1910000, 3906000]
max_video_quality = [640, 853, 960, 1280, 1920]


def index():
    if live_stream_setting:
        html_source = get_url("")
        match = re.compile('"m3uUrl":"(.+?).m3u8"}', re.DOTALL).findall(html_source)
        if len(match) > 0:
            video_url = match[0].replace("\\", "")
            title = re.compile('data-video-title="(.+?)"', re.DOTALL).findall(html_source)
            add_link("***IGN-LIVESTREAM: " + title[0] + "***", video_url + ".m3u8", 'play_live_stream', "", "", "LIVE")

    add_dir(LANGUAGE(30002), "/videos/all/filtergalleryajax?filter=all", 'list_videos', "")
    add_dir("IGN Daily Fix", "/watch/daily-fix?category=videos&page=1", 'list_series_episodes', "")
    add_dir(LANGUAGE(30003), "/videos/all/filtergalleryajax?filter=games-review", 'list_videos', "")
    add_dir(LANGUAGE(30004), "/videos/all/filtergalleryajax?filter=games-trailer", 'list_videos', "")
    add_dir(LANGUAGE(30005), "/videos/all/filtergalleryajax?filter=movies-trailer", 'list_videos', "")
    add_dir(LANGUAGE(30006), "/videos/all/filtergalleryajax?filter=series", 'list_videos', "")
    add_dir(LANGUAGE(30008), "", 'search', "")

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)
    if force_view_mode:
        xbmc.executebuiltin('Container.SetViewMode(' + viewMode + ')')


def list_videos(url):
    html_source = get_url(url)
    spl = html_source.split('<div class="grid_16 alpha bottom_2">')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<li>(.+?)</li>', re.DOTALL).findall(entry)
        if len(match) > 0:
            length = match[0].replace(" mins", "")
            l = length.split(':')
            length = int(l[0]) * 60 + int(l[1])
            match = re.compile(
                '<p class="video-description">\n\s*<span class="publish-date">(.+?)</span> -(.+?)</p>',
                re.DOTALL).findall(entry)
            date = match[0][0]
            desc = match[0][1]
            desc = clean_title(desc)
            match = re.compile('title="(.+?)"', re.DOTALL).findall(entry)
            title = match[0]
            title = clean_title(title)
            match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url = match[0]
            match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb = ""
            if match:
                thumb = match[0].replace("_small.jpg", ".jpg")
            add_link(title, url, 'play_video', thumb, date + "\n" + desc, length)

    match_page = re.compile('<a id="moreVideos" href="(.+?)"', re.DOTALL).findall(html_source)
    # page_count = re.compile('<a id="moreVideos" href=".+?page=(.+?)\&.+?"', re.DOTALL).findall(html_source)
    if len(match_page) > 0:
        url_next = match_page[0]
        add_dir(LANGUAGE(30001), url_next, 'list_videos', os.path.join(IMAGES_PATH, 'next-page.png'))

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)
    if force_view_mode:
        xbmc.executebuiltin('Container.SetViewMode(' + viewMode + ')')


def list_series_episodes(url):
    html_source = get_url(url)
    match = re.compile(
        '<a.+?class="video-link".+?href="(.+?)".+?data-title="(.+?)".+?>.+?<img src="(.+?)" />.+?'
        '<div class="video-title">(.+?)</div>.+?<div class="video-duration">(.+?)</div>.+?<div class="ago">(.+?)</div>',
        re.DOTALL).findall(html_source)
    for i in range(0, len(match), 1):
        vidurl = BASE_URL + match[i][0]
        description = match[i][1]
        thumb = match[i][2]
        title = match[i][3]
        dur_split = match[i][4].split(':')
        duration = int(dur_split[0]) * 60 + int(dur_split[1])
        date = match[i][5]
        add_link(title, vidurl, 'play_video', thumb, date + "\n" + description, duration)

    match_page = re.compile('<a class="next" href="://(.+?)">Next&nbsp;&raquo;</a>', re.DOTALL).findall(html_source)
    page_count = re.compile('<a class="next" href="://.+?page=(.+?)">Next&nbsp;&raquo;</a>', re.DOTALL).findall(html_source)
    if len(page_count) > 0:
        add_dir(LANGUAGE(30001),
                match_page[0] + "&category=videos", 'list_series_episodes', os.path.join(IMAGES_PATH, 'next-page.png'))

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)
    if force_view_mode:
        xbmc.executebuiltin('Container.SetViewMode(' + viewMode + ')')


def list_series(url):
    html_source = get_url(url)
    spl = html_source.split('<div class="grid_16 alpha bottom_2">')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<li>(.+?)</li>', re.DOTALL).findall(entry)
        date = match[0]
        match = re.compile('<p class="video-description">(.+?)</p>', re.DOTALL).findall(entry)
        title = match[0]
        title = clean_title(title)
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = match[0]
        thumb = ""
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        if len(match) > 0:
            thumb = match[0].replace("_small.jpg", ".jpg")
        add_dir(title, url, 'list_videos', thumb, date)

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)
    if force_view_mode:
        xbmc.executebuiltin('Container.SetViewMode(' + viewMode + ')')


def search():
    keyboard = xbmc.Keyboard('', LANGUAGE(30008))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        list_search_results('/search?q=' + search_string + '&page=0&count=10&type=video')


def list_search_results(url):
    url_main = url
    html_source = get_url(url)
    spl = html_source.split('<div class="search-item"')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = ""
        if match:
            thumb = clean_url(match[0]).replace("_small.jpg", ".jpg")
        entry = entry[entry.find('<div class="search-item-title">'):]
        match = re.compile('<span class="duration">(.+?)<span>', re.DOTALL).findall(entry)
        length = ""
        if len(match) > 0:
            length = clean_title(match[0])
        match = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
        url = match[0][0]
        title = match[0][1]
        title = clean_title(title)
        add_link(title, url, 'play_video', thumb, "", length)
    match = re.compile('data-page="(.+?)"', re.DOTALL).findall(html_source)
    page = int(match[0])
    match = re.compile('data-total="(.+?)"', re.DOTALL).findall(html_source)
    max_page = int(int(match[0])/ 10)
    url_next = url_main.replace("page=" + str(page), "page=" + str(page + 1))
    if page < max_page:
        add_dir(LANGUAGE(30001), url_next, 'list_search_results', os.path.join(IMAGES_PATH, 'next-page.png'))

    xbmcplugin.endOfDirectory(PLUGIN_HANDLE)
    if force_view_mode:
        xbmc.executebuiltin('Container.SetViewMode(' + viewMode + ')')


def play_video(page_url):

    log("page_url", page_url)

    match = re.compile(BASE_URL + "(.+)", re.DOTALL).findall(page_url)
    vid = Video(match[0])
    final_url = vid.get_vid_url(max_video_height)

    log("final_url", final_url)

    list_item = xbmcgui.ListItem(path=final_url)
    return xbmcplugin.setResolvedUrl(PLUGIN_HANDLE, True, list_item)


class Video(object):
    def __init__(self, vid_url):
        self.url = vid_url
        self.video_type = ""
        self.urls = {}

    def _detect(self):
        html_source = get_url(self.url)
        self._get_video_links(html_source)

    def _get_video_links(self, html_source):
        # ion"},{"type":"id","generated":true,"id":"$ROOT_QUERY.video({\"slug\":\"artifact-review\"}).recommendations.26","typename":"Recommendation"},{"type":"id","generated":true,"id":"$ROOT_QUERY.video({\"slug\":\"artifact-review\"}).recommendations.27","typename":"Recommendation"},{"type":"id","generated":true,"id":"$ROOT_QUERY.video({\"slug\":\"artifact-review\"}).recommendations.28","typename":"Recommendation"},{"type":"id","generated":true,"id":"$ROOT_QUERY.video({\"slug\":\"artifact-review\"}).recommendations.29","typename":"Recommendation"}],"__typename":"Video"},"$ROOT_QUERY.video({\"slug\":\"artifact-review\"}).assets.0":{"url":"https://assets14.ign.com/videos/zencoder/2018/12/12/640/6446a6b64d3bdf7bcdc904c0c65239b3-500000-1544662394.mp4","width":640,"height":360,"fps":60,"__typename":"VideoAsset"},"$ROOT_QUERY.video({\"slug\":\"artifact-review\"}).assets.1":{"url":"https://assets14.ign.com/videos/zencoder/2018/12/12/960/6446a6b64d3bdf7bcdc904c0c65239b3-3000000-1544662394.mp4","width":960,"height":540,"fps":60,"__typename":"VideoAsset"},"$ROOT_QUERY.video({\"slug\":\"artifact-review\"}).assets.2":{"url":"https://assets14.ign.com/videos/zencoder/2018/12/12/1280/6446a6b64d3bdf7bcdc904c0c65239b3-7500000-1544662394.mp4","width":1280,"height":720,"fps":60,"__typename":"VideoAsset"},"$ROOT_QUERY.video({\"slug\":\"artifact-review\"}).assets.3":{"url":"https://assets14.ign.com/videos/zencoder/2018/12/12/1920/6446a6b64d3bdf7bcdc904c0c65239b3-9000000-1544662394.mp4","width":1920,"height":1080,"fps":60,"__typename":"VideoAsset"},"$ROOT_QUERY.video({\"slug\":\"artifact-review\"}).relatedObjects.0":{"name":"Artifact","slug":"artifact","type":"Game","__typename":"VideoRelatedObject"},"$ROOT_QUERY.video({\"slug\":\"artifact-review\"}).recommendations.0":{"duration":230,"title":"Why We Think Valve Hasn't Made Half-Life 3 Yet","url":"https://www.ign.com/videos/2018/03/10/why-we-think-valve-hasnt-made-half-life-3-yet","videoId":"8b84c80d625cd3c5a163cd0358a67f05",
        temp_matches = re.compile('{"url":"(.+?)/zencoder/(.+?)/(.+?)/(.+?)/(.+?)/(.+?)-(.+?)-(.+?)"', re.DOTALL)\
            .findall(html_source)

        temp_match_index = 0;
        for temp_match in temp_matches:

            log("temp_match", temp_match)

            start_url = temp_match[0]
            year = temp_match[1]
            month = temp_match[2]
            day = temp_match[3]
            resolution = temp_match[4]
            video_id_part_1 = temp_match[5]
            bitrate = temp_match[6]
            video_id_part_2 = temp_match[7]
            temp_url = start_url + "/zencoder/" + year + "/" + month + "/" + day + "/" + resolution + "/" + video_id_part_1 + "-" + bitrate + "-" + video_id_part_2
            try:

                log("temp_url trying", temp_url)

                ret = urllib.request.urlopen(temp_url)
                if ret.code == 200:

                    log("temp_url added", temp_url)

                    self.urls[video_height[temp_match_index]] = temp_url
            except urllib.error.HTTPError as e:
                xbmc.log('HTTPError: ' + temp_url)
            except urllib.error.URLError as e:
                xbmc.log('URLError: ' + temp_url)

            temp_match_index = temp_match_index + 1
            # We only need 5 temp_matches, after that it starts repeating itself
            if temp_match_index > 4:
                break

    def get_vid_url(self, wanted_resolution):
        self._detect()
        final_url = ""
        for available_resolution in list(self.urls.keys()):
            if int(available_resolution) <= wanted_resolution:
                final_url = self.urls[available_resolution]
        return final_url


def show_dialog(title, text):
    dialog = xbmcgui.Dialog()
    dialog.ok(title, text)


def play_live_stream(url):
    listitem = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(PLUGIN_HANDLE, True, listitem)


def clean_title(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "'").replace(
        "&quot;", "\"").replace("&ndash;", "-")
    title = title.replace("<em>", "").replace("</em>", "").strip()
    return title


def clean_url(title):
    title = title.replace("&#x3A;", ":").replace("&#x2F;", "/")
    return title


def get_url(url):
    if url.find(BASE_URL) >= 0:
        complete_url = url
    else:
        complete_url = BASE_URL + url

    log("complete_url", complete_url)

    response = requests.get(complete_url, headers=HEADERS, cookies=COOKIES)
    html_source = response.text
    html_source = convertToUnicodeString(html_source)

    # log("html_source", html_source)

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


def add_link(title, url, mode, iconimage, desc="", duration=""):
    u = sys.argv[0] + "?url=" + urllib.parse.quote_plus(url) + "&mode=" + str(mode)
    liz = xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": title, "Plot": desc, "Duration": duration})
    liz.setProperty('IsPlayable', 'true')
    # let's remove any non-ascii characters from the title, to prevent errors with urllib.parse.parse_qs
    # of the parameters
    title = title.encode('ascii', 'ignore')
    # Add refresh option to context menu
    liz.addContextMenuItems([('Refresh', 'Container.Refresh')])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def add_dir(title, url, mode, iconimage, desc=""):
    u = sys.argv[0] + '?url=' + urllib.parse.quote_plus(url) + '&mode=' + str(mode)
    liz = xbmcgui.ListItem(title, iconImage='DefaultFolder.png', thumbnailImage=iconimage)
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
    if SETTINGS.getSetting('onlyshownewvideocategory') == 'true':
        mode = 'list_videos'
        url = urllib.parse.quote_plus(BASE_URL + LATEST_VIDEOS_URL)

if mode == 'list_videos':
    url = urllib.parse.unquote_plus(url)
    list_videos(url)
elif mode == 'list_series':
    url = urllib.parse.unquote_plus(url)
    list_videos(url)
elif mode == 'list_search_results':
    url = urllib.parse.unquote_plus(url)
    list_search_results(url)
elif mode == 'play_video':
    url = urllib.parse.unquote_plus(url)
    play_video(url)
elif mode == 'list_series_episodes':
    url = urllib.parse.unquote_plus(url)
    list_series_episodes(url)
elif mode == 'play_live_stream':
    url = urllib.parse.unquote_plus(url)
    play_live_stream(url)
elif mode == 'search':
    search()
else:
    xbmc.log("[ADDON] %s debug mode, Python Version %s" % (ADDON, convertToUnicodeString(sys.version)), xbmc.LOGDEBUG)
    xbmc.log("[ADDON] %s v%s (%s) debug mode, is starting, ARGV = %s" % (ADDON, VERSION, DATE, repr(sys.argv)), xbmc.LOGDEBUG)
    index()