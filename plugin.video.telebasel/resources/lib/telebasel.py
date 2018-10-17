# -*- coding: utf-8 -*-

# Copyright (C) 2018 Alexander Seiler
#
#
# This file is part of plugin.video.telebasel.
#
# plugin.video.telebasel is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# plugin.video.telebasel is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with plugin.video.telebasel.
# If not, see <http://www.gnu.org/licenses/>.

import sys
import re
import traceback

import datetime
import json
import socket
import urllib2
import urllib
import urlparse

try:
    from multiprocessing.dummy import Pool as ThreadPool
    ENABLE_POOL = True
except ImportError:
    ENABLE_POOL = False

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

import feedparser
from bs4 import BeautifulSoup
from simplecache import SimpleCache

try:
    CompatStr = unicode  # Python2
except NameError:
    CompatStr = str  # Python3


def get_boolean_setting(label):
    """
    Retrieve the boolean value of a setting switch.

    Keyword arguments:
    label -- the settings label
    """
    return REAL_SETTINGS.getSetting(label) == 'true'


ADDON_ID = 'plugin.video.telebasel'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON = REAL_SETTINGS.getAddonInfo('icon')
FANART = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE = REAL_SETTINGS.getLocalizedString
PROFILE = xbmc.translatePath(
    REAL_SETTINGS.getAddonInfo('profile')).decode("utf-8")

HOST = 'telebasel.ch'
HOST_URL = 'https://%s' % HOST
TIMEOUT = 30
CONTENT_TYPE = 'videos'
DEBUG = get_boolean_setting('Enable_Debugging')
NUMBER_OF_EPISODES = 20


socket.setdefaulttimeout(TIMEOUT)


# General helper functions:

def log(msg, level=xbmc.LOGDEBUG):
    """
    Logs a message using Kodi's logging interface.

    Keyword arguments:
    msg   -- the message to log
    level -- the logging level
    """
    if isinstance(msg, str):
        msg = msg.decode('utf-8')
    if DEBUG:
        if level == xbmc.LOGERROR:
            msg += ' ,' + traceback.format_exc()
    message = ADDON_ID + '-' + ADDON_VERSION + '-' + msg
    xbmc.log(msg=message.encode('utf-8'), level=level)


def get_params():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))


def get_duration(duration_string):
    """
    Converts a duration string into an integer respresenting the
    total duration in seconds. There are three possible input string
    forms possible, either
    <hours>:<minutes>:<seconds>
    or
    <minutes>:<seconds>
    or
    <seconds>
    In case of failure a NoneType will be returned.

    Keyword arguments:
    duration_string -- a string of the above form.
    """
    if not isinstance(duration_string, CompatStr):
        return None
    durrex = r'(((?P<hour>\d+):)?(?P<minute>\d+):)?(?P<second>\d+)'
    match = re.match(durrex, duration_string)
    if match:
        hour = int(match.group('hour')) if match.group('hour') else 0
        minute = int(match.group('minute')) if match.group('minute') else 0
        second = int(match.group('second'))
        return 60 * 60 * hour + 60 * minute + second
    log('Cannot convert duration string: %s' % duration_string)
    return None


