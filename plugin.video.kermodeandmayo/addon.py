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

import re
from datetime import date, timedelta
import time
from functools import partial
import json

from kodiswift import Plugin, xbmc
from bs4 import BeautifulSoup
import requests
import rollbar

from resources.lib import youtube


CLIP_HOST = "https://bbc.co.uk"
CLIP_URL_FMT = CLIP_HOST + "/programmes/b00lvdrj/clips?page={0}"

CLIP_THUMB_WIDTH = 640

CLIP_JSON_FMT = CLIP_HOST + "/programmes/{0}.json"
CLIP_XML_FMT = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/iptv-all/vpid/{0}"

PODCAST_XML = "http://downloads.bbc.co.uk/podcasts/fivelive/kermode/rss.xml"
PODCAST_THUMB = "http://ichef.bbci.co.uk/podcasts/artwork/478/kermode.jpg"


plugin = Plugin()

def get_soup(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')


def clip_item(pid, title, duration_str, thumb_src):
    minutes, seconds = duration_str.split(':')
    duration = timedelta(minutes=int(minutes), seconds=int(seconds))

    item = {'label': title,
            'thumbnail': thumb_src,
            'is_playable': True,
            'path': plugin.url_for('play_clip', pid=pid),
            'info': {'title': title,
                     'album': plugin.get_string(30000)
                     },
            'stream_info': {'video': {'duration': duration.seconds}
                            }
            }

    return item

def add_item_info(item, title, item_date):
    item['info'] = {'title': title,
                    'date': item_date.strftime("%d.%m.%Y")}

def get_clips(soup, page):
    pages = soup.find('ol', 'pagination')

    if not pages.find('li', 'pagination__next pagination--disabled'):
        next_page = str(page + 1)
        item = {'label': u"{0} ({1}) >>".format(plugin.get_string(30001), next_page),
                'path': plugin.url_for('clips', page=next_page)
                }
        yield item

    if page > 1:
        previous_page = str(page - 1)
        item = {'label': u"<< {0} ({1})".format(plugin.get_string(30002), previous_page),
                'path': plugin.url_for('clips', page=previous_page)
                }
        yield item

    for clip in soup('div', 'programme--clip'):
        pid = clip['data-pid']
        title = clip.find('span', 'programme__title').text.strip()
        _, duration_str = clip.find(
            'p', 'programme__service').string.strip().split()
        thumbs = clip.find(
            'div', 'programme__img-box').img['data-srcset'].split(', ')
        thumb_src, _ = next(
            thumb for thumb in thumbs if thumb.endswith("{}w".format(CLIP_THUMB_WIDTH))).split()
        yield clip_item(pid, title, duration_str, thumb_src)

def get_podcasts():
    soup = get_soup(PODCAST_XML)
    for podcast in soup('item'):
        title = podcast.title.string
        date_str = podcast.pubdate.string[:16]
        air_date = date(*(time.strptime(date_str, "%a, %d %b %Y")[:3]))

        media = podcast.find('media:content')

        item = {'label': title,
                'thumbnail': PODCAST_THUMB,
                'is_playable': True,
                'path': media['url'],
                'info': {'title': title,
                         'date': air_date.strftime("%d.%m.%Y"),
                         'size': int(media['filesize']),
                         'duration': int(media['duration']),
                         'album': plugin.get_string(30000)
                         },
                'properties': {'mimetype': 'audio/mpeg'},
                'stream_info': {'audio': {'codec': 'mp3',
                                          'language': 'en'}
                                }
                }

        yield item

def get_youtube_playlists():
    for playlist_id, title, thumbnail, published_at in youtube.get_playlists():
        item = {'label': title,
                'thumbnail': thumbnail,
                'path': plugin.url_for('show_youtube_list', playlist=playlist_id)}

        add_item_info(item, title, published_at)

        yield item

def get_youtube_video_items(generator):
    for video_id, title, thumbnail, published_at in generator():
        item = {'label': title,
                'thumbnail': thumbnail,
                'path': "plugin://plugin.video.youtube/play/?video_id={0}".format(video_id),
                'is_playable': True}

        add_item_info(item, title, published_at)

        yield item

def has_movie_library():
    request = {"jsonrpc": "2.0",
               "method": "VideoLibrary.GetMovies",
               "id": "movies"}

    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
        return response['result']['limits']['total'] > 0
    except:
        return False

def get_library_searches():
    request = {"jsonrpc": "2.0",
               "method": "VideoLibrary.GetMovies",
               "params": {"sort": {"order": "ascending", "method": "label", "ignorearticle": True},
                          "properties" : ["thumbnail"]},
               "id": "movies"}

    response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))

    result = response['result']
    if 'movies' in result:
        for movie in result['movies']:
            name = movie['label'].encode('utf-8')
            item = {'label': name,
                    'thumbnail': movie['thumbnail'],
                    'path': plugin.url_for('youtube_search_result', query=name)}
            yield item

