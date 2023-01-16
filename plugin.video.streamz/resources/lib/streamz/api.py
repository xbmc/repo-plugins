# -*- coding: utf-8 -*-
""" Streamz API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging

from resources.lib import kodiutils
from resources.lib.streamz import API_ANDROID_ENDPOINT, API_ENDPOINT, Category, Episode, Movie, Program, Season, util

_LOGGER = logging.getLogger(__name__)

try:  # Python 3
    from urllib.parse import quote
except ImportError:  # Python 2
    from urllib import quote

CACHE_AUTO = 1  # Allow to use the cache, and query the API if no cache is available
CACHE_ONLY = 2  # Only use the cache, don't use the API
CACHE_PREVENT = 3  # Don't use the cache

CONTENT_TYPE_MOVIE = 'MOVIE'
CONTENT_TYPE_PROGRAM = 'PROGRAM'
CONTENT_TYPE_EPISODE = 'EPISODE'


class Api:
    """ Streamz API """

    def __init__(self, tokens):
        """ Initialise object
        :param resources.lib.vtmgo.vtmgoauth.AccountStorage token:       An authenticated token.
        """
        self._tokens = tokens

    def _mode(self):
        """ Return the mode that should be used for API calls. """
        return self._tokens.product

    @staticmethod
    def get_config():
        """ Returns the config for the app. """
        response = util.http_get(API_ANDROID_ENDPOINT + '/streamz/config')
        info = json.loads(response.text)

        # This contains a player.updateIntervalSeconds that could be used to notify Streamz about the playing progress
        return info

    def get_storefront(self, storefront):
        """ Returns a storefront.

         :param str storefront:         The ID of the storefront.
         :rtype: list[Category|Program|Movie]
         """
        response = util.http_get(API_ENDPOINT + '/%s/storefronts/%s' % (self._mode(), storefront),
                                 token=self._tokens.access_token,
                                 profile=self._tokens.profile)
        result = json.loads(response.text)

        items = []
        for row in result.get('rows', []):
            if row.get('rowType') in ['SWIMLANE_DEFAULT', 'SWIMLANE_PORTRAIT', 'SWIMLANE_LANDSCAPE']:
                items.append(Category(
                    category_id=row.get('id'),
                    title=row.get('title'),
                ))
                continue

            if row.get('rowType') == 'CAROUSEL':
                for item in row.get('teasers'):
                    if item.get('target', {}).get('type') == CONTENT_TYPE_MOVIE:
                        items.append(self._parse_movie_teaser(item))

                    elif item.get('target', {}).get('type') == CONTENT_TYPE_PROGRAM:
                        items.append(self._parse_program_teaser(item))
                continue

            if row.get('rowType') in ['TOP_BANNER', 'MARKETING_BLOCK']:
                item = row.get('teaser')
                if item.get('target', {}).get('type') == CONTENT_TYPE_MOVIE:
                    items.append(self._parse_movie_teaser(item))

                elif item.get('target', {}).get('type') == CONTENT_TYPE_PROGRAM:
                    items.append(self._parse_program_teaser(item))
                continue

            _LOGGER.debug('Skipping recommendation %s with type %s', row.get('title'), row.get('rowType'))

        return items

    def get_storefront_category(self, storefront, category):
        """ Returns a storefront.

         :param str storefront:         The ID of the storefront.
         :param str category:           The ID of the category.
         :rtype: Category
         """
        response = util.http_get(API_ENDPOINT + '/%s/storefronts/%s/detail/%s' % (self._mode(), storefront, category),
                                 token=self._tokens.access_token,
                                 profile=self._tokens.profile)
        result = json.loads(response.text)

        items = []
        for item in result.get('teasers'):
            if item.get('target', {}).get('type') == CONTENT_TYPE_MOVIE:
                items.append(self._parse_movie_teaser(item))

            elif item.get('target', {}).get('type') == CONTENT_TYPE_PROGRAM:
                items.append(self._parse_program_teaser(item))

            elif item.get('target', {}).get('type') == CONTENT_TYPE_EPISODE:
                items.append(self._parse_episode_teaser(item))

        return Category(category_id=category, title=result.get('row', {}).get('title'), content=items)

    def get_mylist(self, content_filter=None, cache=CACHE_ONLY):
        """ Returns the contents of My List """
        response = util.http_get(API_ENDPOINT + '/%s/my-list' % (self._mode()),
                                 token=self._tokens.access_token,
                                 profile=self._tokens.profile)

        # Result can be empty
        if not response.text:
            return []

        result = json.loads(response.text)

        items = []
        for item in result.get('teasers'):
            if item.get('target', {}).get('type') == CONTENT_TYPE_MOVIE and content_filter in [None, Movie]:
                items.append(self._parse_movie_teaser(item, cache=cache))

            elif item.get('target', {}).get('type') == CONTENT_TYPE_PROGRAM and content_filter in [None, Program]:
                items.append(self._parse_program_teaser(item, cache=cache))

            elif item.get('target', {}).get('type') == CONTENT_TYPE_EPISODE and content_filter in [None, Episode]:
                items.append(self._parse_episode_teaser(item, cache=cache))

        return items

    def add_mylist(self, content_id):
        """ Add an item to My List. """
        util.http_put(API_ENDPOINT + '/%s/userData/myList/%s' % (self._mode(), content_id),
                      token=self._tokens.access_token,
                      profile=self._tokens.profile)
        kodiutils.set_cache(['swimlane', 'my-list'], None)

    def del_mylist(self, content_id):
        """ Delete an item from My List. """
        util.http_delete(API_ENDPOINT + '/%s/userData/myList/%s' % (self._mode(), content_id),
                         token=self._tokens.access_token,
                         profile=self._tokens.profile)
        kodiutils.set_cache(['swimlane', 'my-list'], None)

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

        if not movie:
            # Fetch from API
            response = util.http_get(API_ENDPOINT + '/%s/detail/%s' % (self._mode(), movie_id),
                                     token=self._tokens.access_token,
                                     profile=self._tokens.profile)
            movie = json.loads(response.text)
            kodiutils.set_cache(['movie', movie_id], movie)

        return Movie(
            movie_id=movie.get('id'),
            name=movie.get('name'),
            description=movie.get('description'),
            duration=movie.get('durationSeconds'),
            poster=movie.get('portraitTeaserImageUrl'),
            thumb=movie.get('landscapeTeaserImageUrl'),
            fanart=movie.get('backgroundImageUrl'),
            year=movie.get('productionYear'),
            geoblocked=movie.get('blockedFor') == 'GEO',
            remaining=movie.get('remainingDaysAvailable'),
            legal=movie.get('legalIcons'),
            # aired=movie.get('broadcastTimestamp'),
            channel=self._parse_channel(movie.get('channelLogoUrl')),
            # my_list=program.get('addedToMyList'),  # Don't use addedToMyList, since we might have cached this info
            available=movie.get('blockedFor') != 'SUBSCRIPTION',
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

        if not program:
            # Fetch from API
            response = util.http_get(API_ENDPOINT + '/%s/detail/%s' % (self._mode(), program_id),
                                     token=self._tokens.access_token,
                                     profile=self._tokens.profile)
            program = json.loads(response.text)
            kodiutils.set_cache(['program', program_id], program)

        channel = self._parse_channel(program.get('channelLogoUrl'))

        seasons = {}
        for item_season in program.get('seasonIndices', []):
            episodes = {}

            # Fetch season
            season_response = util.http_get(API_ENDPOINT + '/%s/detail/%s?selectedSeasonIndex=%s' % (self._mode(), program_id, item_season),
                                            token=self._tokens.access_token,
                                            profile=self._tokens.profile)
            season = json.loads(season_response.text).get('selectedSeason')

            for item_episode in season.get('episodes', []):
                episodes[item_episode.get('index')] = Episode(
                    episode_id=item_episode.get('id'),
                    program_id=program_id,
                    program_name=program.get('name'),
                    number=item_episode.get('index'),
                    season=item_season,
                    name=item_episode.get('name'),
                    description=item_episode.get('description'),
                    duration=item_episode.get('durationSeconds'),
                    thumb=item_episode.get('imageUrl'),
                    fanart=item_episode.get('imageUrl'),
                    geoblocked=program.get('blockedFor') == 'GEO',
                    remaining=item_episode.get('remainingDaysAvailable'),
                    channel=channel,
                    legal=program.get('legalIcons'),
                    aired=item_episode.get('broadcastTimestamp'),
                    progress=item_episode.get('playerPositionSeconds', 0),
                    watched=item_episode.get('doneWatching', False),
                    available=item_episode.get('blockedFor') != 'SUBSCRIPTION',
                )

            seasons[item_season] = Season(
                number=item_season,
                episodes=episodes,
                channel=channel,
                legal=program.get('legalIcons'),
            )

        return Program(
            program_id=program.get('id'),
            name=program.get('name'),
            description=program.get('description'),
            thumb=program.get('landscapeTeaserImageUrl'),
            fanart=program.get('backgroundImageUrl'),
            geoblocked=program.get('blockedFor') == 'GEO',
            seasons=seasons,
            channel=channel,
            legal=program.get('legalIcons'),
            # my_list=program.get('addedToMyList'),  # Don't use addedToMyList, since we might have cached this info
            available=program.get('blockedFor') != 'SUBSCRIPTION',
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
        response = util.http_get(API_ENDPOINT + '/%s/play/%s' % (self._mode(), episode_id),
                                 token=self._tokens.access_token,
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
                poster=next_playable['imageUrl'],
            )
        else:
            next_episode = None

        return Episode(
            episode_id=episode.get('id'),
            name=episode.get('title'),
            poster=episode.get('posterImageUrl'),
            progress=episode.get('playerPositionSeconds'),
            next_episode=next_episode,
        )

    def do_search(self, search):
        """ Do a search in the full catalog.
        :type search: str
        :rtype list[Union[Movie, Program]]
        """
        response = util.http_get(API_ENDPOINT + '/%s/search/?query=%s' % (self._mode(),
                                                                          kodiutils.to_unicode(quote(kodiutils.from_unicode(search)))),
                                 token=self._tokens.access_token,
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

    def _parse_movie_teaser(self, item, cache=CACHE_ONLY):
        """ Parse the movie json and return a Movie instance.
        :type item: dict
        :type cache: int
        :rtype Movie
        """
        movie = self.get_movie(item.get('target', {}).get('id'), cache=cache)
        if movie:
            movie.available = item.get('blockedFor') != 'SUBSCRIPTION'
            return movie

        return Movie(
            movie_id=item.get('target', {}).get('id'),
            name=item.get('title'),
            thumb=item.get('imageUrl'),
            geoblocked=item.get('blockedFor') == 'GEO',
            available=item.get('blockedFor') != 'SUBSCRIPTION',
        )

    def _parse_program_teaser(self, item, cache=CACHE_ONLY):
        """ Parse the program json and return a Program instance.
        :type item: dict
        :type cache: int
        :rtype Program
        """
        program = self.get_program(item.get('target', {}).get('id'), cache=cache)
        if program:
            program.available = item.get('blockedFor') != 'SUBSCRIPTION'
            return program

        return Program(
            program_id=item.get('target', {}).get('id'),
            name=item.get('title'),
            thumb=item.get('imageUrl'),
            geoblocked=item.get('blockedFor') == 'GEO',
            available=item.get('blockedFor') != 'SUBSCRIPTION',
        )

    def _parse_episode_teaser(self, item, cache=CACHE_ONLY):
        """ Parse the episode json and return an Episode instance.
        :type item: dict
        :type cache: int
        :rtype Episode
        """
        program = self.get_program(item.get('target', {}).get('programId'), cache=cache)
        episode = self.get_episode_from_program(program, item.get('target', {}).get('id')) if program else None

        return Episode(
            episode_id=item.get('target', {}).get('id'),
            program_id=item.get('target', {}).get('programId'),
            program_name=item.get('title'),
            name=item.get('label'),
            description=episode.description if episode else None,
            geoblocked=item.get('blockedFor') == 'GEO',
            thumb=item.get('imageUrl'),
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
