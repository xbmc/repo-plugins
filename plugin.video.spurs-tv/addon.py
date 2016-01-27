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

from xbmcswift2 import Plugin, xbmc
from bs4 import BeautifulSoup
import requests
import livestreamer

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
MEDIA_URL_ROOT = urlunparse((MEDIA_SCHEME, MEDIA_HOST, "/p/{0}/".format(PARTNER_ID), None, None, None))

THUMB_URL_FMT = MEDIA_URL_ROOT + "thumbnail/entry_id/{0}/height/720"

HLS_URL_FMT = MEDIA_URL_ROOT + "playManifest/entryId/{0}/format/applehttp"

PLAYLIST_XML_FMT = urlunparse((MEDIA_SCHEME, MEDIA_HOST,
                               "index.php/partnerservices2/executeplaylist?" +
                               "partner_id={0}&playlist_id={{0}}".format(PARTNER_ID), None, None, None))

FIELD_NAME_ROOT_FMT = ("ctl00$ContentPlaceHolder1$DropZoneMainContent$columnDisplay$"
                       "ctl00$controlcolumn$ctl{0:02d}$WidgetHost$WidgetHost_widget$")

PAGINATION_FMT = "Pagination1${0}"

SEARCH_NAV_FMT = FIELD_NAME_ROOT_FMT.format(0) + PAGINATION_FMT


plugin = Plugin()

form_data = plugin.get_storage('form_data')

debug = plugin.get_setting('debug', bool)
def log(msg):
    if debug:
        plugin.log.info(msg)

def get_soup(url, data=None):
    if not url.endswith('/'):
        url += '/'
    if data is not None:
        log("POST {0} {1}".format(url, data))
        response = requests.post(url, data)
    else:
        log("GET {0}".format(url))
        response = requests.get(url)
    return BeautifulSoup(response.text, 'html5lib')

def get_viewstate(soup):
    return soup.find('input', id='__VIEWSTATE')['value']

def get_media_url(entry_id):
    hls_url = 'hlsvariant://' + HLS_URL_FMT.format(entry_id)
    resolution = plugin.get_setting('resolution')
    streams = livestreamer.streams(hls_url, sorting_excludes=[">{0}".format(resolution)])

    media_url = streams['best'].url
    log("Playing URL {0}".format(media_url))
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
            item = {'label': u"[B]<< {0} ({1:d})[/B]".format(plugin.get_string(30013), page - 1),
                    'path': plugin.url_for(endpoint,
                                           navigate='prev',
                                           **kwargs)
                    }
            links.append(item)
      
        if page < npages:
            item = {'label': u"[B]{0} ({1:d}) >>[/B]".format(plugin.get_string(30012), page + 1),
                    'path': plugin.url_for(endpoint,
                                           navigate='next',
                                           **kwargs)
                    }
            links.append(item)

    return page, links
        
def video_item(entry_id, title, date_str, date_format="%d %B %Y", duration_str=None, duration=None):
    item = {'label': title,
            'thumbnail': THUMB_URL_FMT.format(entry_id),
            'path': plugin.url_for('play_video', entry_id=entry_id),
            'is_playable': True}

    video_date = utils.date_from_str(date_str, date_format)
    utils.add_item_info(item, title, video_date)
    
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
            date_str = " ".join(featured_date.string.replace(u'\xa0', u' ').split()[2:5])
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
    xml = requests.get(playlist_url).text
    for entry in BeautifulSoup(xml, 'html5lib').entries:
        entry_id = entry.id.string
        title = entry.find('name').string
        date_str = entry.createdat.string.split()[0]
        yield video_item(entry_id, title, date_str, date_format="%Y-%m-%d",
                         duration=entry.duration.string)

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
        
def get_categories(path):
    yield {'label': "[B]{0}[/B]".format(plugin.get_string(30010)),
           'path': plugin.url_for('show_video_list', path=path)}

    yield {'label': "Stadium TV",
           'path': plugin.url_for('show_playlist', playlist_id='0_n8hezta2')}

    url = urljoin(HOST, path)
    soup = get_soup(url)
    for a in soup.find('map', id='inside-nav')('a'):
        title = a['title']
        if title in ('Spurs TV Help',
                     'IPB Broadcasters'):
            continue

        href = a['href'].strip('/')
        playable = False
        if href.endswith("spurs-tv"):
            plugin_path = plugin.url_for('show_categories', path=href)
        elif title == "Ledley King Testimonial":
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

        yield {'label': title, 'path': plugin_path, 'is_playable': playable}

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
                'path': plugin.url_for('show_youtube_list', playlist=playlist_id)}

        utils.add_item_info(item, title, published_at)

        yield item

def get_youtube_video_items(generator):
    for video_id, title, thumbnail, published_at in generator():
        item = {'label': title,
                'thumbnail': thumbnail,
                'path': "plugin://plugin.video.youtube/play/?video_id={0}".format(video_id),
                'is_playable': True}

        utils.add_item_info(item, title, published_at)

        yield item



@plugin.route('/')
def show_index():
    try:
        youtube_icon = Plugin(addon_id="plugin.video.youtube").addon.getAddonInfo('icon')
    except:
        youtube_icon = None

    categories = list(get_categories("spurs-tv"))

    search = {'label': "[B]{0}[/B]".format(plugin.get_string(30011)),
              'path': plugin.url_for('search')}
    categories.insert(1, search)

    youtube = {'label': "[B]{0}[/B]".format(plugin.get_string(30001)),
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
    
@plugin.route('/videos/path/<path>')
def show_video_list(path):
    url = urljoin(BASE_URL, path)
    if 'navigate' in plugin.request.args:
        navigate = plugin.request.args['navigate'][0]
        viewstate = form_data['viewstate']
        field = form_data['field']
        data = {"{0}${1}".format(field, navigate): '',
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
    plugin.run()
