# -*- coding: utf-8 -*-
""" VTM GO API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging

import requests

from resources.lib.vtmgo.vtmgoauth import VtmGoAuth, InvalidLoginException

_LOGGER = logging.getLogger('vtmgo')

try:  # Python 3
    from urllib.parse import quote
except ImportError:  # Python 2
    from urllib import quote

CACHE_AUTO = 1  # Allow to use the cache, and query the API if no cache is available
CACHE_ONLY = 2  # Only use the cache, don't use the API
CACHE_PREVENT = 3  # Don't use the cache


class UnavailableException(Exception):
    """ Is thrown when an item is unavailable. """


class ApiUpdateRequired(Exception):
    """ Is thrown when the an API update is required. """


class Profile:
    """ Defines a profile under your account. """

    def __init__(self, key=None, product=None, name=None, gender=None, birthdate=None, color=None, color2=None):
        """
        :type key: str
        :type product: str
        :type name: str
        :type gender: str
        :type birthdate: str
        :type color: str
        :type color2: str
        """
        self.key = key
        self.product = product
        self.name = name
        self.gender = gender
        self.birthdate = birthdate
        self.color = color
        self.color2 = color2

    def __repr__(self):
        return "%r" % self.__dict__


class LiveChannel:
    """ Defines a tv channel that can be streamed live """

    def __init__(self, key=None, channel_id=None, name=None, logo=None, background=None, epg=None, geoblocked=False):
        """
        :type key: str
        :type channel_id: str
        :type name: str
        :type logo: str
        :type background: str
        :type epg: list[LiveChannelEpg]
        :type geoblocked: bool
        """
        self.key = key
        self.channel_id = channel_id
        self.name = name
        self.logo = logo
        self.background = background
        self.epg = epg
        self.geoblocked = geoblocked

    def __repr__(self):
        return "%r" % self.__dict__


class LiveChannelEpg:
    """ Defines a program that is broadcast on a live tv channel"""

    def __init__(self, title=None, start=None, end=None):
        """
        :type title: str
        :type start: datetime.datetime
        :type end: datetime.datetime
        """
        self.title = title
        self.start = start
        self.end = end

    def __repr__(self):
        return "%r" % self.__dict__


class Category:
    """ Defines a category from the catalog """

    def __init__(self, category_id=None, title=None, content=None):
        """
        :type category_id: str
        :type title: str
        :type content: list[Union[Movie, Program, Episode]]
        """
        self.category_id = category_id
        self.title = title
        self.content = content

    def __repr__(self):
        return "%r" % self.__dict__


class Movie:
    """ Defines a Movie """

    def __init__(self, movie_id=None, name=None, description=None, year=None, cover=None, image=None, duration=None,
                 remaining=None, geoblocked=None, channel=None, legal=None, aired=None, my_list=None):
        """
        :type movie_id: str
        :type name: str
        :type description: str
        :type year: int
        :type cover: str
        :type image: str
        :type duration: int
        :type remaining: str
        :type geoblocked: bool
        :type channel: Optional[str]
        :type legal: str
        :type aired: str
        :type my_list: bool
        """
        self.movie_id = movie_id
        self.name = name
        self.description = description if description else ''
        self.year = year
        self.cover = cover
        self.image = image
        self.duration = duration
        self.remaining = remaining
        self.geoblocked = geoblocked
        self.channel = channel
        self.legal = legal
        self.aired = aired
        self.my_list = my_list

    def __repr__(self):
        return "%r" % self.__dict__


class Program:
    """ Defines a Program """

    def __init__(self, program_id=None, name=None, description=None, cover=None, image=None, seasons=None,
                 geoblocked=None, channel=None, legal=None, my_list=None):
        """
        :type program_id: str
        :type name: str
        :type description: str
        :type cover: str
        :type image: str
        :type seasons: dict[int, Season]
        :type geoblocked: bool
        :type channel: str
        :type legal: str
        :type my_list: bool
        """
        self.program_id = program_id
        self.name = name
        self.description = description if description else ''
        self.cover = cover
        self.image = image
        self.seasons = seasons if seasons else {}
        self.geoblocked = geoblocked
        self.channel = channel
        self.legal = legal
        self.my_list = my_list

    def __repr__(self):
        return "%r" % self.__dict__


class Season:
    """ Defines a Season """

    def __init__(self, number=None, episodes=None, cover=None, geoblocked=None, channel=None, legal=None):
        """
        :type number: str
        :type episodes: dict[int, Episode]
        :type cover: str
        :type geoblocked: bool
        :type channel: str
        :type legal: str
        """
        self.number = int(number)
        self.episodes = episodes if episodes else {}
        self.cover = cover
        self.geoblocked = geoblocked
        self.channel = channel
        self.legal = legal

    def __repr__(self):
        return "%r" % self.__dict__


class Episode:
    """ Defines an Episode """

    def __init__(self, episode_id=None, program_id=None, program_name=None, number=None, season=None, name=None,
                 description=None, cover=None, duration=None, remaining=None, geoblocked=None, channel=None, legal=None,
                 aired=None, progress=None, watched=False, next_episode=None):
        """
        :type episode_id: str
        :type program_id: str
        :type program_name: str
        :type number: int
        :type season: str
        :type name: str
        :type description: str
        :type cover: str
        :type duration: int
        :type remaining: int
        :type geoblocked: bool
        :type channel: str
        :type legal: str
        :type aired: str
        :type progress: int
        :type watched: bool
        :type next_episode: Episode
        """
        import re
        self.episode_id = episode_id
        self.program_id = program_id
        self.program_name = program_name
        self.number = int(number) if number else None
        self.season = int(season) if season else None
        if number:
            self.name = re.compile('^%d. ' % number).sub('', name)  # Strip episode from name
        else:
            self.name = name
        self.description = description if description else ''
        self.cover = cover
        self.duration = int(duration) if duration else None
        self.remaining = int(remaining) if remaining is not None else None
        self.geoblocked = geoblocked
        self.channel = channel
        self.legal = legal
        self.aired = aired
        self.progress = progress
        self.watched = watched
        self.next_episode = next_episode

    def __repr__(self):
        return "%r" % self.__dict__


class VtmGo:
    """ VTM GO API """
    API_ENDPOINT = 'https://api.vtmgo.be'

    CONTENT_TYPE_MOVIE = 'MOVIE'
    CONTENT_TYPE_PROGRAM = 'PROGRAM'
    CONTENT_TYPE_EPISODE = 'EPISODE'

    def __init__(self, kodi):
        """ Initialise object
        :type kodi: resources.lib.kodiwrapper.KodiWrapper
        """
        self._kodi = kodi
        self._auth = VtmGoAuth(kodi)

        self._session = requests.session()
        self._session.proxies = kodi.get_proxies()
        self._authenticate()

    def _authenticate(self):
        """ Apply authentication headers in the session """
        self._session.headers = {
            'x-app-version': '8',
            'x-persgroep-mobile-app': 'true',
            'x-persgroep-os': 'android',
            'x-persgroep-os-version': '23',
        }
        token = self._auth.get_token()
        if token:
            self._session.headers['x-dpp-jwt'] = token

        profile = self._auth.get_profile()
        if profile:
            self._session.headers['x-dpp-profile'] = profile

    def _mode(self):
        """ Return the mode that should be used for API calls """
        return 'vtmgo-kids' if self.get_product() == 'VTM_GO_KIDS' else 'vtmgo'

    def get_config(self):
        """ Returns the config for the app """
        # This is currently not used
        response = self._get_url('/config')
        info = json.loads(response)

        # This contains a player.updateIntervalSeconds that could be used to notify VTM GO about the playing progress
        return info

    def get_profiles(self, products='VTM_GO,VTM_GO_KIDS'):
        """ Returns the available profiles """
        response = self._get_url('/profiles', {'products': products})
        result = json.loads(response)

        profiles = [
            Profile(
                key=profile.get('id'),
                product=profile.get('product'),
                name=profile.get('name'),
                gender=profile.get('gender'),
                birthdate=profile.get('birthDate'),
                color=profile.get('color', {}).get('start'),
                color2=profile.get('color', {}).get('end'),
            )
            for profile in result
        ]

        return profiles

    def get_recommendations(self):
        """ Returns the config for the dashboard """
        response = self._get_url('/%s/main' % self._mode())
        recommendations = json.loads(response)

        categories = []
        for cat in recommendations.get('rows', []):
            if cat.get('rowType') not in ['SWIMLANE_DEFAULT']:
                _LOGGER.debug('Skipping recommendation %s with type %s', cat.get('title'), cat.get('rowType'))
                continue

            items = []
            for item in cat.get('teasers'):
                if item.get('target', {}).get('type') == self.CONTENT_TYPE_MOVIE:
                    movie = self.get_movie(item.get('target', {}).get('id'), cache=CACHE_ONLY)
                    if movie:
                        # We have a cover from the overview that we don't have in the details
                        movie.cover = item.get('imageUrl')
                        items.append(movie)
                    else:
                        items.append(Movie(
                            movie_id=item.get('target', {}).get('id'),
                            name=item.get('title'),
                            cover=item.get('imageUrl'),
                            image=item.get('imageUrl'),
                            geoblocked=item.get('geoBlocked'),
                        ))
                elif item.get('target', {}).get('type') == self.CONTENT_TYPE_PROGRAM:
                    program = self.get_program(item.get('target', {}).get('id'), cache=CACHE_ONLY)
                    if program:
                        # We have a cover from the overview that we don't have in the details
                        program.cover = item.get('imageUrl')
                        items.append(program)
                    else:
                        items.append(Program(
                            program_id=item.get('target', {}).get('id'),
                            name=item.get('title'),
                            cover=item.get('imageUrl'),
                            image=item.get('imageUrl'),
                            geoblocked=item.get('geoBlocked'),
                        ))

            categories.append(Category(
                category_id=cat.get('id'),
                title=cat.get('title'),
                content=items,
            ))

        return categories

    def get_swimlane(self, swimlane=None):
        """ Returns the contents of My List """
        response = self._get_url('/%s/main/swimlane/%s' % (self._mode(), swimlane))

        # Result can be empty
        if not response:
            return []

        result = json.loads(response)

        items = []
        for item in result.get('teasers'):
            if item.get('target', {}).get('type') == self.CONTENT_TYPE_MOVIE:
                movie = self.get_movie(item.get('target', {}).get('id'), cache=CACHE_ONLY)
                if movie:
                    # We have a cover from the overview that we don't have in the details
                    movie.cover = item.get('imageUrl')
                    items.append(movie)
                else:
                    items.append(Movie(
                        movie_id=item.get('target', {}).get('id'),
                        name=item.get('title'),
                        geoblocked=item.get('geoBlocked'),
                        cover=item.get('imageUrl'),
                        image=item.get('imageUrl'),
                    ))

            elif item.get('target', {}).get('type') == self.CONTENT_TYPE_PROGRAM:
                program = self.get_program(item.get('target', {}).get('id'), cache=CACHE_ONLY)
                if program:
                    # We have a cover from the overview that we don't have in the details
                    program.cover = item.get('imageUrl')
                    items.append(program)
                else:
                    items.append(Program(
                        program_id=item.get('target', {}).get('id'),
                        name=item.get('title'),
                        geoblocked=item.get('geoBlocked'),
                        cover=item.get('imageUrl'),
                        image=item.get('imageUrl'),
                    ))

            elif item.get('target', {}).get('type') == self.CONTENT_TYPE_EPISODE:
                program = self.get_program(item.get('target', {}).get('programId'), cache=CACHE_ONLY)
                episode = self.get_episode_from_program(program, item.get('target', {}).get('id')) if program else None

                items.append(Episode(
                    episode_id=item.get('target', {}).get('id'),
                    program_id=item.get('target', {}).get('programId'),
                    program_name=item.get('title'),
                    name=item.get('label'),
                    description=episode.description if episode else None,
                    geoblocked=item.get('geoBlocked'),
                    cover=item.get('imageUrl'),
                    progress=item.get('playerPositionSeconds'),
                    watched=False,
                    remaining=item.get('remainingDaysAvailable'),
                ))

        return items

    def add_mylist(self, video_type, content_id):
        """ Add an item to My List """
        self._put_url('/%s/userData/myList/%s/%s' % (self._mode(), video_type, content_id))

    def del_mylist(self, video_type, content_id):
        """ Delete an item from My List """
        self._delete_url('/%s/userData/myList/%s/%s' % (self._mode(), video_type, content_id))

    def get_live_channels(self):
        """ Get a list of all the live tv channels.
        :rtype list[LiveChannel]
        """
        import dateutil.parser
        response = self._get_url('/%s/live' % self._mode())
        info = json.loads(response)

        channels = []
        for item in info.get('channels'):
            epg = []
            for item_epg in item.get('broadcasts', []):
                epg.append(LiveChannelEpg(
                    title=item_epg.get('name'),
                    start=dateutil.parser.parse(item_epg.get('startsAt')),
                    end=dateutil.parser.parse(item_epg.get('endsAt')),
                ))
            channels.append(LiveChannel(
                key=item.get('seoKey'),
                channel_id=item.get('channelId'),
                logo=item.get('channelLogoUrl'),
                background=item.get('channelPosterUrl'),
                name=item.get('name'),
                epg=epg,
            ))

        return channels

    def get_live_channel(self, key):
        """ Get a the specified live tv channel.
        :rtype LiveChannel
        """
        channels = self.get_live_channels()
        return next(c for c in channels if c.key == key)

    def get_categories(self):
        """ Get a list of all the categories.
        :rtype list[Category]
        """
        response = self._get_url('/%s/catalog/filters' % self._mode())
        info = json.loads(response)

        categories = []
        for item in info.get('catalogFilters', []):
            categories.append(Category(
                category_id=item.get('id'),
                title=item.get('title'),
            ))

        return categories

    def get_items(self, category=None):
        """ Get a list of all the items in a category.
        :type category: str
        :rtype list[Union[Movie, Program]]
        """
        # Fetch from API
        if category is None:
            response = self._get_url('/%s/catalog' % self._mode(), {'pageSize': 1000})
        else:
            response = self._get_url('/%s/catalog' % self._mode(), {'pageSize': 1000, 'filter': quote(category)})
        info = json.loads(response)
        content = info.get('pagedTeasers', {}).get('content', [])

        items = []
        for item in content:
            if item.get('target', {}).get('type') == self.CONTENT_TYPE_MOVIE:
                movie = self.get_movie(item.get('target', {}).get('id'), cache=CACHE_ONLY)
                if movie:
                    # We have a cover from the overview that we don't have in the details
                    movie.cover = item.get('imageUrl')
                    items.append(movie)
                else:
                    items.append(Movie(
                        movie_id=item.get('target', {}).get('id'),
                        name=item.get('title'),
                        cover=item.get('imageUrl'),
                        geoblocked=item.get('geoBlocked'),
                    ))
            elif item.get('target', {}).get('type') == self.CONTENT_TYPE_PROGRAM:
                program = self.get_program(item.get('target', {}).get('id'), cache=CACHE_ONLY)
                if program:
                    # We have a cover from the overview that we don't have in the details
                    program.cover = item.get('imageUrl')
                    items.append(program)
                else:
                    items.append(Program(
                        program_id=item.get('target', {}).get('id'),
                        name=item.get('title'),
                        cover=item.get('imageUrl'),
                        geoblocked=item.get('geoBlocked'),
                    ))

        return items

    def get_movie(self, movie_id, cache=CACHE_AUTO):
        """ Get the details of the specified movie.
        :type movie_id: str
        :type cache: int
        :rtype Movie
        """
        if cache in [CACHE_AUTO, CACHE_ONLY]:
            # Try to fetch from cache
            movie = self._kodi.get_cache(['movie', movie_id])
            if movie is None and cache == CACHE_ONLY:
                return None
        else:
            movie = None

        if movie is None:
            # Fetch from API
            response = self._get_url('/%s/movies/%s' % (self._mode(), movie_id))
            info = json.loads(response)
            movie = info.get('movie', {})
            self._kodi.set_cache(['movie', movie_id], movie)

        return Movie(
            movie_id=movie.get('id'),
            name=movie.get('name'),
            description=movie.get('description'),
            duration=movie.get('durationSeconds'),
            cover=movie.get('bigPhotoUrl'),
            image=movie.get('bigPhotoUrl'),
            year=movie.get('productionYear'),
            geoblocked=movie.get('geoBlocked'),
            remaining=movie.get('remainingDaysAvailable'),
            legal=movie.get('legalIcons'),
            # aired=movie.get('broadcastTimestamp'),
            channel=self._parse_channel(movie.get('channelLogoUrl')),
        )

    def get_program(self, program_id, cache=CACHE_AUTO):
        """ Get the details of the specified program.
        :type program_id: str
        :type cache: int
        :rtype Program
        """
        if cache in [CACHE_AUTO, CACHE_ONLY]:
            # Try to fetch from cache
            program = self._kodi.get_cache(['program', program_id])
            if program is None and cache == CACHE_ONLY:
                return None
        else:
            program = None

        if program is None:
            # Fetch from API
            response = self._get_url('/%s/programs/%s' % (self._mode(), program_id))
            info = json.loads(response)
            program = info.get('program', {})
            self._kodi.set_cache(['program', program_id], program)

        channel = self._parse_channel(program.get('channelLogoUrl'))

        seasons = {}
        for item_season in program.get('seasons', []):
            episodes = {}

            for item_episode in item_season.get('episodes', []):
                episodes[item_episode.get('index')] = Episode(
                    episode_id=item_episode.get('id'),
                    program_id=program_id,
                    program_name=program.get('name'),
                    number=item_episode.get('index'),
                    season=item_season.get('index'),
                    name=item_episode.get('name'),
                    description=item_episode.get('description'),
                    duration=item_episode.get('durationSeconds'),
                    cover=item_episode.get('bigPhotoUrl'),
                    geoblocked=program.get('geoBlocked'),
                    remaining=item_episode.get('remainingDaysAvailable'),
                    channel=channel,
                    legal=program.get('legalIcons'),
                    aired=item_episode.get('broadcastTimestamp'),
                    progress=item_episode.get('playerPositionSeconds', 0),
                    watched=item_episode.get('doneWatching', False),
                )

            seasons[item_season.get('index')] = Season(
                number=item_season.get('index'),
                episodes=episodes,
                cover=item_season.get('episodes', [{}])[0].get('bigPhotoUrl')
                if episodes else program.get('bigPhotoUrl'),
                geoblocked=program.get('geoBlocked'),
                channel=channel,
                legal=program.get('legalIcons'),
            )

        return Program(
            program_id=program.get('id'),
            name=program.get('name'),
            description=program.get('description'),
            cover=program.get('bigPhotoUrl'),
            image=program.get('bigPhotoUrl'),
            geoblocked=program.get('geoBlocked'),
            seasons=seasons,
            channel=channel,
            legal=program.get('legalIcons'),
        )

    @staticmethod
    def get_episode_from_program(program, episode_id):
        """ Extract the specified episode from the program data.
        :type program: Program
        :type episode_id: str
        :rtype Episode
        """
        for season in list(program.seasons.values()):
            for episode in list(season.episodes.values()):
                if episode.episode_id == episode_id:
                    return episode

        return None

    @staticmethod
    def get_next_episode_from_program(program, season, number):
        """ Search for the next episode in the program data.
        :type program: Program
        :type season: int
        :type number: int
        :rtype Episode
        """
        next_season_episode = None

        # First, try to find a match in the current season
        for episode in [e for s in list(program.seasons.values()) for e in list(s.episodes.values())]:
            if episode.season == season and episode.number == number + 1:
                return episode
            if episode.season == season + 1 and episode.number == 1:
                next_season_episode = episode

        # No match, use the first episode of next season
        if next_season_episode:
            return next_season_episode

        # We are playing the last episode
        return None

    def get_episode(self, episode_id):
        """ Get some details of the specified episode.
        :type episode_id: str
        :rtype Episode
        """
        response = self._get_url('/%s/play/episode/%s' % (self._mode(), episode_id))
        episode = json.loads(response)

        # Extract next episode info if available
        next_playable = episode.get('nextPlayable')
        if next_playable:
            next_episode = Episode(
                episode_id=next_playable['id'],
                program_name=next_playable['title'],
                name=next_playable['subtitle'],
                description=next_playable['description'],
                cover=next_playable['imageUrl'],
            )
        else:
            next_episode = None

        return Episode(
            episode_id=episode.get('id'),
            name=episode.get('title'),
            cover=episode.get('posterImageUrl'),
            progress=episode.get('playerPositionSeconds'),
            next_episode=next_episode,
        )

    def do_search(self, search):
        """ Do a search in the full catalog.
        :type search: str
        :rtype list[Union[Movie, Program]]
        """
        response = self._get_url('/%s/autocomplete/?maxItems=%d&keywords=%s' % (self._mode(), 50, quote(search)))
        results = json.loads(response)

        items = []
        for item in results.get('suggestions', []):
            if item.get('type') == self.CONTENT_TYPE_MOVIE:
                movie = self.get_movie(item.get('id'), cache=CACHE_ONLY)
                if movie:
                    items.append(movie)
                else:
                    items.append(Movie(
                        movie_id=item.get('id'),
                        name=item.get('name'),
                    ))
            elif item.get('type') == self.CONTENT_TYPE_PROGRAM:
                program = self.get_program(item.get('id'), cache=CACHE_ONLY)
                if program:
                    items.append(program)
                else:
                    items.append(Program(
                        program_id=item.get('id'),
                        name=item.get('name'),
                    ))

        return items

    def get_product(self):
        """ Return the product that is currently selected. """
        profile = self._kodi.get_setting('profile')
        try:
            return profile.split(':')[1]
        except (IndexError, AttributeError):
            return None

    @staticmethod
    def _parse_channel(url):
        """ Parse the channel logo url, and return an icon that matches resource.images.studios.white
        :type url: str
        :rtype str
        """
        if not url:
            return None

        import os.path
        # The channels id's we use in resources.lib.modules.CHANNELS neatly matches this part in the url.
        return str(os.path.basename(url).split('-')[0])

    def _get_url(self, url, params=None):
        """ Makes a GET request for the specified URL.
        :type url: str
        :type params: dict
        :rtype str
        """
        try:
            return self._request('GET', url, params=params)
        except InvalidLoginException:
            self._auth.clear_token()
            self._authenticate()
            # Retry the same request
            return self._request('GET', url, params=params)

    def _put_url(self, url, params=None):
        """ Makes a PUT request for the specified URL.
        :type url: str
        :type params: dict
        :rtype str
        """
        try:
            return self._request('PUT', url, params=params)
        except InvalidLoginException:
            self._auth.clear_token()
            self._authenticate()
            # Retry the same request
            return self._request('PUT', url, params=params)

    def _post_url(self, url, params=None, data=None):
        """ Makes a POST request for the specified URL.
        :type url: str
        :type params: dict
        :type data: dict
        :rtype str
        """
        try:
            return self._request('POST', url, params=params, data=data)
        except InvalidLoginException:
            self._auth.clear_token()
            self._authenticate()
            # Retry the same request
            return self._request('POST', url, params=params)

    def _delete_url(self, url, params=None):
        """ Makes a DELETE request for the specified URL.
        :type url: str
        :type params: dict
        :rtype str
        """
        try:
            return self._request('DELETE', url, params=params)
        except InvalidLoginException:
            self._auth.clear_token()
            self._authenticate()
            # Retry the same request
            return self._request('DELETE', url, params=params)

    def _request(self, method, url, params=None, data=None):
        """ Makes a request for the specified URL.
        :type url: str
        :type params: dict
        :type data: dict
        :rtype str
        """
        _LOGGER.debug('Sending %s %s...', method, url)
        response = self._session.request(method,
                                         self.API_ENDPOINT + url,
                                         params=params,
                                         json=data)

        # Set encoding to UTF-8 if no charset is indicated in http headers (https://github.com/psf/requests/issues/1604)
        if not response.encoding:
            response.encoding = 'utf-8'

        _LOGGER.debug('Got response (status=%s): %s', response.status_code, response.text)

        if response.status_code == 404:
            raise UnavailableException()

        if response.status_code == 401:
            raise InvalidLoginException()

        if response.status_code == 426:
            raise ApiUpdateRequired()

        if response.status_code not in [200, 204]:
            raise Exception('Error %s.' % response.status_code)

        return response.text
