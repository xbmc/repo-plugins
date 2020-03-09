# coding=utf-8
##########################################################################
#
#  Copyright 2014 Lee Smith
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##########################################################################

import os
import re
from urlparse import urlparse, urlunparse, urljoin
from urllib import urlencode
from datetime import timedelta
from functools import partial
import xml.etree.ElementTree as ET
import traceback
import json
import platform

from kodiswift import Plugin, xbmc, xbmcgui
from bs4 import BeautifulSoup
import requests
import livestreamer
import rollbar

from resources.lib import utils
from resources.lib import youtube
from resources.lib import new_stadium
from resources.lib import api

HOST = "http://www.tottenhamhotspur.com"
BASE_URL = HOST
SEARCH_URL = urljoin(HOST, "search")
PARTNER_ID = 2000012

MEDIA_SCHEME = "http"
MEDIA_HOST = "open.http.mp.streamamg.com"
MEDIA_URL_ROOT = urlunparse((MEDIA_SCHEME, MEDIA_HOST, "/p/{}/".format(PARTNER_ID), None, None, None))


THUMB_URL_FMT = MEDIA_URL_ROOT + "thumbnail/entry_id/{}/height/720"

HLS_URL_FMT = MEDIA_URL_ROOT + "playManifest/entryId/{}/format/applehttp"

PLAYLIST_XML_FMT = urlunparse((MEDIA_SCHEME, MEDIA_HOST,
                               "index.php/partnerservices2/executeplaylist?" +
                               "partner_id={}&playlist_id={{}}".format(PARTNER_ID), None, None, None))

COMPETITIONS = [
    ('Premier League', 43172, '23676/premier-league-2048.jpg'),
    ('Champions League', 44679,
     '1093/ticket-details-for-our-ucl-away-matches-updated-with-real-madrid-champions_league_trophy730.jpg'),
    ('FA Cup', 43996, '2654/facup_draw730a.jpg'),
    ('Carabao Cup', 44729, '1203/carabao-cup-spurs-v-barnsley-ticket-news-carabao_cup730.jpg')
]


plugin = Plugin()

debug = plugin.get_setting('debug', bool)


def kodi_version():
    query = dict(jsonrpc='2.0',
                 method='Application.GetProperties',
                 params=dict(properties=['version', 'name']),
                 id=1)
    response = json.loads(xbmc.executeJSONRPC(json.dumps(query)))
    return response['result']['version']

def log(msg):
    if debug:
        plugin.log.info(msg)

def error_report_yes(exc):
    return xbmcgui.Dialog().yesno(plugin.get_string(30130), plugin.get_string(30131),
                                  "[COLOR=red]{}[/COLOR]".format(exc), plugin.get_string(30133))

def report_error():
    data = {'version': plugin.addon.getAddonInfo('version'),
            'platform': platform.system(),
            'machine': platform.machine(),
            'url': plugin.request.url,
            'kodi': kodi_version()}
    rollbar.report_exc_info(extra_data=data)

def get_media_url(entry_id):
    hls_url = HLS_URL_FMT.format(entry_id)
    livestreamer_url = 'hlsvariant://' + hls_url
    log("Retrieving streams from {}".format(hls_url))
    resolution = plugin.get_setting('resolution')
    streams = livestreamer.streams(livestreamer_url, sorting_excludes=[">{}".format(resolution)])
    log("Available streams: {}".format(' '.join(streams)))

    media_url = streams['best'].url
    log("Playing URL {}".format(media_url))
    return media_url

def get_playlist_videos(playlist_id):
    playlist_url = PLAYLIST_XML_FMT.format(playlist_id)
    log("Playlist XML URL {}".format(playlist_url))
    xml = requests.get(playlist_url).content
    root = ET.fromstring(xml, parser=ET.XMLParser(encoding='UTF-8'))
    for entry in root.find('result').find('entries'):
        entry_id = entry.find('id').text
        title = entry.find('name').text
        date_str = entry.find('createdAt').text.split()[0]
        yield video_item(entry_id, title, date_str, date_format="%Y-%m-%d",
                         duration=entry.find('duration').text)

def get_stadium_index():
    for title, youtube_id in new_stadium.get_cams():
        yield {'label': title,
               'thumbnail': 'https://i.ytimg.com/vi/{}/sddefault_live.jpg'.format(youtube_id),
               'info': {'title': title},
               'path': "plugin://plugin.video.youtube/play/?video_id={}".format(youtube_id),
               'is_playable': True}

    yield {'label': plugin.get_string(30019),
           'path': plugin.url_for('show_stadium_video_gallery')}

def get_youtube_index():
    for playlist, stringid in (("latest", 30010),
                               ("popular", 30015)):
        yield {'label': plugin.get_string(stringid),
               'path': plugin.url_for('show_youtube_list', playlist=playlist)}

    yield {'label': plugin.get_string(30011),
           'path': plugin.url_for('youtube_search')}

    yield {'label': plugin.get_string(30016),
           'path': plugin.url_for('show_youtube_playlists')}

def get_youtube_playlists():
    for playlist_id, title, thumbnail, published_at in youtube.get_playlists():
        item = {'label': title,
                'thumbnail': thumbnail,
                'info': {'title': title, 'date': published_at.strftime("%d.%m.%Y")},
                'path': plugin.url_for('show_youtube_list', playlist=playlist_id)}

        yield item

def get_youtube_video_items(generator):
    for video_id, title, thumbnail, published_at in generator():
        item = {'label': title,
                'thumbnail': thumbnail,
                'info': {'title': title, 'date': published_at.strftime("%d.%m.%Y")},
                'path': "plugin://plugin.video.youtube/play/?video_id={}".format(video_id),
                'is_playable': True}

        yield item

