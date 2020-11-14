# -*- coding: utf-8 -*-
""" Metadata module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.streamz import Movie, Program
from resources.lib.streamz.api import Api
from resources.lib.streamz.auth import Auth

_LOGGER = logging.getLogger(__name__)


class Metadata:
    """ Code responsible for the refreshing of the metadata """

    def __init__(self):
        """ Initialise object """
        self._auth = Auth(kodiutils.get_setting('username'),
                          kodiutils.get_setting('password'),
                          kodiutils.get_setting('loginprovider'),
                          kodiutils.get_setting('profile'),
                          kodiutils.get_tokens_path())
        self._api = Api(self._auth)

    def update(self):
        """ Update the metadata with a foreground progress indicator. """
        # Create progress indicator
        progress = kodiutils.progress(message=kodiutils.localize(30715))  # Updating metadata

        def update_status(i, total):
            """ Update the progress indicator. """
            progress.update(int(((i + 1) / total) * 100), kodiutils.localize(30716, index=i + 1, total=total))  # Updating metadata ({index}/{total})
            return progress.iscanceled()

        self.fetch_metadata(callback=update_status)

        # Close progress indicator
        progress.close()

    def fetch_metadata(self, callback=None):
        """ Fetch the metadata for all the items in the catalog.

        :type callback: callable
        """
        # Fetch a list of all items from the catalog
        items = self._api.get_items()
        count = len(items)

        # Loop over all of them and download the metadata
        for index, item in enumerate(items):
            if isinstance(item, Movie):
                self._api.get_movie(item.movie_id)
            elif isinstance(item, Program):
                self._api.get_program(item.program_id)

            # Run callback after every item
            if callback and callback(index, count):
                # Stop when callback returns False
                return False

        return True

    @staticmethod
    def clean():
        """ Clear metadata (called from settings). """
        kodiutils.invalidate_cache()
        kodiutils.set_setting('metadata_last_updated', '0')
        kodiutils.ok_dialog(message=kodiutils.localize(30714))  # Local metadata is cleared
