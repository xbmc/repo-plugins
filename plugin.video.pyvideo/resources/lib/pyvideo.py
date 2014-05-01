# -*- coding: utf-8 -*-
# Copyright 2012 Jörn Schumacher
# Copyright 2014 Benjamin Bertrand
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import bs4
import re
try:
    # We want to import script.module.requests2
    import requests2 as requests
except ImportError:
    # Allows to run the script in cli
    import requests
import urlparse
from config import plugin


ROOT_URL = 'http://pyvideo.org'
CATEGORY_URL = ROOT_URL + '/category'
SEARCH_URL = ROOT_URL + '/search'
API_URL = ROOT_URL + '/api/v2/'
API_VIDEO_URL = API_URL + 'video/'
VIDEO_ID_RE = re.compile('/video/(\d+)/')
FORMATS = ['ogv', 'webm', 'mp4', 'flv']
ADDONS = {
    'youtube': 'plugin://plugin.video.youtube/?action=play_video&videoid={0}',
    'vimeo': 'plugin://plugin.video.vimeo/?action=play_video&videoid={0}'}


def get(url, **kwargs):
    """Return the response of the HTTP get request"""
    plugin.log.debug('HTTP request: {0}'.format(url))
    return requests.get(url, **kwargs)


def get_soup(url, **kwargs):
    """Return the parsed content of HTTP get request"""
    response = get(url, **kwargs)
    return bs4.BeautifulSoup(response.text)


def get_json(url, **kwargs):
    """Return the json-encode content of HTTP get request"""
    response = get(url, **kwargs)
    return response.json()


def get_video_id(url):
    """Return the pyvideo video id from the given url

    The video id can be used to retrieve json metadata via the API
    """
    m = VIDEO_ID_RE.match(url)
    if m:
        return m.group(1)
    return None


def get_videos_from_page(soup):
    """Return the list of videos found on the page"""
    videos = []
    for div in soup.select('.video-summary'):
        item = {'title': div.find('strong').a.text,
                'id': get_video_id(div.find('a').get('href')),
                'thumbnail': div.find('img').get('src')
                }
        videos.append(item)
    return videos


def get_categories():
    """Return the list of categories"""
    soup = get_soup(CATEGORY_URL)
    rows = soup.find_all('tr')
    categories = []
    conf = ''
    # We look at the first column of the table
    # If there is no link, it's the conference title.
    # The following rows are the years.
    for row in rows:
        link = row.td.a
        if link is None:
            conf = row.td.text
        else:
            title = link.text
            if title.isdigit():
                title = ' '.join([conf, title])
            categories.append(
                    {'title': title,
                     'url': link.get('href')})
    return categories


def get_category_videos(url):
    """Return the list of videos found for the given category url"""
    soup = get_soup(ROOT_URL + url)
    return get_videos_from_page(soup)


def get_latest():
    """Return the latest videos displayed on the front page"""
    soup = get_soup(ROOT_URL)
    return [{'title': link.text,
             'id': get_video_id(link.get('href')),
             } for link in soup.select('ul a[href^=/video]')]


def search(text):
    """Return the list of matching videos using the website search

    Only results from first page are returned.
    Pagination seems broken on the website.
    """
    payload = {'models': 'videos.video',
               'q': text}
    soup = get_soup(SEARCH_URL, params=payload)
    return get_videos_from_page(soup)


def get_youtube_id(url):
    """Return the youtube id from url or None"""
    try:
        v = urlparse.parse_qs(urlparse.urlparse(url).query)['v'][0]
    except Exception:
        plugin.log.debug('failed to parse youtube url: {0}'.format(url))
        return None
    return v


def get_vimeo_id(url):
    """Return the vimeo id from url or None"""
    m = re.search('vimeo.com/(\d+)', url)
    if m:
        return m.group(1)
    plugin.log.debug('failed to parse vimeo url: {0}'.format(url))
    return None


def resolve_url(video):
    """Return a playbable url from the video json metadata"""
    # We first check if there is a file available
    # in the existing format
    for fmt in FORMATS:
        attribute = 'video_{0}_url'.format(fmt)
        if video[attribute]:
            plugin.log.debug('found {0} format {1}'.format(
                fmt, video[attribute]))
            return video[attribute]
    # We fallback to the source url.
    src_url = video['source_url']
    for service, addon in ADDONS.items():
        if service in src_url:
            video_id = globals()['get_{0}_id'.format(service)](src_url)
            if video_id:
                plugin.log.debug(
                        'found {0} video id {1}'.format(service, video_id))
                return addon.format(video_id)
    plugin.log.debug('unknown source url {0}'.format(src_url))
    return src_url


def get_video_url(video_id):
    """Return a playable url for video id"""
    video = get_json(API_VIDEO_URL + video_id)
    return resolve_url(video)
