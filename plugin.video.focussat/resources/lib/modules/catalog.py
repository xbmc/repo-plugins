# -*- coding: utf-8 -*-
""" Catalog module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.kodiutils import TitleItem
from resources.lib.modules.menu import Menu
from resources.lib.solocoo import VodEpisode, VodMovie, VodSeries
from resources.lib.solocoo.asset import AssetApi
from resources.lib.solocoo.auth import AuthApi

_LOGGER = logging.getLogger(__name__)


class Catalog:
    """ Menu code related to the Catalog. """

    def __init__(self):
        """ Initialise object. """
        auth = AuthApi(username=kodiutils.get_setting('username'),
                       password=kodiutils.get_setting('password'),
                       tenant=kodiutils.get_setting('tenant'),
                       token_path=kodiutils.get_tokens_path())
        self._api = AssetApi(auth)

    def show_overview(self, catalogs=False):
        """ Shows an overview. """
        listing = []

        if catalogs:
            # Show all catalogs
            catalogs = self._api.get_collection_catalogs()
            for catalog in catalogs:
                title_item = TitleItem(
                    title=catalog.title,
                    path=kodiutils.url_for('show_catalog_by_catalog', catalog=catalog.uid),
                    art_dict={
                        'icon': catalog.cover,
                        'thumb': catalog.cover,
                    },
                )
                listing.append(title_item)

        else:
            # Show catalogs
            title_item = TitleItem(
                title=kodiutils.localize(30013),  # Show catalogs
                path=kodiutils.url_for('show_catalog_catalogs'),
                art_dict=dict(
                    icon='DefaultAddonPVRClient.png',
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30014),
                )
            )
            listing.append(title_item)

            # Show genres
            genres = self._api.get_collection_genres()
            for genre in genres:
                title_item = TitleItem(
                    title=genre.title,
                    path=kodiutils.url_for('show_catalog_by_query', query=genre.query),
                )

                listing.append(title_item)

        kodiutils.show_listing(listing, 30011, content='files')

    def show_by_catalog(self, catalog):
        """ Show an overview by catalog. """
        listing = []

        genres = self._api.get_collection_genres(catalog)
        for genre in genres:
            title_item = TitleItem(
                title=genre.title,
                path=kodiutils.url_for('show_catalog_by_query', query=genre.query),
            )

            listing.append(title_item)

        kodiutils.show_listing(listing, 30011, content='files')

    def show_by_query(self, query):
        """ Show an overview with a query. """
        listing = []

        assets = self._api.query_assets(query)
        for asset in assets:
            if isinstance(asset, VodMovie):
                listing.append(Menu.generate_titleitem_vod_movie(asset))

            if isinstance(asset, VodSeries):
                listing.append(Menu.generate_titleitem_vod_series(asset))

            if isinstance(asset, VodEpisode):
                listing.append(Menu.generate_titleitem_vod_episode(asset))

        kodiutils.show_listing(listing, 30011, content='files')

    def show_series(self, asset):
        """ Show an overview of the seasons of a series. """
        listing = []

        seasons = self._api.get_collection_seasons(asset)
        for season in seasons:
            listing.append(Menu.generate_titleitem_vod_season(season))

        kodiutils.show_listing(listing, 30011, content='seasons')
