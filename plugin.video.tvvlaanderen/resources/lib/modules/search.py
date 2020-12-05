# -*- coding: utf-8 -*-
""" Search module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.modules.menu import Menu
from resources.lib.solocoo import Program, Channel
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.search import SearchApi

_LOGGER = logging.getLogger(__name__)


class Search:
    """ Menu code related to search """

    def __init__(self):
        """ Initialise object. """
        auth = AuthApi(username=kodiutils.get_setting('username'),
                       password=kodiutils.get_setting('password'),
                       tenant=kodiutils.get_setting('tenant'),
                       token_path=kodiutils.get_tokens_path())
        self._search_api = SearchApi(auth)

    def show_search(self, query=None):
        """ Shows the search dialog.

        :param str query:               The query to search for.
        """
        if not query:
            # Ask for query
            query = kodiutils.get_search_string(heading=kodiutils.localize(30009))  # Search
            if not query:
                kodiutils.end_of_directory()
                return

        # Do search
        items = self._search_api.search(query)

        # Generate the results
        listing = []
        for item in items:
            if isinstance(item, Program):
                if item.series_id:
                    listing.append(Menu.generate_titleitem_series(item))
                else:
                    listing.append(Menu.generate_titleitem_program(item))

            if isinstance(item, Channel) and item.available is not False:
                listing.append(Menu.generate_titleitem_channel(item))

        # Sort like we get our results back.
        kodiutils.show_listing(listing, 30009, content='files')
