# -*- coding: utf-8 -*-
""" Search module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.modules.menu import Menu
from resources.lib.streamz.api import Api
from resources.lib.streamz.auth import Auth

_LOGGER = logging.getLogger(__name__)


class Search:
    """ Menu code related to search """

    def __init__(self,):
        """ Initialise object """
        auth = Auth(kodiutils.get_tokens_path())
        self._api = Api(auth.get_tokens())

    def show_search(self, query=None):
        """ Shows the search dialog.

        :type query: str
        """
        if not query:
            # Ask for query
            query = kodiutils.get_search_string(heading=kodiutils.localize(30009))  # Search Streamz
            if not query:
                kodiutils.end_of_directory()
                return

        # Do search
        try:
            items = self._api.do_search(query)
        except Exception as ex:  # pylint: disable=broad-except
            kodiutils.notification(message=str(ex))
            kodiutils.end_of_directory()
            return

        # Display results
        show_unavailable = kodiutils.get_setting_bool('interface_show_unavailable')
        listing = []
        for item in items:
            if show_unavailable or item.available:
                listing.append(Menu.generate_titleitem(item))

        # Sort like we get our results back.
        kodiutils.show_listing(listing, 30009, content='tvshows')
