#!/usr/bin/env python

import re
import sys
import time
from urllib2 import urlopen
from xml.dom.minidom import parseString

ATOM_MIME_TYPE          = 'application/atom+xml'
THUMBNAIL_MIME_TYPE     = 'image/jpeg'
FLASH_VIDEO_MIME_TYPE   = 'video/x-flv'
PLAYLIST_MIME_TYPE      = 'application/x-mpegURL'
START_URL               = 'http://deredactie.be/cm/vrtnieuws/videozone?mode=atom'

# TODO Expose as preference
USE_HLS = 1
USE_HTTPS = 0

class Item(object):
    def __init__(self, title, date, url, mime_type):
        self.title = title
        self.date = date
        self.url = url
        self.mime_type = mime_type

class VideoItem(Item):
    def __init__(self, title, date, video_url, video_mime_type,
            thumbnail_url, thumbnail_mime_type):
        super(VideoItem, self).__init__(title, date, video_url, video_mime_type)
        self.thumbnail_url = thumbnail_url
        self.thumbnail_mime_type = thumbnail_mime_type

def normalize_url(url):
    if url is None:
        return url
    protocol = 'https://' if USE_HTTPS else 'http://'
    return re.sub(r'.*?//', protocol, url)

def parse_feed(url):
    url = normalize_url(url)
    return parse_feed_xml(_get_url(url))

def parse_feed_xml(xml):
    dom = parseString(xml)
    title = dom.getElementsByTagName('title')[0].firstChild.data
    entries = []
    for entry_elem in dom.getElementsByTagName('entry'):
        entry = parse_entry(entry_elem)
        entries.append(entry)
    return (title, entries)

def parse_entry(entry_elem):
    title = None
    date = None
    feed_url = None
    video_url = None
    thumbnail_url = None
    for link_elem in entry_elem.getElementsByTagName('link'):
        attr = link_elem.attributes
        rel = attr['rel'].value
        href = attr['href'].value
        mime_type = re.sub(r';.*', '', attr['type'].value)
        if rel == 'enclosure':
            if mime_type == THUMBNAIL_MIME_TYPE:
                thumbnail_url = href
            elif not USE_HLS and mime_type == FLASH_VIDEO_MIME_TYPE:
                video_url = href
                video_mime_type = FLASH_VIDEO_MIME_TYPE
        elif rel == 'self' and mime_type == ATOM_MIME_TYPE:
            title = attr['title'].value
            feed_url = href
    if USE_HLS:
        elems = entry_elem.getElementsByTagName('vrtns:iosURL')
        if len(elems) and elems[0].firstChild is not None:
            video_url = elems[0].firstChild.data
            video_url = re.sub(r'/playlist\.m3u8$', '/chunklist.m3u8', video_url)
            video_mime_type = PLAYLIST_MIME_TYPE
    date_str = entry_elem.getElementsByTagName('published')[0].firstChild.data
    date = time.strptime(date_str[:18], '%Y-%m-%dT%H:%M:%S')
    if video_url is not None:
        video_url = normalize_url(video_url)
        thumbnail_url = normalize_url(thumbnail_url)
        return VideoItem(title, date, video_url, video_mime_type,
            thumbnail_url, THUMBNAIL_MIME_TYPE)
    else:
        feed_url = normalize_url(feed_url)
        return Item(title, date, feed_url, ATOM_MIME_TYPE)

def _get_url(url):
    return urlopen(url).read()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = START_URL

    (title, entries) = parse_feed(url)

    print 'Title: {0}'.format(title)

    for entry in entries:
        print '\n- {0}\n  Date:  {1}\n  URL:   {2}'.format(
            entry.title.encode('utf-8', 'ignore'),
            time.strftime('%Y-%m-%d %H:%M:%S', entry.date),
            entry.url
        )
        if isinstance(entry, VideoItem):
            print '  Thumb: {0}'.format(entry.thumbnail_url)
