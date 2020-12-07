# -*- coding: utf-8 -*-
""" Catalog module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.kodiutils import TitleItem
from resources.lib.modules.menu import Menu
from resources.lib.streamz import Category, STOREFRONT_SERIES, STOREFRONT_MOVIES
from resources.lib.streamz.api import CACHE_PREVENT, Api
from resources.lib.streamz.auth import Auth
from resources.lib.streamz.exceptions import UnavailableException

_LOGGER = logging.getLogger(__name__)


class Catalog:
    """ Menu code related to the catalog """

    def __init__(self):
        """ Initialise object """
        self._auth = Auth(kodiutils.get_setting('username'),
                          kodiutils.get_setting('password'),
                          kodiutils.get_setting('loginprovider'),
                          kodiutils.get_setting('profile'),
                          kodiutils.get_tokens_path())
        self._api = Api(self._auth)

    def show_catalog(self):
        """ Show the catalog. """
        categories = self._api.get_categories()

        listing = []
        for cat in categories:
            listing.append(TitleItem(
                title=cat.title,
                path=kodiutils.url_for('show_catalog_category', category=cat.category_id),
                info_dict=dict(
                    plot='[B]{category}[/B]'.format(category=cat.title),
                ),
            ))

        # Sort categories by default like in Streamz.
        kodiutils.show_listing(listing, 30003, content='files')

    def show_catalog_category(self, category=None):
        """ Show a category in the catalog.

        :type category: str
        """
        items = self._api.get_items(category)

        listing = []
        for item in items:
            listing.append(Menu.generate_titleitem(item))

        # Sort items by label, but don't put folders at the top.
        # Used for A-Z listing or when movies and episodes are mixed.
        kodiutils.show_listing(listing, 30003, content='files', sort=['label', 'year', 'duration'])

    def show_program(self, program):
        """ Show a program from the catalog.

        :type program: str
         """
        try:
            program_obj = self._api.get_program(program, cache=CACHE_PREVENT)  # Use CACHE_PREVENT since we want fresh data
        except UnavailableException:
            kodiutils.ok_dialog(message=kodiutils.localize(30712))  # The video is unavailable and can't be played right now.
            kodiutils.end_of_directory()
            return

        # Go directly to the season when we have only one season
        if len(program_obj.seasons) == 1:
            self.show_program_season(program, list(program_obj.seasons.values())[0].number)
            return

        # studio = CHANNELS.get(program_obj.channel, {}).get('studio_icon')

        listing = []

        # Add an '* All seasons' entry when configured in Kodi
        if kodiutils.get_global_setting('videolibrary.showallitems') is True:
            listing.append(TitleItem(
                title='* %s' % kodiutils.localize(30204),  # * All seasons
                path=kodiutils.url_for('show_catalog_program_season', program=program, season=-1),
                art_dict=dict(
                    thumb=program_obj.cover,
                    fanart=program_obj.cover,
                ),
                info_dict=dict(
                    tvshowtitle=program_obj.name,
                    title=kodiutils.localize(30204),  # All seasons
                    tagline=program_obj.description,
                    set=program_obj.name,
                    # studio=studio,
                    mpaa=', '.join(program_obj.legal) if hasattr(program_obj, 'legal') and program_obj.legal else kodiutils.localize(30216),  # All ages
                ),
            ))

        # Add the seasons
        for season in list(program_obj.seasons.values()):
            listing.append(TitleItem(
                title=kodiutils.localize(30205, season=season.number),  # Season {season}
                path=kodiutils.url_for('show_catalog_program_season', program=program, season=season.number),
                art_dict=dict(
                    thumb=season.cover,
                    fanart=program_obj.cover,
                ),
                info_dict=dict(
                    tvshowtitle=program_obj.name,
                    title=kodiutils.localize(30205, season=season.number),  # Season {season}
                    tagline=program_obj.description,
                    set=program_obj.name,
                    # studio=studio,
                    mpaa=', '.join(program_obj.legal) if hasattr(program_obj, 'legal') and program_obj.legal else kodiutils.localize(30216),  # All ages
                ),
            ))

        # Sort by label. Some programs return seasons unordered.
        kodiutils.show_listing(listing, program_obj.name, content='tvshows', sort=['label'])

    def show_program_season(self, program, season):
        """ Show the episodes of a program from the catalog.

        :type program: str
        :type season: int
        """
        try:
            program_obj = self._api.get_program(program)  # Use CACHE_AUTO since the data is just refreshed in show_program
        except UnavailableException:
            kodiutils.ok_dialog(message=kodiutils.localize(30712))  # The video is unavailable and can't be played right now.
            kodiutils.end_of_directory()
            return

        if season == -1:
            # Show all seasons
            seasons = list(program_obj.seasons.values())
        else:
            # Show the season that was selected
            seasons = [program_obj.seasons[season]]

        listing = [Menu.generate_titleitem(e) for s in seasons for e in list(s.episodes.values())]

        # Sort by episode number by default. Takes seasons into account.
        kodiutils.show_listing(listing, program_obj.name, content='episodes', sort=['episode', 'duration'])

    def show_recommendations(self, storefront):
        """ Show the recommendations.

        :type storefront: str
        """
        results = self._api.get_storefront(storefront)

        listing = []
        for item in results:
            if isinstance(item, Category):
                listing.append(TitleItem(
                    title=item.title,
                    path=kodiutils.url_for('show_recommendations_category', storefront=storefront, category=item.category_id),
                    info_dict=dict(
                        plot='[B]{category}[/B]'.format(category=item.title),
                    ),
                ))
            else:
                listing.append(Menu.generate_titleitem(item))

        if storefront == STOREFRONT_SERIES:
            label = 30005  # Series
        elif storefront == STOREFRONT_MOVIES:
            label = 30003  # Movies
        else:
            label = 30015  # Recommendations

        kodiutils.show_listing(listing, label, content='files')

    def show_recommendations_category(self, storefront, category):
        """ Show the items in a recommendations category.

        :type storefront: str
        :type category: str
        """
        result = self._api.get_storefront_category(storefront, category)

        listing = []
        for item in result.content:
            listing.append(Menu.generate_titleitem(item))

        if storefront == STOREFRONT_SERIES:
            content = 'tvshows'
        elif storefront == STOREFRONT_MOVIES:
            content = 'movies'
        else:
            content = 'files'

        kodiutils.show_listing(listing, result.title, content=content, sort=['unsorted', 'label', 'year', 'duration'])

    def show_mylist(self):
        """ Show the items in "My List". """
        mylist = self._api.get_swimlane('my-list')

        listing = []
        for item in mylist:
            item.my_list = True
            listing.append(Menu.generate_titleitem(item))

        # Sort categories by default like in Streamz.
        kodiutils.show_listing(listing, 30017, content='files', sort=['unsorted', 'label', 'year', 'duration'])

    def mylist_add(self, video_type, content_id):
        """ Add an item to "My List".

        :type video_type: str
        :type content_id: str
         """
        self._api.add_mylist(video_type, content_id)
        kodiutils.end_of_directory()

    def mylist_del(self, video_type, content_id):
        """ Remove an item from "My List".

        :type video_type: str
        :type content_id: str
        """
        self._api.del_mylist(video_type, content_id)
        kodiutils.end_of_directory()

    def show_continuewatching(self):
        """ Show the items in "Continue Watching". """
        mylist = self._api.get_swimlane('continue-watching')

        listing = []
        for item in mylist:
            titleitem = Menu.generate_titleitem(item, progress=True)

            # Add Program Name to title since this list contains episodes from multiple programs
            title = '%s - %s' % (
                titleitem.info_dict.get('tvshowtitle'),
                titleitem.info_dict.get('title'))
            titleitem.info_dict['title'] = title
            listing.append(titleitem)

        # Sort categories by default like in Streamz.
        kodiutils.show_listing(listing, 30019, content='episodes', sort='label')