class Telebasel(object):
    def __init__(self):
        log('__init__')
        self.cache = SimpleCache()

    @staticmethod
    def build_url(mode=None, name=None, url=None, page_hash=None, page=None):
        """Build a URL for this Kodi plugin.

        Keyword arguments:
        mode      -- an integer representing the mode
        name      -- a string containing some information, e.g. a video id
        url       -- a plugin URL, if another plugin/script needs to called
        page_hash -- a string (used to get additional videos through the API)
        page      -- an integer used to indicate the current page in
                     the list of items
        """
        if mode:
            mode = str(mode)
        if page:
            page = str(page)
        added = False
        queries = (url, mode, name, page_hash, page)
        query_names = ('url', 'mode', 'name', 'page_hash', 'page')
        purl = sys.argv[0]
        for query, qname in zip(queries, query_names):
            if query:
                add = '?' if not added else '&'
                purl += '%s%s=%s' % (add, qname, urllib.quote_plus(query))
                added = True
        return purl

    def open_url(self, url, use_cache=True):
        """Open and read the content given by a URL.

        Keyword arguments:
        url       -- the URL to open as a string
        use_cache -- boolean to indicate if the cache provided by the
                     Kodi module SimpleCache should be used (default: True)
        """
        log('open_url, url = ' + str(url))
        try:
            cache_response = None
            if use_cache:
                cache_response = self.cache.get(
                    ADDON_NAME + '.open_url, url = %s' % url)
            if not cache_response:
                request = urllib2.Request(url)
                request.add_header(
                    'User-Agent',
                    ('Mozilla/5.0 (X11; Linux x86_64; rv:59.0)'
                     'Gecko/20100101 Firefox/59.0'))
                response = urllib2.urlopen(request, timeout=TIMEOUT).read()
                self.cache.set(
                    ADDON_NAME + '.open_url, url = %s' % url,
                    response,
                    expiration=datetime.timedelta(hours=2))
            return self.cache.get(ADDON_NAME + '.open_url, url = %s' % url)
        except urllib2.URLError as err:
            log("openURL Failed! " + str(err), xbmc.LOGERROR)
        except socket.timeout as err:
            log("openURL Failed! " + str(err), xbmc.LOGERROR)
        except Exception as err:
            log("openURL Failed! " + str(err), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(
                ADDON_NAME, LANGUAGE(30100), ICON, 4000)
            return ''

    def build_main_menu(self):
        """
        Builds the main menu of the plugin:

        All shows
        Newest shows
        Live TV
        """
        log('build_main_menu')
        main_menu_list = [
            {
                # All shows
                'name': LANGUAGE(30050),
                'mode': 10,
                'isFolder': True,
                'displayItem': True,
            }, {
                # Newest shows
                'name': LANGUAGE(30051),
                'mode': 11,
                'isFolder': True,
                'displayItem': True,
            }, {
                # Live TV
                'name': LANGUAGE(30072),
                'mode': 12,
                'isFolder': True,
                'displayItem': True,
            },
        ]
        for menu_item in main_menu_list:
            if menu_item['displayItem']:
                list_item = xbmcgui.ListItem(menu_item['name'])
                list_item.setProperty('IsPlayable', 'false')
                list_item.setArt({'thumb': ICON})
                purl = self.build_url(
                    mode=menu_item['mode'], name=menu_item['name'])
                xbmcplugin.addDirectoryItem(
                    handle=int(sys.argv[1]), url=purl,
                    listitem=list_item, isFolder=menu_item['isFolder'])

    def retrieve_shows(self):
        """
        Retrieve basic infos about the available shows from the website.
        It returns a list of dictionaries with the keys
        'title', 'page', 'image'.
        """
        log('retrieve_shows')
        url = HOST_URL + '/mediathek'
        url_result = self.open_url(url, use_cache=True)
        soup = BeautifulSoup(url_result, 'html.parser')
        shows_soup = soup.find_all('a', {'class': 'tb-a-unstyled'})

        shows = []
        image_regex = r'background-image\s*:\s*url\(\'(?P<url>.+)\''
        for ssoup in shows_soup:
            page = ssoup.attrs['href']
            m = re.search(image_regex, str(ssoup))
            image_url = m.group('url')

            filename = image_url.split('/')[-1]
            filename_regex = r'(?P<trunk>.+)-\d+x\d+\.(?P<ext>.+)'
            match = re.match(filename_regex, filename)
            if match:
                trunk = match.group('trunk')
                ext = match.group('ext')
                image_url = '/'.join(
                    image_url.split('/')[:-1]) + '/' + trunk + '.' + ext

            title = ssoup.h2.text

            # The element 'Telebasel Archiv' refers to the old
            # website. We need to skip this:
            if 'Archiv' in title:
                continue

            shows.append({'title': title, 'page': page, 'image': image_url})

        return shows

    def extract_channel_id(self, feed_url):
        """
        Extracts the channel id from a podcast feed.

        Keyword arguments:
        feed_url  -- the URL of the podcast feed
        """
        log('extract_channel_id, feed_url = %s' % feed_url)
        feed = self.open_url(feed_url)
        channel_id_regex = r'channels\s*:\s*(?P<id>\d+)'
        match = re.search(channel_id_regex, feed)
        return match.group('id')

    def build_all_shows_menu(self):
        """
        Builds a list of folders containing the names of all the current
        shows.
        """
        log('build_all_shows_menu')
        shows = self.retrieve_shows()
        list_items = []
        for show in shows:
            list_item = xbmcgui.ListItem(label=show['title'])
            list_item.setProperty('IsPlayable', 'false')
            list_item.setArt({
                'thumb': show['image'],
                'poster': show['image'],
            })
            surl = self.build_url(mode=20, name=show['page'])
            list_items.append((surl, list_item, True))
        xbmcplugin.addDirectoryItems(
            int(sys.argv[1]), list_items, totalItems=len(list_items))

    def build_newest_shows_menu(self):
        """
        Builds the menu containing the most recent episodes.
        """
        log('build_newest_shows_menu, ENABLE_POOL=%s' % ENABLE_POOL)
        shows = self.retrieve_shows()
        show_pages = [x['page'] + '&podcast' for x in shows]

        episodes = []
        if ENABLE_POOL:
            n_threads = 10 if (len(show_pages) > 0) else len(show_pages)
            pool = ThreadPool(n_threads)
            result = pool.map(self.parse_feed, show_pages)
            pool.close()
            pool.join()
            for res in result:
                episodes += res
        else:
            for show_page in show_pages:
                episodes += self.parse_feed(show_page)

        sorted_episodes = sorted(
            episodes, key=lambda k: k['date'], reverse=True)
        reduced_sorted_episodes = sorted_episodes[:NUMBER_OF_EPISODES]

        for entry in reduced_sorted_episodes:
            self.add_video_item(entry)

    def play_livestream(self):
        """
        Plays the livestream.
        """
        json_url = ('https://player.cdn.tv1.eu/player/macros/_v_/'
                    '_s_defaultPlayerLiveSkin/_x_s-510394368_w-2685009931'
                    '/pl/data/playlist_html.json'
                    '?playout=hls&noflash=true&theov=2.30.9&phase=20')
        content = json.loads(self.open_url(json_url, use_cache=False))
        playlist_url = content['pl']['entries'][0]['video']['src']
        play_item = xbmcgui.ListItem('Telebasel Live', path=playlist_url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, play_item)

    def parse_feed(self, feed_url):
        """
        Parses a podcast feed and returns a list containing
        the episode information.

        Keyword arguments:
        feed_url  -- the URL of the podcast feed
        """
        log('parse_feed, feed_url = %s' % feed_url)
        feed = feedparser.parse(feed_url)
        try:
            show_image = feed['feed']['image']['href']
        except Exception:
            log('parse_feed: Unable to get show image from feed %s' % feed_url)
            show_image = ''

        entries = []
        for entry in feed.entries:
            title = entry.get('title')
            description = entry.get('description')
            podcast_url = entry.get('link')
            duration_string = entry.get('itunes_duration')
            duration = get_duration(duration_string)
            date_parsed = entry.get('published_parsed')
            try:
                aired = '%s-%s-%s' % (str(date_parsed.tm_year),
                                      str(date_parsed.tm_mon).zfill(2),
                                      str(date_parsed.tm_mday).zfill(2))
            except Exception:
                log('parse_feed: Unable to get the date for '
                    'episode %s from feed %s' % (title, feed_url))
                aired = ''
            try:
                image = entry.get('image')['href']
            except Exception:
                log('parse_feed: Unable to get the image '
                    'for episode %s from feed %s' % (title, feed_url))
                image = ''

            item = {
                'title': title,
                'description': description,
                'image': image,
                'podcast_url': podcast_url,
                'duration': duration,
                'aired': aired,
                'date': date_parsed,
                'show_image': show_image,
            }
            vid_regex = r'.+/(?P<cid>\d+)/(?P<aid>\d+)/(?P<vid>\d+)/.+'
            match_link = re.match(vid_regex, podcast_url)

            guid = entry.get('guid')
            match_guid = re.match(vid_regex, guid)

            match_image = re.match(vid_regex, image)

            match = match_guid or match_link or match_image
            if match:
                cid = match.group('cid')
                aid = match.group('aid')
                vid = match.group('vid')
                playlist_url = ('https://video.%s/content/'
                                '%s/%s/%s/index.m3u8' % (HOST, cid, aid, vid))
                item['playlist_url'] = playlist_url
            entries.append(item)

        return entries

    def build_show_menu(self, surl):
        """
        Builds a list of videos for a show given by its show URL.

        Keyword arguments:
        surl  -- the URL of the show
        """
        podcast_url = surl + '&podcast'
        entries = self.parse_feed(podcast_url)
        for entry in entries:
            self.add_video_item(entry)

    def add_video_item(self, entry):
        """
        Adds a playlist entry to the Kodi menu.

        Keyword argmuments:
        entry  -- a dictionary containing the necessary information
        """
        log('add_video_item, title = %s' % entry.get('title'))
        list_item = xbmcgui.ListItem(label=entry['title'])
        list_item.setProperty('IsPlayable', 'true')
        list_item.setArt({
            'thumb': entry['image'],
            'poster': entry['image'],
            'banner': entry['show_image']
        })
        list_item.setInfo(
            'video',
            {
                'title': entry['title'],
                'plot': entry['description'],
                'aired': entry['aired'],
                'duration': entry['duration'],
            }
        )
        video = entry.get('playlist_url') or entry['podcast_url']
        url = self.build_url(mode=50, name=video)
        xbmcplugin.addDirectoryItem(
            int(sys.argv[1]), url, list_item, isFolder=False)

    def build_live_menu(self):
        """
        Builds the live TV menu.
        """
        log('build_live_menu')
        list_item = xbmcgui.ListItem(label=LANGUAGE(30074))
        list_item.setProperty('IsPlayable', 'true')
        list_item.setArt({
            'thumb': ICON,
        })
        url = self.build_url(mode=51)
        xbmcplugin.addDirectoryItem(
            int(sys.argv[1]), url, list_item, isFolder=False)

    def play_video(self, video_url):
        """
        Plays a video.

        Keyword arguments:
        video_url  -- the URL of the video to play
        """
        log('play_video, video_url=%s' % video_url)
        play_item = xbmcgui.ListItem('Telebasel Video', path=video_url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, play_item)


def run():
    """
    Run the plugin.
    """
    params = get_params()
    try:
        url = urllib.unquote_plus(params["url"])
    except Exception:
        url = None
    try:
        name = urllib.unquote_plus(params["name"])
    except Exception:
        name = None
    try:
        mode = int(params["mode"])
    except Exception:
        mode = None

    log("Mode: "+str(mode))
    log("URL : "+str(url))
    log("Name: "+str(name))

    if mode is None:
        Telebasel().build_main_menu()
    elif mode == 10:
        Telebasel().build_all_shows_menu()
    elif mode == 11:
        Telebasel().build_newest_shows_menu()
    elif mode == 12:
        Telebasel().build_live_menu()
    elif mode == 20:
        Telebasel().build_show_menu(name)
    elif mode == 50:
        Telebasel().play_video(name)
    elif mode == 51:
        Telebasel().play_livestream()

    xbmcplugin.setContent(int(sys.argv[1]), CONTENT_TYPE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)
