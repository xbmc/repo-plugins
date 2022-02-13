# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

import xml.etree.ElementTree as ET


FORMAT_URL = 'https://fosdem.org/{year}/schedule/xml'


def fetch_xml(year):
    if not hasattr(fetch_xml, 'cached'):
        fetch_xml.cached = {}

    if fetch_xml.cached.get(year):
        return fetch_xml.cached[year]

    http_get = urlopen(FORMAT_URL.format(year=year))
    data = http_get.read()
    http_get.close()
    fetch_xml.cached[year] = ET.fromstring(data)
    return fetch_xml.cached[year]


def contains_videos(links):
    videos = list([x for x in [x.attrib['href'] for x in links] if 'video.fosdem.org' in x])
    return videos != []
