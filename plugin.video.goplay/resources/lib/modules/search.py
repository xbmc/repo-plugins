# -*- coding: utf-8 -*-
""" Search module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.goplay.auth import AuthApi
from resources.lib.goplay.content import ContentApi
from resources.lib.modules.menu import Menu

_LOGGER = logging.getLogger(__name__)


class Search:
    """ Menu code related to search """

    def __init__(self):
        """ Initialise object """
        if not kodiutils.has_credentials():
            kodiutils.open_settings()
        self._auth = AuthApi(kodiutils.get_setting('username'), kodiutils.get_setting('password'), kodiutils.get_tokens_path())
        self._api = ContentApi(self._auth, cache_path=kodiutils.get_cache_path())

    def show_search(self, query=None):
        """ Shows the search dialog
        :type query: str
        """
        if not query:
            # Ask for query
            query = kodiutils.get_search_string(heading=kodiutils.localize(30009))  # Search
            if not query:
                kodiutils.end_of_directory()
                return

        # Do search
        try:
            _, items = self._api.search(query)
        except Exception as ex:  # pylint: disable=broad-except
            kodiutils.notification(message=str(ex))
            kodiutils.end_of_directory()
            return

        # Display results
        listing = [Menu.generate_titleitem(item) for item in items]

        # Sort like we get our results back.
        kodiutils.show_listing(listing, 30009, content='tvshows')
