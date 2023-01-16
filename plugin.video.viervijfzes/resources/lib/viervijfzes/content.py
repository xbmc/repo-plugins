# -*- coding: utf-8 -*-
""" AUTH API """

from __future__ import absolute_import, division, unicode_literals

import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime

import requests

from resources.lib.kodiutils import STREAM_DASH, STREAM_HLS, html_to_kodi
from resources.lib.viervijfzes import ResolvedStream

try:  # Python 3
    from html import unescape
except ImportError:  # Python 2
    from HTMLParser import HTMLParser

    unescape = HTMLParser().unescape

_LOGGER = logging.getLogger(__name__)

CACHE_AUTO = 1  # Allow to use the cache, and query the API if no cache is available
CACHE_ONLY = 2  # Only use the cache, don't use the API
CACHE_PREVENT = 3  # Don't use the cache


class UnavailableException(Exception):
    """ Is thrown when an item is unavailable. """


class NoContentException(Exception):
    """ Is thrown when no items are unavailable. """


class GeoblockedException(Exception):
    """ Is thrown when a geoblocked item is played. """


class Program:
    """ Defines a Program. """

    def __init__(self, uuid=None, path=None, channel=None, title=None, description=None, aired=None, poster=None, thumb=None, fanart=None, seasons=None,
                 episodes=None,
                 clips=None, my_list=False):
        """
        :type uuid: str
        :type path: str
        :type channel: str
        :type title: str
        :type description: str
        :type aired: datetime
        :type poster: str
        :type thumb: str
        :type fanart: str
        :type seasons: list[Season]
        :type episodes: list[Episode]
        :type clips: list[Episode]
        :type my_list: bool
        """
        self.uuid = uuid
        self.path = path
        self.channel = channel
        self.title = title
        self.description = description
        self.aired = aired
        self.poster = poster
        self.thumb = thumb
        self.fanart = fanart
        self.seasons = seasons
        self.episodes = episodes
        self.clips = clips
        self.my_list = my_list

    def __repr__(self):
        return "%r" % self.__dict__


class Season:
    """ Defines a Season. """

    def __init__(self, uuid=None, path=None, channel=None, title=None, description=None, number=None):
        """
        :type uuid: str
        :type path: str
        :type channel: str
        :type title: str
        :type description: str
        :type number: int

        """
        self.uuid = uuid
        self.path = path
        self.channel = channel
        self.title = title
        self.description = description
        self.number = number

    def __repr__(self):
        return "%r" % self.__dict__


class Episode:
    """ Defines an Episode. """

    def __init__(self, uuid=None, nodeid=None, path=None, channel=None, program_title=None, title=None, description=None, thumb=None, duration=None,
                 season=None, season_uuid=None, number=None, rating=None, aired=None, expiry=None, stream=None, islongform=False):
        """
        :type uuid: str
        :type nodeid: str
        :type path: str
        :type channel: str
        :type program_title: str
        :type title: str
        :type description: str
        :type thumb: str
        :type duration: int
        :type season: int
        :type season_uuid: str
        :type number: int
        :type rating: str
        :type aired: datetime
        :type expiry: datetime
        :type stream: string
        :type islongform: bool
        """
        self.uuid = uuid
        self.nodeid = nodeid
        self.path = path
        self.channel = channel
        self.program_title = program_title
        self.title = title
        self.description = description
        self.thumb = thumb
        self.duration = duration
        self.season = season
        self.season_uuid = season_uuid
        self.number = number
        self.rating = rating
        self.aired = aired
        self.expiry = expiry
        self.stream = stream
        self.islongform = islongform

    def __repr__(self):
        return "%r" % self.__dict__


class Category:
    """ Defines a Category. """

    def __init__(self, uuid=None, channel=None, title=None, programs=None, episodes=None):
        """
        :type uuid: str
        :type channel: str
        :type title: str
        :type programs: List[Program]
        :type episodes: List[Episode]
        """
        self.uuid = uuid
        self.channel = channel
        self.title = title
        self.programs = programs
        self.episodes = episodes

    def __repr__(self):
        return "%r" % self.__dict__