def video_item(entry_id, title, date_str=None, date_format="%d %B %Y", duration_str=None, duration=None):
    item = {'label': title,
            'thumbnail': THUMB_URL_FMT.format(entry_id),
            'path': plugin.url_for('play_video', entry_id=entry_id),
            'is_playable': True}

    info = {'title': title}
    if date_str is not None:
        info['date'] = utils.date_from_str(date_str, date_format).strftime("%d.%m.%Y")
    item['info'] = info

    if duration is not None:
        item['stream_info'] = {'video': {'duration': duration}}
    elif duration_str is not None:
        minutes, seconds = duration_str.split(':')
        duration = timedelta(minutes=int(minutes), seconds=int(seconds))
        item['stream_info'] = {'video': {'duration': duration.seconds}}

    return item


@plugin.route('/')
def show_index():
    image_path = os.path.join(plugin.addon.getAddonInfo('path'), 'resources', 'images')

    yield {
        'label': plugin.get_string(30010),
        'path': plugin.url_for('show_videos_page', tag_id=56552, page=1),
        'thumbnail': plugin.addon.getAddonInfo('icon')
    }

    yield {
        'label': plugin.get_string(30020),
        'path': plugin.url_for('show_videos_page', tag_id=45833, page=1),
        'thumbnail': api.image_url('23675/match-highlights.jpg')
    }

    for competition, tag_id, thumbnail_path in COMPETITIONS:
        yield {
            'label': competition,
            'path': plugin.url_for('show_videos', tag_id=tag_id),
            'thumbnail': api.image_url(thumbnail_path)
        }

    yield {
        'label': plugin.get_string(30017),
        'path': plugin.url_for('show_stadium_video_gallery'),
        'thumbnail': api.image_url('4363/newstadium-concept-internalbowl-eveninggamewithfans.jpg')
    }

    yield {
        'label': "The Vault",
        'path': plugin.url_for('show_playlist', playlist_id='0_32nxk7s7'),
        'thumbnail': os.path.join(image_path, 'the-vault-video-image.jpg')
    }

    yield {
        'label': plugin.get_string(30001),
        'path': plugin.url_for('show_youtube_index'),
        'thumbnail': os.path.join(image_path, 'YouTube-logo-light.png')
    }


def video_page_items(tag_id, page):
    page = int(page)
    videos, end = api.videos(tag_id, page=page, items=12)

    if page > 1:
        yield {
            'label': u'[B]<< {} ({:d})[/B]'.format(plugin.get_string(30013), page - 1),
            'path': plugin.url_for('show_videos_page', tag_id=tag_id, page=page - 1)
        }
    if not end:
        yield {
            'label': u'[B]{} ({:d}) >> [/B]'.format(plugin.get_string(30012), page + 1),
            'path': plugin.url_for('show_videos_page', tag_id=tag_id, page=page + 1)
        }

    for video in videos:
        yield video_item(video.entry_id, video.title)


@plugin.route('/tag/<tag_id>/page/<page>')
def show_videos_page(tag_id, page):
    return plugin.finish(video_page_items(tag_id, page), update_listing=(int(page) > 1))


@plugin.route('/tag/<tag_id>')
def show_videos(tag_id):
    videos, _ = api.videos(tag_id=tag_id)
    return (video_item(video.entry_id, video.title) for video in videos)


@plugin.route('/stadium')
def show_stadium_video_gallery():
    return (video_item(entry_id, title)
            for title, entry_id in new_stadium.get_video_gallery())

@plugin.route('/playlist/<playlist_id>')
def show_playlist(playlist_id):
    return plugin.finish(get_playlist_videos(playlist_id),
                         sort_methods=['unsorted', 'date', 'duration', 'title'])

@plugin.route('/video/<entry_id>')
def play_video(entry_id):
    return plugin.set_resolved_url(get_media_url(entry_id))

@plugin.cached_route('/youtube')
def show_youtube_index():
    return list(get_youtube_index())

@plugin.route('/youtube/playlists')
def show_youtube_playlists():
    return plugin.finish(get_youtube_playlists(),
                         sort_methods=['unsorted', 'date', 'title'])

@plugin.route('/youtube/playlist/<playlist>')
def show_youtube_list(playlist="latest"):
    if playlist == "latest":
        generator = youtube.get_latest
    elif playlist == "popular":
        generator = youtube.get_popular
    else:
        generator = partial(youtube.get_playlist_items, playlist)

    return plugin.finish(get_youtube_video_items(generator),
                         sort_methods=['unsorted', 'date', 'title'])

@plugin.route('/youtube/search')
def youtube_search():
    query = plugin.keyboard(heading="Search")
    if query:
        url = plugin.url_for('youtube_search_result', query=query)
        plugin.redirect(url)

@plugin.route('/youtube/search/<query>')
def youtube_search_result(query):
    generator = partial(youtube.get_search_results, query)
    return plugin.finish(get_youtube_video_items(generator),
                         sort_methods=['unsorted', 'date', 'title'])


if __name__ == '__main__':
    rollbar.init('45541e2cb1e24f95b9c6311c2e931a11')
    try:
        plugin.run()
    except Exception as exc:
        if plugin.get_setting('send_error_reports', bool) or error_report_yes(exc):
            report_error()
            xbmcgui.Dialog().notification(plugin.name, plugin.get_string(30134))
        plugin.log.error(traceback.format_exc())
