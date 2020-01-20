#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import simplejson as json

from . import settings
from .app_common import log, get_data, translate, defaultlogo, kodiVersion
from .base import addElement
from .utils import formatAiredString, dateFromTimeStamp

_str_nl = '\n'

# urls
_base_url = 'http://m.puls4.com'
_main_url = 'http://www.puls4.com/api/json-fe/page/'
_highlight_url = 'http://www.puls4.com/api/json-fe/page/sendungen'
_show_dir_url = 'http://www.puls4.com/api/json-fe/page/Alle-Sendungen'
_detail_url = 'http://m.puls4.com/api/video/'


def buildLink(url):
    if not url:
        return url
    if str(url).isdigit():
        return _detail_url + url
    if url[:4] == '/api':
        return _base_url + url
    if url[:4] == '/var':
        return _base_url + url
    if url[:1] == '/':
        return _main_url + url[1:]
    else:
        return url


def getData(url):
    return get_data(buildLink(url))


def getMainMenu():
    log('getMainMenu', 'Debug')
    addElement(translate(30000), defaultlogo, '', translate(30000),
               getJsonContentUrl(_highlight_url), 'getFormatSlider')
    addElement(translate(30001), defaultlogo, '', translate(30001),
               getJsonContentUrl(_show_dir_url), 'getFormatSliderForce')
    if kodiVersion >= 17:
        addElement('Livestream', defaultlogo, '', 'Puls4 LiveStream',
                   '', 'playlive', isFolder=False, width=1024 , height=576)
    getDynamicMenuItems(_main_url)


def getJsonContentUrl(url):
    log('getJsonContentUrl', 'Debug')
    data = getData(url)
    if data.get('content'):
        if len(data.get('content')) > 1:
            return data.get('content')[0].get('url')


def getJsonContentUrls(url):
    log('getJsonContentUrls', 'Debug')
    data = getData(url)
    if data.get('content'):
        if len(data.get('content')) > 0:
            return data.get('content')


def getJsonContentFilter(url):
    log('getJsonContentFilter', 'Debug')
    data = getData(url)
    if data.get('content'):
        for url in data.get('content'):
            if 'content-filter' in url.get('url'):
                return url.get('url')


def getJsonContentFilterUrls(url):
    log('getJsonContentFilterUrls', 'Debug')
    data = getData(url)
    ret = []
    for menu in data.get('menu'):
        ret.append(menu.get('link').get('url'))
        if menu.get('menu'):
            for sub in menu.get('menu'):
                ret.append(sub.get('link').get('url'))
    return ret


def getJsonVideoLink(url):
    log('getJsonVideoLink', 'Debug')
    video = getData(url)[0]
    videourl = None
    if video.get('files').get('h3').get('url'):
        videourl = video.get('files').get('h3').get('url')
    elif video.get('files').get('h2').get('url'):
        videourl = video.get('files').get('h2').get('url')
    elif video.get('files').get('h1').get('url'):
        videourl = video.get('files').get('h1').get('url')
    return videourl


def parseJsonFormatSliderContent(url, forceUrl=False):
    log('parseJsonFormatSliderContent', 'Debug')
    data = getData(url)
    if data.get('formatOverviewItems'):
        for video in data.get('formatOverviewItems'):
            if video.get('blocks'):
                for item in video.get('blocks'):
                    if item.get('channel'):
                        duration = 0
                        name = item.get('channel')
                        fanart = buildLink(
                            video.get('formatOverviewItemImgVersions').get('hi'))
                        icon = buildLink(
                            video.get('formatOverviewItemImgVersions').get('low'))
                        aired = formatAiredString(item.get('airDateTime'))
                        desc = name + _str_nl + aired + _str_nl + \
                            _str_nl + video.get('announcement')
                        isVideo = item.get('isVideo')
                        if isVideo and not forceUrl:
                            url = item.get('objectId')
                            duration = item.get('duration')
                            name = name + ' - ' + item.get('title')
                            mode = 'Play'
                        else:
                            url = item.get('channelUrl')
                            isVideo = False
                            mode = 'getShowByUrl'
                            icon = buildLink(video.get('channelLogoImg'))
                            desc = name
                        addElement(name, fanart, icon, desc, url, mode, duration=duration,
                                   isFolder=not isVideo, showID=item.get('channelId'))
            else:
                if video.get('title'):
                    name = video.get('title')
                    id = video.get('id')
                    fanart = video.get('images').get('format_overview_image').get(
                        'formatOverviewItemImgVersions').get('low')
                    desc = name + _str_nl + video.get('announcement')
                    addElement(name, fanart, fanart, desc, id, 'getShowByID')


