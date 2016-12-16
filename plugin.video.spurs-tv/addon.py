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
from datetime import timedelta
from functools import partial
import xml.etree.ElementTree as ET
import traceback
import json
import platform

from xbmcswift2 import Plugin, xbmc, xbmcgui
from bs4 import BeautifulSoup
import requests
import livestreamer
import rollbar

from resources.lib import utils
from resources.lib import youtube

HOST = "http://www.tottenhamhotspur.com"
BASE_URL = HOST
SEARCH_URL = urljoin(HOST, "search")
PARTNER_ID = 2000012

ENTRY_ID_RE = re.compile("entry_id/(\w+)/")
PAGE_RE = re.compile("page +(\d+) +of +(\d+)")

MEDIA_SCHEME = "http"
MEDIA_HOST = "open.http.mp.streamamg.com"
MEDIA_URL_ROOT = urlunparse((MEDIA_SCHEME, MEDIA_HOST, "/p/{}/".format(PARTNER_ID), None, None, None))

THUMBS = {
    'KANE50':
        HOST + "/uploadedImages/Segments/Testing_Area/HARRY50/KANE50-16-17.jpg",
    'The Vault':
        HOST + ("/uploadedImages/Shared_Assets/Images/The_Vault/"
                "Top_20_Premier_League/the-vault-video-image.jpg"),
    'Ledley King Testimonial':
        HOST + ("/uploadedImages/Shared_Assets/Images/News_images/SEASON_13-14/"
                "All_matches/1st_team_matches/Ledley_Testimonial_12_May/leds730.jpg"),
}

THUMB_URL_FMT = MEDIA_URL_ROOT + "thumbnail/entry_id/{}/height/720"

HLS_URL_FMT = MEDIA_URL_ROOT + "playManifest/entryId/{}/format/applehttp"

PLAYLIST_XML_FMT = urlunparse((MEDIA_SCHEME, MEDIA_HOST,
                               "index.php/partnerservices2/executeplaylist?" +
                               "partner_id={}&playlist_id={{}}".format(PARTNER_ID), None, None, None))

FIELD_NAME_ROOT_FMT = ("ctl00$ContentPlaceHolder1$DropZoneMainContent$columnDisplay$"
                       "ctl00$controlcolumn$ctl{:02d}$WidgetHost$WidgetHost_widget$")

PAGINATION_FMT = "Pagination1${}"

SEARCH_NAV_FMT = FIELD_NAME_ROOT_FMT.format(0) + PAGINATION_FMT

PLAYER_VARS_RE = re.compile("kWidget.embed\((.*?)\)", re.MULTILINE|re.DOTALL)
STADIUM_THUMB = HOST + ("/uploadedImages/Shared_Assets/Images/News_images/SEASON_16-17/"
                        "July_2016/NDP_update/west_elevation_instory.jpg")

plugin = Plugin()

form_data = plugin.get_storage('form_data')
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

def get_soup(url, data=None):
    if not url.endswith('/'):
        url += '/'
    if data is not None:
        log("POST {} {}".format(url, data))
        response = requests.post(url, data)
    else:
        log("GET {}".format(url))
        response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')

def get_viewstate(soup):
    return soup.find('input', id='__VIEWSTATE')['value']

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

def get_page_links(soup, endpoint, **kwargs):
    page = None
    links = []
    intro = soup.find('div', 'intro')
    if intro:
        input = intro.find_next_sibling('input')
        form_data['field'] = input['name'].rpartition('$')[0]

        page, npages = [int(n) for n in PAGE_RE.search(intro.contents[0]).groups()]

        if page > 1:
            item = {'label': u"[B]<< {} ({:d})[/B]".format(plugin.get_string(30013), page - 1),
                    'path': plugin.url_for(endpoint,
                                           navigate='prev',
                                           **kwargs)
                    }
            links.append(item)

        if page < npages:
            item = {'label': u"[B]{} ({:d}) >>[/B]".format(plugin.get_string(30012), page + 1),
                    'path': plugin.url_for(endpoint,
                                           navigate='next',
                                           **kwargs)
                    }
            links.append(item)

    return page, links

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

def get_videos(soup, path):
    page, links = get_page_links(soup, 'show_video_list', path=path)
    for page_link in links:
        yield page_link

    if page is None or page == 1:
        featured_video = soup.find('div', 'video')
        if featured_video:
            featured_entry_id = featured_video['data-videoid']
            title = featured_video['data-title']
            duration_str = featured_video.find_next('span', 'duration').string
            featured_date = featured_video.find_previous('p', 'featured-date')
            if featured_date is not None:
                date_str = ' '.join(featured_date.string.replace(u'\xa0', u' ').split()[2:5])
                yield video_item(featured_entry_id, title, date_str, duration_str=duration_str)

    for card in soup(class_='card'):
        entry_id = ENTRY_ID_RE.search(card.a['style']).group(1)
        title = card.find('span', 'video-title').contents[0]
        duration_str = card.find('span', 'duration').string
        date_str = card.find('em', 'video-date').string

        yield video_item(entry_id, title, date_str, duration_str=duration_str)

    form_data['viewstate'] = get_viewstate(soup)

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

def get_search_result_videos(soup, query):
    page, links = get_page_links(soup, 'search_result', query=query)
    for page_link in links:
        yield page_link

    for card in soup(class_='card'):
        entry_id = ENTRY_ID_RE.search(card.a['style']).group(1)
        title = card.parent.find('h3').text
        date_str = " ".join(card.parent.find('span', 'date').text.split()[-4:-1])
        yield video_item(entry_id, title, date_str, date_format="%d %b %Y")

    form_data['viewstate'] = get_viewstate(soup)

