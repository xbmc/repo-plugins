# -*- coding: utf-8 -*-
""" VTM GO API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging

from resources.lib import kodiutils
from resources.lib.vtmgo import (API_ENDPOINT, Category, Movie, Program, Episode, Season, LiveChannelEpg, LiveChannel,
                                 CONTENT_TYPE_MOVIE, CONTENT_TYPE_PROGRAM, CONTENT_TYPE_EPISODE, util)

_LOGGER = logging.getLogger(__name__)

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


class VtmGo:
    """ VTM GO API """

    def __init__(self, auth):
        """ Initialise object """
        self._auth = auth
        self._tokens = self._auth.login()

    def _mode(self):
        """ Return the mode that should be used for API calls """
        return 'vtmgo-kids' if self.get_product() == 'VTM_GO_KIDS' else 'vtmgo'

    def get_config(self):
        """ Returns the config for the app """
        # This is currently not used
        response = util.http_get(API_ENDPOINT + '/config', token=self._tokens.jwt_token)
        info = json.loads(response.text)

        # This contains a player.updateIntervalSeconds that could be used to notify VTM GO about the playing progress
        return info

    def get_recommendations(self):
        """ Returns the config for the dashboard """
        response = util.http_get(API_ENDPOINT + '/%s/main' % self._mode(),
                                 token=self._tokens.jwt_token,
                                 profile=self._tokens.profile)
        recommendations = json.loads(response.text)

        categories = []
        for cat in recommendations.get('rows', []):
            if cat.get('rowType') not in ['SWIMLANE_DEFAULT']:
                _LOGGER.debug('Skipping recommendation %s with type %s', cat.get('title'), cat.get('rowType'))
                continue

            items = []
            for item in cat.get('teasers'):
                if item.get('target', {}).get('type') == CONTENT_TYPE_MOVIE:
                    items.append(self._parse_movie_teaser(item))

                elif item.get('target', {}).get('type') == CONTENT_TYPE_PROGRAM:
                    items.append(self._parse_program_teaser(item))

            categories.append(Category(
                category_id=cat.get('id'),
                title=cat.get('title'),
                content=items,
            ))

        return categories

    def get_swimlane(self, swimlane=None):
        """ Returns the contents of My List """
        response = util.http_get(API_ENDPOINT + '/%s/main/swimlane/%s' % (self._mode(), swimlane),
                                 token=self._tokens.jwt_token,
                                 profile=self._tokens.profile)

        # Result can be empty
        if not response.text:
            return []

        result = json.loads(response.text)

        items = []
        for item in result.get('teasers'):
            if item.get('target', {}).get('type') == CONTENT_TYPE_MOVIE:
                items.append(self._parse_movie_teaser(item))

            elif item.get('target', {}).get('type') == CONTENT_TYPE_PROGRAM:
                items.append(self._parse_program_teaser(item))

            elif item.get('target', {}).get('type') == CONTENT_TYPE_EPISODE:
                items.append(self._parse_episode_teaser(item))

        return items

    def add_mylist(self, video_type, content_id):
        """ Add an item to My List """
        util.http_put(API_ENDPOINT + '/%s/userData/myList/%s/%s' % (self._mode(), video_type, content_id),
                      token=self._tokens.jwt_token,
                      profile=self._tokens.profile)

    def del_mylist(self, video_type, content_id):
        """ Delete an item from My List """
        util.http_delete(API_ENDPOINT + '/%s/userData/myList/%s/%s' % (self._mode(), video_type, content_id),
                         token=self._tokens.jwt_token,
                         profile=self._tokens.profile)

    def get_live_channels(self):
        """ Get a list of all the live tv channels.
        :rtype list[LiveChannel]
        """
        import dateutil.parser
        response = util.http_get(API_ENDPOINT + '/%s/live' % self._mode(),
                                 token=self._tokens.jwt_token,
                                 profile=self._tokens.profile)
        info = json.loads(response.text)

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
        response = util.http_get(API_ENDPOINT + '/%s/catalog/filters' % self._mode(),
                                 token=self._tokens.jwt_token,
                                 profile=self._tokens.profile)
        info = json.loads(response.text)

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
            response = util.http_get(API_ENDPOINT + '/%s/catalog' % self._mode(), {'pageSize': 1000},
                                     token=self._tokens.jwt_token,
                                     profile=self._tokens.profile)
        else:
            response = util.http_get(API_ENDPOINT + '/%s/catalog' % self._mode(), {'pageSize': 1000, 'filter': quote(category)},
                                     token=self._tokens.jwt_token,
                                     profile=self._tokens.profile)
        info = json.loads(response.text)
        content = info.get('pagedTeasers', {}).get('content', [])

        items = []
        for item in content:
            if item.get('target', {}).get('type') == CONTENT_TYPE_MOVIE:
                items.append(self._parse_movie_teaser(item))

            elif item.get('target', {}).get('type') == CONTENT_TYPE_PROGRAM:
                items.append(self._parse_program_teaser(item))

        return items

    def get_movie(self, movie_id, cache=CACHE_AUTO):
        """ Get the details of the specified movie.
        :type movie_id: str
        :type cache: int
        :rtype Movie
        """
        if cache in [CACHE_AUTO, CACHE_ONLY]:
            # Try to fetch from cache
            movie = kodiutils.get_cache(['movie', movie_id])
            if movie is None and cache == CACHE_ONLY:
                return None
        else:
            movie = None

        if movie is None:
            # Fetch from API
            response = util.http_get(API_ENDPOINT + '/%s/movies/%s' % (self._mode(), movie_id),
                                     token=self._tokens.jwt_token,
                                     profile=self._tokens.profile)
            info = json.loads(response.text)
            movie = info.get('movie', {})
            kodiutils.set_cache(['movie', movie_id], movie)

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
            program = kodiutils.get_cache(['program', program_id])
            if program is None and cache == CACHE_ONLY:
                return None
        else:
            program = None

        if program is None:
            # Fetch from API
            response = util.http_get(API_ENDPOINT + '/%s/programs/%s' % (self._mode(), program_id),
                                     token=self._tokens.jwt_token,
                                     profile=self._tokens.profile)
            info = json.loads(response.text)
            program = info.get('program', {})
            kodiutils.set_cache(['program', program_id], program)

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
        response = util.http_get(API_ENDPOINT + '/%s/play/episode/%s' % (self._mode(), episode_id),
                                 token=self._tokens.jwt_token,
                                 profile=self._tokens.profile)
        episode = json.loads(response.text)

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
        response = util.http_get(API_ENDPOINT + '/%s/search/?query=%s' % (self._mode(), quote(search)),
                                 token=self._tokens.jwt_token,
                                 profile=self._tokens.profile)
        results = json.loads(response.text)

        items = []
        for category in results.get('results', []):
            for item in category.get('teasers'):
                if item.get('target', {}).get('type') == CONTENT_TYPE_MOVIE:
                    items.append(self._parse_movie_teaser(item))

                elif item.get('target', {}).get('type') == CONTENT_TYPE_PROGRAM:
                    items.append(self._parse_program_teaser(item))
        return items

    @staticmethod
    def get_product():
        """ Return the product that is currently selected. """
        profile = kodiutils.get_setting('profile')
        try:
            return profile.split(':')[1]
        except (IndexError, AttributeError):
            return None

    def _parse_movie_teaser(self, item):
        """ Parse the movie json and return an Movie instance.
        :type item: dict
        :rtype Movie
        """
        movie = self.get_movie(item.get('target', {}).get('id'), cache=CACHE_ONLY)
        if movie:
            # We have a cover from the overview that we don't have in the details
            movie.cover = item.get('imageUrl')
            return movie

        return Movie(
            movie_id=item.get('target', {}).get('id'),
            name=item.get('title'),
            cover=item.get('imageUrl'),
            image=item.get('imageUrl'),
            geoblocked=item.get('geoBlocked'),
        )

    def _parse_program_teaser(self, item):
        """ Parse the program json and return an Program instance.
        :type item: dict
        :rtype Program
        """
        program = self.get_program(item.get('target', {}).get('id'), cache=CACHE_ONLY)
        if program:
            # We have a cover from the overview that we don't have in the details
            program.cover = item.get('imageUrl')
            return program

        return Program(
            program_id=item.get('target', {}).get('id'),
            name=item.get('title'),
            cover=item.get('imageUrl'),
            image=item.get('imageUrl'),
            geoblocked=item.get('geoBlocked'),
        )

    def _parse_episode_teaser(self, item):
        """ Parse the episode json and return an Episode instance.
        :type item: dict
        :rtype Episode
        """
        program = self.get_program(item.get('target', {}).get('programId'), cache=CACHE_ONLY)
        episode = self.get_episode_from_program(program, item.get('target', {}).get('id')) if program else None

        return Episode(
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
        )

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