class ContentApi:
    """ GoPlay Content API"""
    SITE_URL = 'https://www.goplay.be'
    API_GOPLAY = 'https://api.goplay.be'

    def __init__(self, auth=None, cache_path=None):
        """ Initialise object """
        self._session = requests.session()
        self._auth = auth
        self._cache_path = cache_path

    def get_programs(self, channel=None, cache=CACHE_AUTO):
        """ Get a list of all programs of the specified channel.
        :type channel: str
        :type cache: str
        :rtype list[Program]
        """

        def update():
            """ Fetch the program listing by scraping """
            # Load webpage
            raw_html = self._get_url(self.SITE_URL + '/programmas')

            # Parse programs
            regex_programs = re.compile(r'data-program="(?P<json>[^"]+)"', re.DOTALL)

            data = [
                json.loads(unescape(item.group('json')))
                for item in regex_programs.finditer(raw_html)
            ]

            if not data:
                raise Exception('No programs found')

            return data

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['programs'], cache_mode=cache, update=update, ttl=30 * 60)  # 30 minutes
        if not data:
            return []

        if channel:
            programs = [
                self._parse_program_data(record) for record in data if record['pageInfo']['brand'] == channel
            ]
        else:
            programs = [
                self._parse_program_data(record) for record in data
            ]

        return programs

    def get_program(self, path, extract_clips=False, cache=CACHE_AUTO):
        """ Get a Program object from the specified page.
        :type path: str
        :type extract_clips: bool
        :type cache: int
        :rtype Program
        """
        # We want to use the html to extract clips
        # This is the worst hack, since Python 2.7 doesn't support nonlocal
        raw_html = [None]

        def update():
            """ Fetch the program metadata by scraping """
            # Fetch webpage
            page = self._get_url(self.SITE_URL + '/' + path)

            # Store a copy in the parent's raw_html var.
            raw_html[0] = page

            # Extract JSON
            regex_program = re.compile(r'data-hero="([^"]+)', re.DOTALL)
            json_data = unescape(regex_program.search(page).group(1))
            data = json.loads(json_data)['data']

            return data

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['program', path], cache_mode=cache, update=update)
        if not data:
            return None

        program = self._parse_program_data(data)

        # Also extract clips if we did a real HTTP call
        if extract_clips and raw_html[0]:
            clips = self._extract_videos(raw_html[0])
            program.clips = clips

        return program

    def get_program_by_uuid(self, uuid, cache=CACHE_AUTO):
        """ Get a Program object with the specified uuid.
        :type uuid: str
        :type cache: str
        :rtype Program
        """
        if not uuid:
            return None

        def update():
            """ Fetch the program metadata """
            # Fetch webpage
            result = self._get_url(self.SITE_URL + '/api/program/%s' % uuid)
            data = json.loads(result)
            return data

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['program', uuid], cache_mode=cache, update=update)
        if not data:
            return None

        program = self._parse_program_data(data)

        return program

    def get_episode(self, path, cache=CACHE_AUTO):
        """ Get a Episode object from the specified page.
        :type path: str
        :type cache: str
        :rtype Episode
        """

        def update():
            """ Fetch the program metadata by scraping """
            # Load webpage
            page = self._get_url(self.SITE_URL + '/' + path)

            program_json = None
            episode_json = None

            # Extract video JSON by looking for a data-video tag
            # This is not present on every page
            regex_video_data = re.compile(r'data-video="([^"]+)"', re.DOTALL)
            result = regex_video_data.search(page)
            if result:
                video_id = json.loads(unescape(result.group(1)))['id']
                video_json_data = self._get_url('%s/web/v1/videos/short-form/%s' % (self.API_GOPLAY, video_id))
                video_json = json.loads(video_json_data)
                return dict(video=video_json)

            # Extract program JSON
            regex_program = re.compile(r'data-hero="([^"]+)', re.DOTALL)
            result = regex_program.search(page)
            if result:
                program_json_data = unescape(result.group(1))
                program_json = json.loads(program_json_data)['data']

            # Extract episode JSON
            regex_episode = re.compile(r'<script type="application/json" data-drupal-selector="drupal-settings-json">(.*?)</script>', re.DOTALL)
            result = regex_episode.search(page)
            if result:
                episode_json_data = unescape(result.group(1))
                episode_json = json.loads(episode_json_data)

            return dict(program=program_json, episode=episode_json)

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['episode', path], cache_mode=cache, update=update)
        if not data:
            return None

        if 'video' in data and data['video']:
            # We have found detailed episode information
            episode = self._parse_clip_data(data['video'])
            return episode

        if 'program' in data and 'episode' in data and data['program'] and data['episode']:
            # We don't have detailed episode information
            # We need to lookup the episode in the program JSON
            program = self._parse_program_data(data['program'])
            for episode in program.episodes:
                if episode.nodeid == data['episode']['pageInfo']['nodeId']:
                    return episode

        return None

    def get_stream_by_uuid(self, uuid, islongform):
        """ Get the stream URL to use for this video.
        :type uuid: str
        :type islongform: bool
        :rtype str
        """
        mode = 'long-form' if islongform else 'short-form'
        response = self._get_url(self.API_GOPLAY + '/web/v1/videos/%s/%s' % (mode, uuid), authentication='Bearer %s' % self._auth.get_token())
        data = json.loads(response)

        if not data:
            raise UnavailableException

        if data.get('manifestUrls'):

            if data.get('drmXml'):
                # DRM protected stream
                # See https://docs.unified-streaming.com/documentation/drm/buydrm.html#setting-up-the-client

                # DRM protected DASH stream
                return ResolvedStream(
                    uuid=uuid,
                    url=data['manifestUrls']['dash'],
                    stream_type=STREAM_DASH,
                    license_url='https://wv-keyos.licensekeyserver.com/',
                    auth=data['drmXml'],
                )

            if data.get('manifestUrls').get('dash'):
                # Unprotected DASH stream
                return ResolvedStream(
                    uuid=uuid,
                    url=data['manifestUrls']['dash'],
                    stream_type=STREAM_DASH,
                )

            # Unprotected HLS stream
            return ResolvedStream(
                uuid=uuid,
                url=data['manifestUrls']['hls'],
                stream_type=STREAM_HLS,
            )

        # No manifest url found, get manifest from Server-Side Ad Insertion service
        if data.get('adType') == 'SSAI' and data.get('ssai'):
            url = 'https://pubads.g.doubleclick.net/ondemand/dash/content/%s/vid/%s/streams' % (data.get('ssai').get('contentSourceID'), data.get('ssai').get('videoID'))
            ad_data = json.loads(self._post_url(url, data=''))

            # Unprotected DASH stream
            return ResolvedStream(
                uuid=uuid,
                url=ad_data['stream_manifest'],
                stream_type=STREAM_DASH,
            )

        raise UnavailableException


    def get_program_tree(self, cache=CACHE_AUTO):
        """ Get a content tree with information about all the programs.
        :type cache: str
        :rtype dict
        """

        def update():
            """ Fetch the content tree """
            response = self._get_url(self.SITE_URL + '/api/content_tree')
            return json.loads(response)

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['content_tree'], cache_mode=cache, update=update, ttl=5 * 60)  # 5 minutes

        return data

    def get_popular_programs(self, brand=None):
        """ Get a list of popular programs.
        :rtype list[Program]
        """
        if brand:
            response = self._get_url(self.SITE_URL + '/api/programs/popular/%s' % brand)
        else:
            response = self._get_url(self.SITE_URL + '/api/programs/popular')
        data = json.loads(response)

        programs = []
        for program in data:
            programs.append(self._parse_program_data(program))

        return programs

    def get_categories(self):
        """ Return a list of categories.
        :rtype list[Category]
        """
        content_tree = self.get_program_tree()

        categories = []
        for category_id, category_name in content_tree.get('categories').items():
            categories.append(Category(uuid=category_id,
                                       title=category_name))

        return categories

    def get_category_content(self, category_id):
        """ Return a category.
        :type category_id: int
        :rtype list[Program]
        """
        content_tree = self.get_program_tree()

        # Find out all the program_id's of the requested category
        program_ids = [key for key, value in content_tree.get('programs').items() if value.get('category') == category_id]

        # Filter out the list of all programs to only keep the one of the requested category
        return [program for program in self.get_programs() if program.uuid in program_ids]

    def get_recommendation_categories(self):
        """ Get a list of all categories.
        :rtype list[Category]
        """
        # Load all programs
        all_programs = self.get_programs()

        # Load webpage
        raw_html = self._get_url(self.SITE_URL)

        # Categories regexes
        regex_articles = re.compile(r'<article[^>]+>(.*?)</article>', re.DOTALL)
        regex_category = re.compile(r'<h2.*?>(.*?)</h2>(?:.*?<div class="visually-hidden">(.*?)</div>)?', re.DOTALL)

        categories = []
        for result in regex_articles.finditer(raw_html):
            article_html = result.group(1)

            match_category = regex_category.search(article_html)
            category_title = None
            if match_category:
                category_title = match_category.group(1).strip()
                if match_category.group(2):
                    category_title += ' [B]%s[/B]' % match_category.group(2).strip()

            if category_title:
                # Extract programs and lookup in all_programs so we have more metadata
                programs = []
                for program in self._extract_programs(article_html):
                    try:
                        rich_program = next(rich_program for rich_program in all_programs if rich_program.path == program.path)
                        programs.append(rich_program)
                    except StopIteration:
                        programs.append(program)

                episodes = self._extract_videos(article_html)

                categories.append(
                    Category(uuid=hashlib.md5(category_title.encode('utf-8')).hexdigest(), title=category_title, programs=programs, episodes=episodes))

        return categories

    def get_mylist(self):
        """ Get the content of My List
        :rtype list[Program]
        """
        data = self._get_url(self.API_GOPLAY + '/my-list', authentication='Bearer %s' % self._auth.get_token())
        result = json.loads(data)

        items = []
        for item in result:
            try:
                program = self.get_program_by_uuid(item.get('programId'))
                if program:
                    program.my_list = True
                    items.append(program)
            except Exception as exc:  # pylint: disable=broad-except
                _LOGGER.warning(exc)

        return items

    def mylist_add(self, program_id):
        """ Add a program on My List """
        self._post_url(self.API_GOPLAY + '/my-list', data={'programId': program_id}, authentication='Bearer %s' % self._auth.get_token())

    def mylist_del(self, program_id):
        """ Remove a program on My List """
        self._delete_url(self.API_GOPLAY + '/my-list-item', params={'programId': program_id}, authentication='Bearer %s' % self._auth.get_token())

    @staticmethod
    def _extract_programs(html):
        """ Extract Programs from HTML code
        :type html: str
        :rtype list[Program]
        """
        # Item regexes
        regex_item = re.compile(r'<a[^>]+?href="(?P<path>[^"]+)"[^>]+?>'
                                r'.*?<h3 class="poster-teaser__title">(?P<title>[^<]*)</h3>.*?data-background-image="(?P<image>.*?)".*?'
                                r'</a>', re.DOTALL)

        # Extract items
        programs = []
        for item in regex_item.finditer(html):
            path = item.group('path')
            if path.startswith('/video'):
                continue

            # Program
            programs.append(Program(
                path=path.lstrip('/'),
                title=unescape(item.group('title')),
                poster=unescape(item.group('image')),
            ))

        return programs

    @staticmethod
    def _extract_videos(html):
        """ Extract videos from HTML code
        :type html: str
        :rtype list[Episode]
        """
        # Item regexes
        regex_item = re.compile(r'<a[^>]+?href="(?P<path>[^"]+)"[^>]+?>.*?</a>', re.DOTALL)

        regex_episode_program = re.compile(r'<h3 class="episode-teaser__subtitle">([^<]*)</h3>')
        regex_episode_title = re.compile(r'<(?:div|h3) class="(?:poster|card|image|episode)-teaser__title">(?:<span>)?([^<]*)(?:</span>)?</(?:div|h3)>')
        regex_episode_duration = re.compile(r'data-duration="([^"]*)"')
        regex_episode_video_id = re.compile(r'data-video-id="([^"]*)"')
        regex_episode_image = re.compile(r'data-background-image="([^"]*)"')
        regex_episode_badge = re.compile(r'<div class="(?:poster|card|image|episode)-teaser__badge badge">([^<]*)</div>')

        # Extract items
        episodes = []
        for item in regex_item.finditer(html):
            item_html = item.group(0)
            path = item.group('path')

            # Extract title
            try:
                title = unescape(regex_episode_title.search(item_html).group(1))
            except AttributeError:
                continue

            # This is not a video
            if not path.startswith('/video'):
                continue

            try:
                episode_program = regex_episode_program.search(item_html).group(1)
            except AttributeError:
                _LOGGER.warning('Found no episode_program for %s', title)
                episode_program = None

            try:
                episode_duration = int(regex_episode_duration.search(item_html).group(1))
            except AttributeError:
                _LOGGER.warning('Found no episode_duration for %s', title)
                episode_duration = None

            try:
                episode_video_id = regex_episode_video_id.search(item_html).group(1)
            except AttributeError:
                _LOGGER.warning('Found no episode_video_id for %s', title)
                episode_video_id = None

            try:
                episode_image = unescape(regex_episode_image.search(item_html).group(1))
            except AttributeError:
                _LOGGER.warning('Found no episode_image for %s', title)
                episode_image = None

            try:
                episode_badge = unescape(regex_episode_badge.search(item_html).group(1))
            except AttributeError:
                episode_badge = None

            description = title
            if episode_badge:
                description += "\n\n[B]%s[/B]" % episode_badge

            # Episode
            episodes.append(Episode(
                path=path.lstrip('/'),
                channel='',  # TODO
                title=title,
                description=html_to_kodi(description),
                duration=episode_duration,
                uuid=episode_video_id,
                thumb=episode_image,
                program_title=episode_program,
            ))

        return episodes

    @staticmethod
    def _parse_program_data(data):
        """ Parse the Program JSON.
        :type data: dict
        :rtype Program
        """
        # Create Program info
        program = Program(
            uuid=data.get('id'),
            path=data.get('link').lstrip('/'),
            channel=data.get('pageInfo').get('brand'),
            title=data.get('title'),
            description=html_to_kodi(data.get('description')),
            aired=datetime.fromtimestamp(data.get('pageInfo', {}).get('publishDate', 0.0)),
            poster=data.get('images').get('poster'),
            thumb=data.get('images').get('teaser'),
            fanart=data.get('images').get('teaser'),
        )

        # Create Season info
        program.seasons = {
            key: Season(
                uuid=playlist.get('id'),
                path=playlist.get('link').lstrip('/'),
                channel=playlist.get('pageInfo').get('brand'),
                title=playlist.get('title'),
                description=html_to_kodi(playlist.get('description')),
                number=playlist.get('episodes')[0].get('seasonNumber'),  # You did not see this
            )
            for key, playlist in enumerate(data.get('playlists', [])) if playlist.get('episodes')
        }

        # Create Episodes info
        program.episodes = [
            ContentApi._parse_episode_data(episode, playlist.get('id'))
            for playlist in data.get('playlists', [])
            for episode in playlist.get('episodes')
        ]

        return program

    @staticmethod
    def _parse_episode_data(data, season_uuid=None):
        """ Parse the Episode JSON.
        :type data: dict
        :type season_uuid: str
        :rtype Episode
        """
        if data.get('episodeNumber'):
            episode_number = data.get('episodeNumber')
        else:
            # The episodeNumber can be absent
            match = re.compile(r'\d+$').search(data.get('title'))
            if match:
                episode_number = match.group(0)
            else:
                episode_number = None

        episode = Episode(
            uuid=data.get('videoUuid'),
            nodeid=data.get('pageInfo', {}).get('nodeId'),
            path=data.get('link').lstrip('/'),
            channel=data.get('pageInfo', {}).get('site'),
            program_title=data.get('program', {}).get('title') if data.get('program') else data.get('title'),
            title=data.get('title'),
            description=html_to_kodi(data.get('description')),
            thumb=data.get('image'),
            duration=data.get('duration'),
            season=data.get('seasonNumber'),
            season_uuid=season_uuid,
            number=episode_number,
            aired=datetime.fromtimestamp(int(data.get('createdDate'))),
            expiry=datetime.fromtimestamp(int(data.get('unpublishDate'))) if data.get('unpublishDate') else None,
            rating=data.get('parentalRating'),
            stream=data.get('path'),
            islongform=data.get('isLongForm'),
        )
        return episode

    @staticmethod
    def _parse_clip_data(data):
        """ Parse the Clip JSON.
        :type data: dict
        :rtype Episode
        """
        episode = Episode(
            uuid=data.get('videoUuid'),
            program_title=data.get('title'),
            title=data.get('title'),
        )
        return episode

    def _get_url(self, url, params=None, authentication=None):
        """ Makes a GET request for the specified URL.
        :type url: str
        :type authentication: str
        :rtype str
        """
        if authentication:
            response = self._session.get(url, params=params, headers={
                'authorization': authentication,
            })
        else:
            response = self._session.get(url, params=params)

        if response.status_code != 200:
            _LOGGER.error(response.text)
            raise Exception('Could not fetch data')

        return response.text

    def _post_url(self, url, params=None, data=None, authentication=None):
        """ Makes a POST request for the specified URL.
        :type url: str
        :type authentication: str
        :rtype str
        """
        if authentication:
            response = self._session.post(url, params=params, json=data, headers={
                'authorization': authentication,
            })
        else:
            response = self._session.post(url, params=params, json=data)

        if response.status_code not in (200, 201):
            _LOGGER.error(response.text)
            raise Exception('Could not fetch data')

        return response.text

    def _delete_url(self, url, params=None, authentication=None):
        """ Makes a DELETE request for the specified URL.
        :type url: str
        :type authentication: str
        :rtype str
        """
        if authentication:
            response = self._session.delete(url, params=params, headers={
                'authorization': authentication,
            })
        else:
            response = self._session.delete(url, params=params)

        if response.status_code != 200:
            _LOGGER.error(response.text)
            raise Exception('Could not fetch data')

        return response.text

    def _handle_cache(self, key, cache_mode, update, ttl=30 * 24 * 60 * 60):
        """ Fetch something from the cache, and update if needed """
        if cache_mode in [CACHE_AUTO, CACHE_ONLY]:
            # Try to fetch from cache
            data = self._get_cache(key)
            if data is None and cache_mode == CACHE_ONLY:
                return None
        else:
            data = None

        if data is None:
            try:
                # Fetch fresh data
                _LOGGER.debug('Fetching fresh data for key %s', '.'.join(key))
                data = update()
                if data:
                    # Store fresh response in cache
                    self._set_cache(key, data, ttl)
            except Exception as exc:  # pylint: disable=broad-except
                _LOGGER.warning('Something went wrong when refreshing live data: %s. Using expired cached values.', exc)
                data = self._get_cache(key, allow_expired=True)

        return data

    def _get_cache(self, key, allow_expired=False):
        """ Get an item from the cache """
        filename = ('.'.join(key) + '.json').replace('/', '_')
        fullpath = os.path.join(self._cache_path, filename)

        if not os.path.exists(fullpath):
            return None

        if not allow_expired and os.stat(fullpath).st_mtime < time.time():
            return None

        with open(fullpath, 'r') as fdesc:
            try:
                _LOGGER.debug('Fetching %s from cache', filename)
                value = json.load(fdesc)
                return value
            except (ValueError, TypeError):
                return None

    def _set_cache(self, key, data, ttl):
        """ Store an item in the cache """
        filename = ('.'.join(key) + '.json').replace('/', '_')
        fullpath = os.path.join(self._cache_path, filename)

        if not os.path.exists(self._cache_path):
            os.makedirs(self._cache_path)

        with open(fullpath, 'w') as fdesc:
            _LOGGER.debug('Storing to cache as %s', filename)
            json.dump(data, fdesc)

        # Set TTL by modifying modification date
        deadline = int(time.time()) + ttl
        os.utime(fullpath, (deadline, deadline))
