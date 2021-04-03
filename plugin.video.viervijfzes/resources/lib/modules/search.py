# -*- coding: utf-8 -*-
""" Search module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.modules.menu import Menu
from resources.lib.viervijfzes.search import SearchApi

_LOGGER = logging.getLogger(__name__)


class Search:
    """ Menu code related to search """

    def __init__(self):
        """ Initialise object """
        self._search = SearchApi()

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
            items = self._search.search(query)
        except Exception as ex:  # pylint: disable=broad-except
            kodiutils.notification(message=str(ex))
            kodiutils.end_of_directory()
            return

        # Display results
        listing = [Menu.generate_titleitem(item) for item in items]

        # Sort like we get our results back.
        kodiutils.show_listing(listing, 30009, content='tvshows')