def get_version_pid(pid):
    return requests.get(CLIP_JSON_FMT.format(pid)).json()['programme']['versions'][0]['pid']


###########################################################################################

@plugin.route('/')
def index():
    try:
        youtube_icon = Plugin(addon_id="plugin.video.youtube").addon.getAddonInfo('icon')
    except:
        youtube_icon = None

    items = [{'label': plugin.get_string(30003),
              'thumbnail': "http://ichef.bbci.co.uk/podcasts/artwork/478/kermode.jpg",
              'path': plugin.url_for('podcasts')},
             {'label': plugin.get_string(30004),
              'thumbnail': "http://ichef.bbci.co.uk/images/ic/512x288/p01lysw6.jpg",
              'path': plugin.url_for('clips', page='1')},
             {'label': "Kermode Uncut",
#             'path': plugin.url_for('show_youtube_list', playlist="PLwSLy9KPuWVVNS5N7WVzIAveGWBIbfgZF")}]
              'thumbnail': "http://static.bbc.co.uk/programmeimages/512xn/images/p012j25p.jpg",
              'path': plugin.url_for('youtube_search_result', query="Kermode Uncut: ")},
             {'label': plugin.get_string(30005),
              'thumbnail': youtube_icon,
              'path': plugin.url_for('show_youtube_list', playlist='latest')},
             {'label': plugin.get_string(30006),
              'thumbnail': youtube_icon,
              'path': plugin.url_for('show_youtube_list', playlist='popular')},
             {'label': plugin.get_string(30007),
              'thumbnail': youtube_icon,
              'path': plugin.url_for('youtube_playlists')},
             {'label': plugin.get_string(30008),
              'thumbnail': youtube_icon,
              'path': plugin.url_for('youtube_search')}]

    if has_movie_library():
        items.append({'label': plugin.get_string(30009),
                      'thumbnail': youtube_icon,
                      'path': plugin.url_for('youtube_search_library')})

    return items

@plugin.route('/podcasts')
def podcasts():
    return plugin.finish(get_podcasts(),
                         sort_methods=['date',
                                       'duration',
                                       'title',
                                       'size'])

@plugin.route('/clips/page/<page>')
def clips(page='1'):
    soup = get_soup(CLIP_URL_FMT.format(page))

    page = int(page)
    if page > 1:
        update_listing = True
    else:
        update_listing = False

    return plugin.finish(get_clips(soup, page),
                         sort_methods=['playlist_order', 'duration', 'title'],
                         update_listing=update_listing)

@plugin.route('/clip/<pid>')
def play_clip(pid):
    vpid = get_version_pid(pid)

    xml = requests.get(CLIP_XML_FMT.format(vpid)).text
    plugin.log.debug(xml)
    media = BeautifulSoup(xml, 'html.parser').find(
        'media',
        service='stream-uk-iptv_streaming_concrete_combined_sd'
    )
    connection = media.find(supplier='mf_akamai_uk_hls')
    return plugin.set_resolved_url(connection['href'])

@plugin.route('/youtube/playlists')
def youtube_playlists():
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

@plugin.route('/youtube/search-library')
def youtube_search_library():
    return get_library_searches()

@plugin.route('/youtube/search/<query>')
def youtube_search_result(query):
    generator = partial(youtube.get_search_results, query)
    return plugin.finish(get_youtube_video_items(generator),
                         sort_methods=['unsorted', 'date', 'title'])


if __name__ == '__main__':
    rollbar.init('0a87de9bd8434df2a691b99cf0da3d98')
    try:
        plugin.run()
    except Exception:
        rollbar.report_exc_info(extra_data={'url': plugin.request.url})
        raise
