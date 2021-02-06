# -*- coding: utf-8 -*-
""" Library module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.modules.menu import Menu
from resources.lib.streamz import Movie, Program
from resources.lib.streamz.api import CACHE_AUTO, CACHE_PREVENT, CONTENT_TYPE_MOVIE, CONTENT_TYPE_PROGRAM, Api
from resources.lib.streamz.auth import Auth

_LOGGER = logging.getLogger(__name__)

LIBRARY_FULL_CATALOG = 0
LIBRARY_ONLY_MYLIST = 1


class Library:
    """ Menu code related to the catalog """

    def __init__(self):
        """ Initialise object """
        self._auth = Auth(kodiutils.get_setting('username'),
                          kodiutils.get_setting('password'),
                          kodiutils.get_setting('loginprovider'),
                          kodiutils.get_setting('profile'),
                          kodiutils.get_tokens_path())
        self._api = Api(self._auth)

    def show_library_movies(self, movie=None):
        """ Return a list of the movies that should be exported. """
        if movie is None:
            if kodiutils.get_setting_int('library_movies') == LIBRARY_FULL_CATALOG:
                # Full catalog
                # Use cache if available, fetch from api otherwise so we get rich metadata for new content
                items = self._api.get_items(content_filter=Movie, cache=CACHE_AUTO)
            else:
                # Only favourites, use cache if available, fetch from api otherwise
                items = self._api.get_swimlane('my-list', content_filter=Movie)
        else:
            items = [self._api.get_movie(movie)]

        show_unavailable = kodiutils.get_setting_bool('interface_show_unavailable')

        listing = []
        for item in items:
            if show_unavailable or item.available:
                title_item = Menu.generate_titleitem(item)
                # title_item.path = kodiutils.url_for('library_movies', movie=item.movie_id)  # We need a trailing /
                title_item.path = 'plugin://plugin.video.streamz/library/movies/?movie=%s' % item.movie_id
                listing.append(title_item)

        kodiutils.show_listing(listing, 30003, content='movies', sort=['label', 'year', 'duration'])

    def show_library_tvshows(self, program=None):
        """ Return a list of the series that should be exported. """
        if program is None:
            if kodiutils.get_setting_int('library_tvshows') == LIBRARY_FULL_CATALOG:
                # Full catalog
                # Use cache if available, fetch from api otherwise so we get rich metadata for new content
                # NOTE: We should probably use CACHE_PREVENT here, so we can pick up new episodes, but we can't since that would
                #       require a massive amount of API calls for each update. We do this only for programs in 'My list'.
                items = self._api.get_items(content_filter=Program, cache=CACHE_AUTO)
            else:
                # Only favourites, don't use cache, fetch from api
                # If we use CACHE_AUTO, we will miss updates until the user manually opens the program in the Add-on
                items = self._api.get_swimlane('my-list', content_filter=Program, cache=CACHE_PREVENT)
        else:
            # Fetch only a single program
            items = [self._api.get_program(program, cache=CACHE_PREVENT)]

        show_unavailable = kodiutils.get_setting_bool('interface_show_unavailable')

        listing = []
        for item in items:
            if show_unavailable or item.available:
                title_item = Menu.generate_titleitem(item)
                # title_item.path = kodiutils.url_for('library_tvshows', program=item.program_id)  # We need a trailing /
                title_item.path = 'plugin://plugin.video.streamz/library/tvshows/?program={program_id}'.format(program_id=item.program_id)
                listing.append(title_item)

        kodiutils.show_listing(listing, 30003, content='tvshows', sort=['label', 'year', 'duration'])

    def show_library_tvshows_program(self, program):
        """ Return a list of the episodes that should be exported. """
        program_obj = self._api.get_program(program)

        listing = []
        for season in list(program_obj.seasons.values()):
            for item in list(season.episodes.values()):
                title_item = Menu.generate_titleitem(item)
                # title_item.path = kodiutils.url_for('library_tvshows', program=item.program_id, episode=item.episode_id)
                title_item.path = 'plugin://plugin.video.streamz/library/tvshows/?program={program_id}&episode={episode_id}'.format(program_id=item.program_id,
                                                                                                                                    episode_id=item.episode_id)
                listing.append(title_item)

        # Sort by episode number by default. Takes seasons into account.
        kodiutils.show_listing(listing, 30003, content='episodes', sort=['episode', 'duration'])

    def check_library_movie(self, movie):
        """ Check if the given movie is still available. """
        _LOGGER.debug('Checking if movie %s is still available', movie)

        # Our parent path always exists
        if movie is None:
            kodiutils.library_return_status(True)
            return

        if kodiutils.get_setting_int('library_movies') == LIBRARY_FULL_CATALOG:
            id_list = self._api.get_catalog_ids()
        else:
            id_list = self._api.get_mylist_ids()

        kodiutils.library_return_status(movie in id_list)

    def check_library_tvshow(self, program):
        """ Check if the given program is still available. """
        _LOGGER.debug('Checking if program %s is still available', program)

        # Our parent path always exists
        if program is None:
            kodiutils.library_return_status(True)
            return

        if kodiutils.get_setting_int('library_tvshows') == LIBRARY_FULL_CATALOG:
            id_list = self._api.get_catalog_ids()
        else:
            id_list = self._api.get_mylist_ids()

        kodiutils.library_return_status(program in id_list)

    @staticmethod
    def mylist_added(video_type, content_id):
        """ Something has been added to My List. We want to index this. """
        if video_type == CONTENT_TYPE_MOVIE:
            if kodiutils.get_setting_int('library_movies') != LIBRARY_ONLY_MYLIST:
                return
            # This unfortunately adds the movie to the database with the wrong parent path:
            # Library().update('plugin://plugin.video.streamz/library/movies/?movie=%s&kodi_action=refresh_info' % content_id)
            Library().update('plugin://plugin.video.streamz/library/movies/')

        elif video_type == CONTENT_TYPE_PROGRAM:
            if kodiutils.get_setting_int('library_tvshows') != LIBRARY_ONLY_MYLIST:
                return
            Library().update('plugin://plugin.video.streamz/library/tvshows/?program=%s&kodi_action=refresh_info' % content_id)

    @staticmethod
    def mylist_removed(video_type, content_id):
        """ Something has been removed from My List. We want to de-index this. """
        if video_type == CONTENT_TYPE_MOVIE:
            if kodiutils.get_setting_int('library_movies') != LIBRARY_ONLY_MYLIST:
                return
            Library().clean('plugin://plugin.video.streamz/library/movies/?movie=%s' % content_id)

        elif video_type == CONTENT_TYPE_PROGRAM:
            if kodiutils.get_setting_int('library_tvshows') != LIBRARY_ONLY_MYLIST:
                return
            Library().clean('plugin://plugin.video.streamz/library/tvshows/?program=%s' % content_id)

    @staticmethod
    def configure():
        """ Configure the library integration. """
        # There seems to be no way to add sources automatically.
        # * https://forum.kodi.tv/showthread.php?tid=228840

        # Open the sources view
        kodiutils.execute_builtin('ActivateWindow(Videos,sources://video/)')

    @staticmethod
    def update(path=None):
        """ Update the library integration. """
        _LOGGER.debug('Scanning %s', path)
        if path:
            # We can use this to instantly add something to the library when we've added it to 'My List'.
            kodiutils.jsonrpc(method='VideoLibrary.Scan', params=dict(
                directory=path,
                showdialogs=False,
            ))
        else:
            kodiutils.jsonrpc(method='VideoLibrary.Scan')

    @staticmethod
    def clean(path=None):
        """ Cleanup the library integration. """
        _LOGGER.debug('Cleaning %s', path)
        if path:
            # We can use this to instantly remove something from the library when we've removed it from 'My List'.
            # This only works from Kodi 19 however. See https://github.com/xbmc/xbmc/pull/18562
            if kodiutils.kodi_version_major() > 18:
                kodiutils.jsonrpc(method='VideoLibrary.Clean', params=dict(
                    directory=path,
                    showdialogs=False,
                ))
            else:
                kodiutils.jsonrpc(method='VideoLibrary.Clean', params=dict(
                    showdialogs=False,
                ))
        else:
            kodiutils.jsonrpc(method='VideoLibrary.Clean')
