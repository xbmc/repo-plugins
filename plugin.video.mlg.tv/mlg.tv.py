#!/usr/bin/python

import gzip
import json
import re
from StringIO import StringIO
import sys
import urllib
import urllib2
import urlparse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin


base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon()
quality_setting = addon.getSetting('quality')


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


def getJsonData(url):
    request = urllib2.Request(url)
    request.add_header('Accept-encoding', 'gzip')
    request.add_header('Accept', 'application/json')

    data = urllib2.urlopen(request)
    buffer_compressed = StringIO(data.read())
    buffer_decompressed = gzip.GzipFile(fileobj=buffer_compressed)

    result = json.loads(buffer_decompressed.read())
    return result


class M3u8:
    def __init__(self, url):
        request = urllib2.Request(url)

        data = urllib2.urlopen(request)
        buffer = StringIO(data.read())

        self.parse(buffer.read())

    def parse(self, m3u8):
        m3u8_streams_regex = re.compile('BANDWIDTH=(?P<Bitrate>\d+),'
                                        'RESOLUTION=\d+x(?P<Resolution>\d+).*'
                                        '\n(?P<url>http:\/\/.+?av-p.+)')
        self.stream_urls = sorted(m3u8_streams_regex.findall(m3u8),
                                  key=lambda stream: int(stream[0]),
                                  reverse=True)


def addStream(title, stream_url, infoLabels={}, image='DefaultVideo.png'):
    url = build_url({'mode': 'playStream', 'url': stream_url})
    streamItem = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
    xbmcplugin.addDirectoryItem(handle=addon_handle,
                                url=url,
                                listitem=streamItem)


def listStreams():
    streams = getJsonData(
        'http://streamapi.majorleaguegaming.com/service/streams/all?status=1')
    channels_info = getJsonData(
        'http://www.majorleaguegaming.com/api/channels/all.js'
        '?fields=id,name,subtitle,image_16_9_medium'
        )

    for stream in sorted(streams['data']['items'],
                         key=lambda s: s.get('viewers', 0),
                         reverse=True):
        stream_url = 'http://streamapi.majorleaguegaming.com'\
                     '/service/streams/playback/'\
                     '%s?format=all' % stream['stream_name']

        channel_info = next(channel for channel
                            in channels_info['data']['items']
                            if channel['id'] == stream['channel_id'])

        addStream(channel_info['name'],
                  stream_url,
                  image=channel_info['image_16_9_medium'])


def getQualityUrl(url):
    if quality_setting == '0':
        return url
    else:
        m3u8 = M3u8(url)
        if quality_setting == '1':
            return m3u8.stream_urls[0][2]

        elif quality_setting == '2':
            return next(stream for stream
                        in m3u8.stream_urls
                        if stream[1] == '720')[2]

        elif quality_setting == '3':
            streams = [stream for stream
                       in m3u8.stream_urls
                       if stream[1] == '720']
            return streams[-1][2]

        elif quality_setting == '4':
            return next(stream for stream
                        in m3u8.stream_urls
                        if stream[1] == '480')[2]

        elif quality_setting == '5':
            return next(stream for stream
                        in m3u8.stream_urls
                        if stream[1] == '360')[2]


def play(url):
    items = getJsonData(url)
    stream_url = next(item['url'] for item
                      in items['data']['items']
                      if item['format'] == 'hls')
    built_url = getQualityUrl(stream_url)
    xbmc.executebuiltin("xbmc.PlayMedia(%s)" % built_url)


args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode', None)
if mode is None:
    listStreams()
    xbmcplugin.endOfDirectory(addon_handle)
elif mode[0] == 'playStream':
    play(args.get('url', None)[0])
