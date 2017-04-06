#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import re
import xbmcplugin
import xbmcgui
import sys
import xbmcaddon
import socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon(id='plugin.video.ign_com')
translation = addon.getLocalizedString
base_url = "http://www.ign.com"

max_video_quality = addon.getSetting("maxVideoQualityRes")

force_view_mode = bool(addon.getSetting("force_view_mode"))
live_stream_setting = bool(addon.getSetting("LiveStream"))

viewMode = str(addon.getSetting("viewMode"))

video_height = [360, 480, 540, 720, 1080]
max_video_height = video_height[int(max_video_quality)]
max_video_bitrate = [347000, 724000, 1129000, 1910000, 3906000]
max_video_quality = [640, 853, 960, 1280, 1920]

def index():
    if live_stream_setting:
        content = get_url("")
        match = re.compile('"m3uUrl":"(.+?).m3u8"}', re.DOTALL).findall(content)
        if len(match) > 0:
            video_url = match[0].replace("\\", "")
            title = re.compile('data-video-title="(.+?)"', re.DOTALL).findall(content)
            add_link("***IGN-LIVESTREAM: " + title[0] + "***", video_url + ".m3u8", 'play_live_stream', "", "", "LIVE")
    add_dir(translation(30002), "/videos/all/filtergalleryajax?filter=all", 'list_videos', "")
    add_dir("IGN Daily Fix", "/watch/daily-fix?category=videos&page=1", 'list_series_episodes', "")
    add_dir(translation(30003), "/videos/all/filtergalleryajax?filter=games-review", 'list_videos',
            "")
    add_dir(translation(30004), "/videos/all/filtergalleryajax?filter=games-trailer", 'list_videos',
            "")
    add_dir(translation(30005), "/videos/all/filtergalleryajax?filter=movies-trailer", 'list_videos',
            "")
    add_dir("Podcasts", "", 'podcast_index', "")

    add_dir(translation(30008), "", 'search', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if force_view_mode:
        xbmc.executebuiltin('Container.SetViewMode(' + viewMode + ')')


def podcast_index():
    content = get_url("/")
    match = re.compile(
        '<li class="ign-shows-list-container ign-transition">(.+?)</li>\s*<li class="ign-show ign-transition">',
        re.DOTALL).findall(content)
    podcasts = re.compile('<li><a href="(.+?)">(.+?)</a></li>', re.DOTALL).findall(match[0])
    for pod in podcasts:
        add_dir(pod[1], pod[0] + "?category=videos&page=1", 'list_series_episodes', "", pod[1])
    xbmcplugin.endOfDirectory(pluginhandle)
    if force_view_mode:
        xbmc.executebuiltin('Container.SetViewMode(' + viewMode + ')')


def list_videos(url):
    content = get_url(url)
    spl = content.split('<div class="grid_16 alpha bottom_2">')
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
    match_page = re.compile('<a id="moreVideos" href="(.+?)"', re.DOTALL).findall(content)
    page_count = re.compile('<a id="moreVideos" href=".+?page=(.+?)\&.+?"', re.DOTALL).findall(content)
    if len(match_page) > 0:
        url_next = match_page[0]
        add_dir(translation(30001) + " (" + str(page_count[0]) + ")", url_next, 'list_videos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if force_view_mode:
        xbmc.executebuiltin('Container.SetViewMode(' + viewMode + ')')


def list_series_episodes(url):
    content = get_url(url)
    match = re.compile(
        '<a.+?class="video-link".+?href="(.+?)".+?data-title="(.+?)".+?>.+?<img src="(.+?)" />.+?'
        '<div class="video-title">(.+?)</div>.+?<div class="video-duration">(.+?)</div>.+?<div class="ago">(.+?)</div>',
        re.DOTALL).findall(content)
    for i in range(0, len(match), 1):
        vidurl = "http://www.ign.com/" + match[i][0]
        description = match[i][1]
        thumb = match[i][2]
        title = match[i][3]
        dur_split = match[i][4].split(':')
        duration = int(dur_split[0]) * 60 + int(dur_split[1])
        date = match[i][5]
        add_link(title, vidurl, 'play_video', thumb, date + "\n" + description, duration)
    match_page = re.compile('<a class="next" href="://(.+?)">Next&nbsp;&raquo;</a>', re.DOTALL).findall(content)
    page_count = re.compile('<a class="next" href="://.+?page=(.+?)">Next&nbsp;&raquo;</a>', re.DOTALL).findall(content)
    if len(page_count) > 0:
        add_dir(translation(30001) + " (" + str(page_count[0]) + ")",
                match_page[0] + "&category=videos", 'list_series_episodes', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if force_view_mode:
        xbmc.executebuiltin('Container.SetViewMode(' + viewMode + ')')


def list_series(url):
    content = get_url(url)
    spl = content.split('<div class="grid_16 alpha bottom_2">')
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
    xbmcplugin.endOfDirectory(pluginhandle)
    if force_view_mode:
        xbmc.executebuiltin('Container.SetViewMode(' + viewMode + ')')


def search():
    keyboard = xbmc.Keyboard('', translation(30008))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        list_search_results('/search?q=' + search_string + '&page=0&count=10&type=video')


def list_search_results(url):
    url_main = url
    content = get_url(url)
    spl = content.split('<div class="search-item"')
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
    match = re.compile('data-page="(.+?)"', re.DOTALL).findall(content)
    page = int(match[0])
    match = re.compile('data-total="(.+?)"', re.DOTALL).findall(content)
    max_page = int(int(match[0]) / 10)
    url_next = url_main.replace("page=" + str(page), "page=" + str(page + 1))
    if page < max_page:
        add_dir(translation(30001), url_next, 'list_search_results', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if force_view_mode:
        xbmc.executebuiltin('Container.SetViewMode(' + viewMode + ')')


def play_video(page_url):
    match = re.compile(base_url + "(.+)", re.DOTALL).findall(page_url)
    vid = Video(match[0])
    final_url = vid.get_vid_url(max_video_height)
    list_item = xbmcgui.ListItem(path=final_url)
    return xbmcplugin.setResolvedUrl(pluginhandle, True, list_item)


class Video:
    def __init__(self, vid_url):
        self.url = vid_url
        self.video_type = ""
        self.urls = {}

    def _detect(self):
        content = get_url(self.url)
        has_video_url = False

        if "data-settings" in content:
            has_video_url = True;
            self._get_data_settings(content)

        if "hero-unit-container" in content:
            has_video_url = True;
            self._get_hero_unit_container(content)

        if not has_video_url:
            show_dialog("Unknown Video", "The IGN-Plugin does not know how to handle the selected video. "
                                       "Please report the name of the video on the Kodi-Forums so it can be fixed. "
                                       "http://forum.kodi.tv/showthread.php?tid=136353")

    def _get_data_settings(self, content):
        match = re.compile("data-settings='(.+?)'").findall(content)
        match = re.compile('"(\d+?)":{"url":"(.+?)",.+?}').findall(match[0])
        for res in match:
            self.urls[res[0]] = res[1].replace("\\", "")

    def _get_hero_unit_container(self, content):
        match = re.compile('class="hero-poster instant-play hidden"\n\s.+?\n\s.+?data-id="(.+?)"', re.DOTALL)\
            .findall(content)
        config = get_url("/videos/configs/id/" + match[0] + ".config").replace("\\", "")
        temp_matches = re.compile('"url":"(.+?)/zencoder/(.+?)/(.+?)/(.+?)/(.+?)/(.+?)-(.+?)-(.+?)"', re.DOTALL)\
            .findall(config)
        start_url = temp_matches[0][0]
        date = temp_matches[0][1] + "/" + temp_matches[0][2] + "/" + temp_matches[0][3]
        resolution = int(temp_matches[0][4])
        vid_id = temp_matches[0][5]
        bitrate = temp_matches[0][6]
        ext = temp_matches[0][7]

        for i in range(0, len(video_height), 1):

            temp_url = start_url + "/zencoder/" + date + "/" + str(max_video_quality[i]) + "/" + vid_id + "-" + str(
                max_video_bitrate[i]) + "-" + ext
            try:
                ret = urllib2.urlopen(temp_url)
                if ret.code == 200:
                    self.urls[video_height[i]] = temp_url
            except urllib2.HTTPError, e:
                xbmc.log('HTTPError: ' + temp_url)
            except urllib2.URLError, e:
                xbmc.log('URLError: ' + temp_url)

    def get_vid_url(self, res):
        self._detect()
        final_url = ""
        for u in self.urls.keys():
            if int(u) >= res:
                final_url = self.urls[u]
        return final_url


def show_dialog(title, text):
    dialog = xbmcgui.Dialog()
    dialog.ok(title, text)


def play_live_stream(url):
    listitem = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def clean_title(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "'").replace(
        "&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace(
        "&uuml;", "ü").replace("&ouml;", "ö")
    title = title.replace("<em>", "").replace("</em>", "").strip()
    return title


def clean_url(title):
    title = title.replace("&#x3A;", ":").replace("&#x2F;", "/")
    return title


def get_url(url):
    req = urllib2.Request(base_url + url)
    req.add_header('User-Agent',
                   'Mozilla/5.0 (X11; CrOS i686 2268.111.0) '
                   'AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11')
    req.add_header('Cookie', 'i18n-ccpref=15-US-www-1')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link


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


def add_link(name, url, mode, iconimage, desc="", duration=""):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Duration": duration})
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def add_dir(name, url, mode, iconimage, desc=""):
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url) + '&mode=' + str(mode)
    liz = xbmcgui.ListItem(name, iconImage='DefaultFolder.png', thumbnailImage=iconimage)
    liz.setInfo(type='video', infoLabels={'title': name, 'plot': desc, 'plotoutline': desc})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('url')
if isinstance(url, str):
    url = urllib.unquote_plus(url)

if mode == 'list_videos':
    list_videos(url)
elif mode == 'list_series':
    list_series(url)
elif mode == 'list_search_results':
    list_search_results(url)
elif mode == 'play_video':
    play_video(url)
elif mode == 'list_series_episodes':
    list_series_episodes(url)
elif mode == 'podcast_index':
    podcast_index()
elif mode == 'play_live_stream':
    play_live_stream(url)
elif mode == 'search':
    search()
else:
    index()