def parseJsonGridVideoContent(url):
    log('parseJsonGridVideoContent', 'Debug')
    data = getData(url)
    if data.get('blockType') == 'Characteristics':
        log('Characteristics', 'Debug')
        for cat in data.get('characteristics'):
            title = cat.get('name')
            url = getJsonContentUrl(cat.get('detailUrl').get('url'))
            fanart = cat.get('imageUrl')
            addElement(title, fanart, fanart, title, url, 'getContentGrid')

    elif data.get('rows'):
        for video in data.get('rows'):
            for item in video.get('cols'):
                if 'content' in item:
                    for video_item in item.get('content'):
                        if not 'channel' in video_item:
                            continue
                        name = video_item.get('channel')
                        aired = ''
                        if video_item.get('airDateTime'):
                            aired = formatAiredString(
                                video_item.get('airDateTime'))
                        isVideo = False
                        duration = None
                        if video_item.get('isVideo'):
                            isVideo = video_item.get('isVideo')
                            id = video_item.get('objectId')
                            duration = video_item.get('duration')
                            mode = 'Play'
                        else:
                            id = video_item.get('channelId')
                            mode = 'getShowByID'
                        title = name + ' - ' + video_item.get('title')
                        fanart = video_item.get(
                            'previewLinkVersions').get('low')
                        if video_item.get('description'):
                            desc = name + _str_nl + aired + _str_nl + \
                                _str_nl + video_item.get('description')
                        else:
                            desc = name + _str_nl + aired
                        addElement(title, fanart, fanart, desc, id,
                                   mode, duration=duration, isFolder=not isVideo)


def getJsonShowById(id):
    log('getJsonShowById', 'Debug')
    for video in getData(id):
        fanart = video.get('picture').get('orig')
        duration = video.get('duration')
        date = dateFromTimeStamp(float(video.get('broadcast_datetime')))
        aired = formatAiredString(date)
        title = video.get('title')
        channel = video.get('channel').get('name')
        desc = channel+_str_nl+aired+_str_nl+_str_nl+video.get('description')
        videourl = None
        if video.get('files').get('h3').get('url'):
            videourl = video.get('files').get('h3').get('url')
        elif video.get('files').get('h2').get('url'):
            videourl = video.get('files').get('h2').get('url')
        elif video.get('files').get('h1').get('url'):
            videourl = video.get('files').get('h1').get('url')

        if videourl:
            addElement(title, fanart, fanart, desc, videourl, 'Play',
                       channel, duration, date, isFolder=False)


def getJsonShowByUrl(url):
    log('getJsonShowByUrl', 'Debug')
    contFilt = getJsonContentFilter(url)
    if not contFilt:
        return
    filters = getJsonContentFilterUrls(contFilt)
    # add folders with 'content'
    for filt in filters:
        urlToUse = getJsonContentUrls(filt)
        if len(urlToUse) < 3:
            continue
        urlToUse = urlToUse[len(urlToUse)-2]
        data = getData(filt)
        name = data.get('meta').get('title').replace('- puls4.com', '')
        addElement(name, defaultlogo, defaultlogo, name,
                   urlToUse.get('url'), 'getContentGrid')


def getDynamicMenuItems(url):
    log('getDynamicMenuItems', 'Debug')
    json_links = getJsonContentUrls(url)
    for json_link in json_links:
        url = json_link.get('url')
        data = getData(url)
        if data.get('blockType') == 'FormatOverviewSlider':
            addElement(data.get('title'), defaultlogo,
                       '', data.get('title'), url, 'getFormatSlider')
        elif data.get('blockType') == 'ContentGrid':
            addElement(data.get('headingText'), defaultlogo,
                       '', data.get('headingText'), url, 'getContentGrid')
