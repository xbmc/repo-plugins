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
import requests
import urlparse
from config import plugin


ROOT_URL = 'http://pyvideo.org'
CATEGORY_URL = ROOT_URL + '/category'
SEARCH_URL = ROOT_URL + '/search'
API_URL = ROOT_URL + '/api/v2/'
API_VIDEO_URL = API_URL + 'video/'
API_CATEGORY_URL = API_URL + 'category/'
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
    results = get_json(API_CATEGORY_URL).get('results', [])
    categories = [{'title': result['title'],
                   'slug': result['slug']} for result in results]
    return categories


def get_videos_from_json(items):
    """Return the videos from the json response"""
    return [{'title': result['title'],
             'id': result['id'],
             'thumbnail': result.get('thumbnail_url'),
             'description': result.get('description', ''),
             'summary': result.get('summary', '')} for result in items.get('results', [])]


def get_category_videos(slug, page):
    """Return the list of videos found for the given category slug"""
    items = get_json(API_VIDEO_URL + '/?category=' + slug + '&page=' + page)
    videos = get_videos_from_json(items)
    return (videos, items['next'])


def get_latest():
    """Return the latest videos"""
    items = get_json(API_VIDEO_URL + '/?ordering=-added')
    return get_videos_from_json(items)


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


def exists(url):
    """Send a HEAD request to check if the url exists"""
    try:
        r = requests.head(url)
    except:
        return False
    plugin.log.debug('HEAD request status: {0}'.format(
        r.status_code))
    return r.status_code in (200, 301, 302, 307)


def resolve_url(video):
    """Return a playbable url from the video json metadata"""
    # We first check if there is a file available
    # in the existing format
    for fmt in FORMATS:
        attribute = 'video_{0}_url'.format(fmt)
        if video[attribute]:
            plugin.log.debug('found {0} format {1}'.format(
                fmt, video[attribute]))
            if exists(video[attribute]):
                return video[attribute]
            else:
                plugin.log.debug("{0} doesn't seem to exist".format(
                    video[attribute]))
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