def get_stadium_cams():
    soup = get_soup(urljoin(HOST, "/new-scheme/stadium-tv/"))
    js = requests.get(urljoin(HOST, "/components/js/stadium-tv.js")).text
    entry_ids = re.findall('"entry_id":\s+"(\w+)"', js)
    for entry_id, video in zip(entry_ids, soup('div', 'video-new')):
        title = video.find_previous('h2').get_text().strip()
        yield title, entry_id

def get_stadium_index():
    for title, entry_id in get_stadium_cams():
        yield {'label': title,
               'path': plugin.url_for('play_video', entry_id=entry_id),
               'is_playable': True}

    yield {'label': plugin.get_string(30019),
           'path': plugin.url_for('show_playlist', playlist_id='0_n8hezta2')}

def get_categories(path):
    yield {'label': "[B]{}[/B]".format(plugin.get_string(30010)),
           'path': plugin.url_for('show_video_list', path=path)}

    yield {'label': plugin.get_string(30017),
           'path': plugin.url_for('show_stadium_index'),
           'thumbnail': STADIUM_THUMB}

    url = urljoin(HOST, path)
    soup = get_soup(url)
    for a in soup.find('map', id='inside-nav')('a'):
        title = a['title']
        if title in ('Spurs TV Help',
                     'IPB Broadcasters'):
            continue

        href = a['href'].strip('/')
        playable = False
        if title == "Ledley King Testimonial":
            plugin_path = plugin.url_for('show_playlist', playlist_id='0_2nmzot3u')
        elif title == "The Vault":
            plugin_path = plugin.url_for('show_playlist', playlist_id='0_32nxk7s7')
        elif title == "A Question of Spurs":
            playable = True
            plugin_path = plugin.url_for('play_video', entry_id='0_52u0px90')
        elif title == "Live Audio Commentary":
            playable = True
            plugin_path = plugin.url_for('play_video', entry_id='0_7nqzdt52')
        elif 'children' in a.parent['class']:
            plugin_path = plugin.url_for('show_subcategories', path=href)
        else:
            plugin_path = plugin.url_for('show_video_list', path=href)

        yield {'label': title,
               'path': plugin_path,
               'is_playable': playable,
               'thumbnail': THUMBS.get(title)}

def get_subcategories(path):
    yield {'label': plugin.get_string(30014), 'path': plugin.url_for('show_video_list', path=path)}

    url = urljoin(HOST, path)
    soup = get_soup(url)
    for li in soup.find('li', 'active')('li'):
        yield {'label': li.a['title'],
               'path': plugin.url_for('show_video_list', path=li.a['href'].strip('/'))}


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



@plugin.route('/')
def show_index():
    try:
        youtube_icon = Plugin(addon_id="plugin.video.youtube").addon.getAddonInfo('icon')
    except:
        youtube_icon = None

    categories = list(get_categories("spurs-tv"))

    search = {'label': "[B]{}[/B]".format(plugin.get_string(30011)),
              'path': plugin.url_for('search')}
    categories.insert(1, search)

    youtube = {'label': "[B]{}[/B]".format(plugin.get_string(30001)),
               'thumbnail': youtube_icon,
               'path': plugin.url_for('show_youtube_index')}
    categories.append(youtube)

    return categories

@plugin.cached_route('/path/<path>')
def show_categories(path):
    return list(get_categories(path))

@plugin.cached_route('/path/<path>/subcategories')
def show_subcategories(path):
    return list(get_subcategories(path))

@plugin.cached_route('/stadium')
def show_stadium_index():
    return list(get_stadium_index())

@plugin.route('/videos/path/<path>')
def show_video_list(path):
    url = urljoin(BASE_URL, path)
    if 'navigate' in plugin.request.args:
        navigate = plugin.request.args['navigate'][0]
        viewstate = form_data['viewstate']
        field = form_data['field']
        data = {"{}${}".format(field, navigate): '',
                '__VIEWSTATE': viewstate}
        soup = get_soup(url, data)
        update_listing = True
    else:
        soup = get_soup(url)
        update_listing = False

    return plugin.finish(get_videos(soup, path),
                         sort_methods=['unsorted', 'date', 'duration', 'title'],
                         update_listing=update_listing)

@plugin.route('/playlist/<playlist_id>')
def show_playlist(playlist_id):
    return plugin.finish(get_playlist_videos(playlist_id),
                         sort_methods=['unsorted', 'date', 'duration', 'title'])

@plugin.route('/search')
def search():
    query = plugin.keyboard(heading=plugin.get_string(30011))
    if query:
        url = plugin.url_for('search_result', query=query, page=1)
        plugin.redirect(url)

@plugin.route('/search/<query>')
def search_result(query):
    search_data = {FIELD_NAME_ROOT_FMT.format(0) + "drpTaxonomyCategoriesFilter": '144',
                   FIELD_NAME_ROOT_FMT.format(0) + "hdSearchTerm": query}

    if 'navigate' in plugin.request.args:
        navigate = plugin.request.args['navigate'][0]
        search_data[SEARCH_NAV_FMT.format(navigate)] = ''
        viewstate = form_data['viewstate']
        update_listing = True
    else:
        soup = get_soup(SEARCH_URL)
        viewstate = get_viewstate(soup)
        update_listing = False

    search_data['__VIEWSTATE'] = viewstate

    soup = get_soup(SEARCH_URL, search_data)

    return plugin.finish(get_search_result_videos(soup, query),
                         sort_methods=['unsorted', 'date', 'title'])

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
