# -*- coding: utf-8 -*-
""" AUTH API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import os
import re
import time
from datetime import datetime

import requests

from resources.lib import kodiutils
from resources.lib.goplay import ResolvedStream
from resources.lib.kodiutils import STREAM_DASH, STREAM_HLS, html_to_kodi

_LOGGER = logging.getLogger(__name__)

CACHE_AUTO = 1  # Allow to use the cache, and query the API if no cache is available
CACHE_ONLY = 2  # Only use the cache, don't use the API
CACHE_PREVENT = 3  # Don't use the cache

PROXIES = kodiutils.get_proxies()


class UnavailableException(Exception):
    """ Is thrown when an item is unavailable. """


class NoContentException(Exception):
    """ Is thrown when no items are unavailable. """


class GeoblockedException(Exception):
    """ Is thrown when a geoblocked item is played. """


class Program:
    """ Defines a Program. """

    def __init__(self, uuid=None, path=None, channel=None, category_id=None, category_name=None, title=None, description=None, aired=None, expiry=None, poster=None, thumb=None, fanart=None, seasons=None,
                 my_list=False):
        """
        :type uuid: str
        :type path: str
        :type channel: str
        :type category_id: str
        :type category_name: str
        :type title: str
        :type description: str
        :type aired: datetime
        :type expiry: datetime
        :type poster: str
        :type thumb: str
        :type fanart: str
        :type seasons: list[Season]
        :type my_list: bool
        """
        self.uuid = uuid
        self.path = path
        self.channel = channel
        self.category_id = category_id
        self.category_name = category_name
        self.title = title
        self.description = description
        self.aired = aired
        self.expiry = expiry
        self.poster = poster
        self.thumb = thumb
        self.fanart = fanart
        self.seasons = seasons
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
                 position=None, season=None, season_uuid=None, number=None, rating=None, aired=None, expiry=None, stream=None, content_type=None):
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
        :type position: int
        :type season: int
        :type season_uuid: str
        :type number: int
        :type rating: str
        :type aired: datetime
        :type expiry: datetime
        :type stream: str
        :type content_type: str
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
        self.position = position
        self.season = season
        self.season_uuid = season_uuid
        self.number = number
        self.rating = rating
        self.aired = aired
        self.expiry = expiry
        self.stream = stream
        self.content_type = content_type

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


class Swimlane:
    """ Defines a Swimlane. """

    def __init__(self, index=None, title=None, lane_type=None):
        """
        :type index: int
        :type title: str
        :type lane_type: str
        """
        self.index = index
        self.title = title
        self.lane_type = lane_type

    def __repr__(self):
        return "%r" % self.__dict__


class Channel:
    """ Defines a Channel. """

    def __init__(self, uuid=None, index=None, title=None, description=None, brand=None, logo=None, fanart=None):
        """
        :type uuid: str
        :type index: int
        :type title: str
        :type description: str
        :type brand: str
        :type logo: str
        :type fanart: str
        """
        self.uuid = uuid
        self.index = index
        self.title = title
        self.description = description
        self.brand = brand
        self.logo = logo
        self.fanart = fanart


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

    @staticmethod
    def channel2brand(channel):
        """ Maps a channel name to a brand id
        :type channel: str
        :rtype str
        """
        brands = {
            'Play 4': 'vier',
            'Play 5': 'vijf',
            'Play 6': 'zes',
            'Play 7': 'zeven',
            'GoPlay': 'goplay',
            'Play Crime': 'play crime',
        }
        return brands.get(channel)

    def get_programs(self, channel=None, category=None):
        """ Get all programs optionally filtered by channel or category.
        :type channel: str
        :type category: int
        :rtype list[Program]
        """
        programs = self.get_program_tree()

        # Return all programs
        if not channel and not category:
            return programs

        # filter by category_id, channel
        key = ''
        value = None
        if channel:
            key = 'channel'
            value = self.channel2brand(channel)
        elif category:
            key = 'category_id'
            value = category
        return [program for program in programs if getattr(program, key) == value]

    def get_program(self, uuid, cache=CACHE_AUTO):
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
            result = self._get_url(self.API_GOPLAY + '/tv/v2/programs/%s' % uuid)
            data = json.loads(result)
            return data

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['program', uuid], cache_mode=cache, update=update)
        if not data:
            return None

        program = self._parse_program_data(data)

        return program

    def get_live_channels(self, cache=CACHE_AUTO):
        """  Get a list of live channels.
        :type cache: str
        :rtype list[Channel]
        """
        def update():
            """ Fetch the program metadata """
            # Fetch webpage
            result = self._get_url(self.API_GOPLAY + '/tv/v1/liveStreams', authentication='Bearer %s' % self._auth.get_token())
            data = json.loads(result)
            return data

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['channels'], cache_mode=cache, update=update)
        if not data:
            raise NoContentException('No content')

        channels = self._parse_channels_data(data)

        return channels

    def get_episodes(self, playlist_uuid, offset=0, limit=100, cache=CACHE_AUTO):
        """  Get a list of all episodes of the specified playlist.
        :type playlist_uuid: str
        :type cache: str
        :rtype list[Episode]
        """
        if not playlist_uuid:
            return None

        def update():
            """ Fetch the program metadata """
            # Fetch webpage
            result = self._get_url(self.API_GOPLAY + '/tv/v1/playlists/%s?offset=%s&limit=%s' % (playlist_uuid, offset, limit), authentication='Bearer %s' % self._auth.get_token())
            data = json.loads(result)
            return data

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['playlist', playlist_uuid, offset, limit], cache_mode=cache, update=update)
        if not data:
            return None

        episodes = self._parse_playlist_data(data)

        return episodes

    def get_stream(self, uuid, content_type):
        """ Return a ResolvedStream for this video.
        :type uuid: str
        :type content_type: str
        :rtype: ResolvedStream
        """
        mode = 'videos/long-form'
        if content_type == 'video-short_form':
            mode = 'videos/short-form'
        elif content_type == 'live_channel':
            mode = 'liveStreams'
        response = self._get_url(self.API_GOPLAY + '/tv/v1/%s/%s' % (mode, uuid), authentication='Bearer %s' % self._auth.get_token())
        data = json.loads(response)

        if not data:
            raise UnavailableException

        # Get DRM license
        license_key = None
        if data.get('drmXml'):
            # BuyDRM format
            # See https://docs.unified-streaming.com/documentation/drm/buydrm.html#setting-up-the-client

            # Generate license key
            license_key = self.create_license_key('https://wv-keyos.licensekeyserver.com/', key_headers={
                'customdata': data['drmXml']
            })

        # Get manifest url
        if data.get('manifestUrls'):

            if data.get('manifestUrls').get('dash'):
                # DASH stream
                return ResolvedStream(
                    uuid=uuid,
                    url=data['manifestUrls']['dash'],
                    stream_type=STREAM_DASH,
                    license_key=license_key,
                )

            # HLS stream
            return ResolvedStream(
                uuid=uuid,
                url=data['manifestUrls']['hls'],
                stream_type=STREAM_HLS,
                license_key=license_key,
            )

        # No manifest url found, get manifest from Server-Side Ad Insertion service
        if data.get('adType') == 'SSAI' and data.get('ssai'):
            url = 'https://pubads.g.doubleclick.net/ondemand/dash/content/%s/vid/%s/streams' % (
                data.get('ssai').get('contentSourceID'), data.get('ssai').get('videoID'))
            ad_data = json.loads(self._post_url(url, data=''))

            # Server-Side Ad Insertion DASH stream
            return ResolvedStream(
                uuid=uuid,
                url=ad_data['stream_manifest'],
                stream_type=STREAM_DASH,
                license_key=license_key,
            )
        if data.get('message'):
            raise GeoblockedException(data)
        raise UnavailableException

    def get_program_tree(self):
        """ Get a content tree with information about all the programs.
        :rtype list[Program]
        """
        page = 'programs'
        swimlanes = self.get_page(page)
        cards = []
        # get lanes
        for lane in swimlanes:
            index = lane.index
            # get lane by index
            _, data = self.get_swimlane(page, index)
            cards.extend(data)
        return cards

    def get_categories(self):
        """ Return a list of categories.
        :rtype list[Category]
        """
        content_tree = self.get_program_tree()
        categories = []
        cat_set = set()
        for item in content_tree:
            cat_obj = Category(uuid=item.category_id, title=item.category_name)
            if item.category_id not in cat_set:
                categories.append(cat_obj)
                cat_set.add(item.category_id)
        return categories

    def get_page(self, page, cache=CACHE_AUTO):
        """ Get a list of all swimlanes on a page.
        :rtype list[Swimlane]
        """

        def update():
            """ Fetch the pages metadata """
            data = self._get_url(self.API_GOPLAY + '/tv/v2/pages/%s' % page, authentication='Bearer %s' % self._auth.get_token())
            result = json.loads(data)
            return result

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['pages', page], cache_mode=cache, update=update)
        if not data:
            return None

        swimlanes = []
        for item in data.get('lanes'):
            swimlanes.append(
                Swimlane(index=item.get('index'),
                         title=item.get('title'),
                         lane_type=item.get('laneType')
                )
            )
        return swimlanes

    def get_swimlane(self, page, index, limit=100, offset=0, cache=CACHE_PREVENT):
        """ Get a list of all categories.
        :rtype list[Episode], list[Program]
        """

        def update():
            """ Fetch the swimlane metadata """
            cards = []
            got_everything = False
            offset = 0
            while not got_everything:
                data = self._get_url(self.API_GOPLAY + '/tv/v2/pages/%s/lanes/%s?limit=%s&offset=%s' % (page, index, limit, offset), authentication='Bearer %s' % self._auth.get_token())
                result = json.loads(data)
                cards.extend(result.get('cards'))
                total = result.get('total')
                if offset < (total - limit):
                    offset += limit
                else:
                    got_everything = True
            return cards

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['swimlane', page, index, limit, offset], cache_mode=cache, update=update)

        videos, programs = self._parse_cards_data(data)

        return videos, programs

    def search(self, query, limit=100, offset=0, cache=CACHE_AUTO):
        """ Search by query """
        def update():
            """ Fetch the search metadata """
            offset = 0
            payload = {
                'limit': limit,
                'offset': offset,
                'query': query,
            }
            cards = []
            got_everything = False
            while not got_everything:
                data = self._post_url(self.API_GOPLAY + '/tv/v1/search', data=payload, authentication='Bearer %s' % self._auth.get_token())
                result = json.loads(data)
                cards.extend(result.get('cards'))
                total = result.get('total')
                if offset < (total - limit):
                    offset += limit
                else:
                    got_everything = True
            return cards

        # Fetch listing from cache or update if needed
        data = self._handle_cache(key=['search', query, limit, offset], cache_mode=cache, update=update)

        videos, programs = self._parse_cards_data(data)
        return videos, programs

    def get_mylist(self):
        """ Get the content of My List
        :rtype list[Program]
        """
        data = self._get_url(
            self.API_GOPLAY + '/tv/v1/programs/myList',
            authentication='Bearer %s' % self._auth.get_token()
        )
        result = json.loads(data)

        items = []
        for item in result:
            try:
                program = self.get_program(item)
                if program:
                    program.my_list = True
                    items.append(program)
            except Exception as exc:  # pylint: disable=broad-except
                _LOGGER.warning(exc)

        return items

    def mylist_add(self, program_id):
        """ Add a program on My List """
        self._put_url(
            self.API_GOPLAY + '/tv/v1/programs/%s/myList' % program_id,
            data={'onMyList': True},
            authentication='Bearer %s' % self._auth.get_token()
        )

    def mylist_del(self, program_id):
        """ Remove a program on My List """
        self._put_url(
            self.API_GOPLAY + '/tv/v1/programs/%s/myList' % program_id,
            data={'onMyList': False},
            authentication='Bearer %s' % self._auth.get_token()
        )

    def update_position(self, video_id, position):
        """ Update resume position of a video """
        self._put_url(
            self.API_GOPLAY + '/tv/v1/videos/%s/position' % video_id,
            data={'position': position},
            authentication='Bearer %s' % self._auth.get_token()
        )

    def delete_position(self, video_id):
        """ Update resume position of a video """
        self._delete_url(
            self.API_GOPLAY + '/web/v1/videos/continue-watching/%s' % video_id,
            authentication='Bearer %s' % self._auth.get_token()
        )

    @staticmethod
    def _parse_program_data(data):
        """ Parse the Program JSON.
        :type data: dict
        :rtype Program
        """
        # Create Program info
        program = Program(
            uuid=data.get('programUuid'),
            path=data.get('programUuid'),
            channel=data.get('brand'),
            title=data.get('title'),
            description=html_to_kodi(data.get('description')),
            aired=datetime.fromtimestamp(data.get('dates', {}).get('publishDate', 0.0) or 0.0),
            expiry=datetime.fromtimestamp(data.get('dates', {}).get('unpublishDate', 0.0) or 0.0),
            poster=data.get('images').get('portrait'),
            thumb=data.get('images').get('portrait'),
            fanart=data.get('images').get('background'),
        )

        # Create Season info

        program.seasons = {
            key: Season(
                uuid=playlist.get('playlistUuid'),
                title=playlist.get('title'),
                number=re.compile(r'\d+$').findall(playlist.get('title'))[-1] if re.compile(r'\d+$').findall(playlist.get('title')) else None,
            )
            for key, playlist in enumerate(data.get('playlists', [])) if playlist.get('title')
        }

        return program


    @staticmethod
    def _parse_cards_data(data):
        """ Parse the Cards JSON.
        :type data: dict
        ::rtype list[Episode], list[Program]
        """
        videos = []
        programs = []
        for card in data:
            if card.get('type') == 'PROGRAM':
                # Program
                programs.append(Program(
                    uuid=card.get('uuid'),
                    title=card.get('title'),
                    category_id=str(card.get('categoryId')),
                    category_name=card.get('category') or 'No category',
                    poster=card.get('images')[0].get('url'),
                    channel=card.get('brand'),
                ))
            elif card.get('type') == 'VIDEO':
                # Video
                videos.append(Episode(
                    uuid=card.get('uuid'),
                    title=card.get('subtitle'),
                    channel=card.get('brand'),
                    description=html_to_kodi(card.get('description')),
                    duration=card.get('duration'),
                    position=card.get('position'),
                    thumb=card.get('images')[0].get('url'),
                    program_title=card.get('title'),
                    aired=datetime.fromtimestamp(card.get('dates', {}).get('publishDate', 0.0) or 0.0),
                    expiry=datetime.fromtimestamp(card.get('dates', {}).get('unpublishDate', 0.0) or 0.0),
                    content_type='long_form',
                ))
        return videos, programs


    @staticmethod
    def _parse_playlist_data(data):
        """ Parse the Playlist JSON.
        :type data: dict
        :rtype Playlist
        """
        # Create Playlist info
        playlist = [
            Episode(
                uuid=video.get('videoUuid'),
                title=video.get('title'),
                aired=datetime.fromtimestamp(video.get('dates', {}).get('publishDate', 0.0) or 0.0),
                expiry=datetime.fromtimestamp(video.get('dates', {}).get('unpublishDate', 0.0) or 0.0),
                description=html_to_kodi(video.get('description')),
                thumb=video.get('image'),
                duration=video.get('duration'),
                #number=video.get('title').split()[1],
                content_type='long_form',
            )
            for video in data.get('videos', [])
        ]
        return playlist


    @staticmethod
    def _parse_channels_data(data):
        """ Parse the Channel JSON.
        :type data: dict
        :rtype list[Channel]
        """
        # Create Channel info
        channels = [
            Channel(
                uuid=channel.get('uuid'),
                index=channel.get('index'),
                title=channel.get('title'),
                description=html_to_kodi(channel.get('description')),
                brand=channel.get('brand'),
                logo=channel.get('transparentLogo')[0].get('url'),
                fanart=channel.get('images')[2].get('url'),
            )
            for channel in data
        ]
        return channels


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
            content_type=data.get('type'),
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

    @staticmethod
    def create_license_key(key_url, key_type='R', key_headers=None, key_value='', response_value=''):
        """ Create a license key string that we need for inputstream.adaptive.
        :type key_url: str
        :type key_type: str
        :type key_headers: dict[str, str]
        :type key_value: str
        :type response_value: str
        :rtype str
        """
        try:  # Python 3
            from urllib.parse import quote, urlencode
        except ImportError:  # Python 2
            from urllib import quote, urlencode

        header = ''
        if key_headers:
            header = urlencode(key_headers)

        if key_type in ('A', 'R', 'B'):
            key_value = key_type + '{SSM}'
        elif key_type == 'D':
            if 'D{SSM}' not in key_value:
                raise ValueError('Missing D{SSM} placeholder')
            key_value = quote(key_value)

        return '%s|%s|%s|%s' % (key_url, header, key_value, response_value)

    def _get_url(self, url, params=None, authentication=None):
        """ Makes a GET request for the specified URL.
        :type url: str
        :type authentication: str
        :rtype str
        """
        if authentication:
            response = self._session.get(url, params=params, headers={
                'authorization': authentication,
            }, proxies=PROXIES)
        else:
            response = self._session.get(url, params=params, proxies=PROXIES)

        if response.status_code not in (200, 451):
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
            }, proxies=PROXIES)
        else:
            response = self._session.post(url, params=params, json=data, proxies=PROXIES)

        if response.status_code not in (200, 201):
            _LOGGER.error(response.text)
            raise Exception('Could not fetch data')

        return response.text

    def _put_url(self, url, params=None, data=None, authentication=None):
        """ Makes a PUT request for the specified URL.
        :type url: str
        :type authentication: str
        :rtype str
        """
        if authentication:
            response = self._session.put(url, params=params, json=data, headers={
                'authorization': authentication,
            }, proxies=PROXIES)
        else:
            response = self._session.put(url, params=params, json=data, proxies=PROXIES)

        if response.status_code not in (200, 201, 204):
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
            }, proxies=PROXIES)
        else:
            response = self._session.delete(url, params=params, proxies=PROXIES)

        if response.status_code not in (200, 202):
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
                _LOGGER.debug('Fetching fresh data for key %s', '.'.join(str(x) for x in key))
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
        filename = ('.'.join(str(x) for x in key) + '.json').replace('/', '_')
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
        filename = ('.'.join(str(x) for x in key) + '.json').replace('/', '_')
        fullpath = os.path.join(self._cache_path, filename)

        if not os.path.exists(self._cache_path):
            os.makedirs(self._cache_path)

        with open(fullpath, 'w') as fdesc:
            _LOGGER.debug('Storing to cache as %s', filename)
            json.dump(data, fdesc)

        # Set TTL by modifying modification date
        deadline = int(time.time()) + ttl
        os.utime(fullpath, (deadline, deadline))
