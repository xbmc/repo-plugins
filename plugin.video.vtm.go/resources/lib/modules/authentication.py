# -*- coding: utf-8 -*-
""" Profile module """

from __future__ import absolute_import, division, unicode_literals

import logging
from datetime import datetime, timedelta
from time import sleep

from resources.lib import kodiutils
from resources.lib.vtmgo.vtmgoauth import VtmGoAuth

_LOGGER = logging.getLogger(__name__)


class Authentication:
    """ Code responsible for the Authentication """

    def __init__(self):
        """ Initialise object """
        self._auth = VtmGoAuth(kodiutils.get_tokens_path())

    def login(self):
        """ Start the authorisation flow. """
        auth_info = self._auth.authorize()

        # Show the authorization message
        progress_dialog = kodiutils.progress(
            message=kodiutils.localize(30701,
                                       url=auth_info.get('verification_uri'),
                                       code=auth_info.get('user_code')))
        progress_dialog.update(0)

        # Check the authorization until it succeeds or the user cancels.
        delay = auth_info.get('interval')
        expiry = auth_info.get('expires_in')
        time_start = datetime.now()
        time_end = time_start + timedelta(seconds=expiry)
        while datetime.now() < time_end:
            # Update progress
            progress_dialog.update(int((datetime.now() - time_start).seconds * 100 / expiry))

            # Check if the users has cancelled the login flow
            if progress_dialog.iscanceled():
                progress_dialog.close()
                return

            # Check if we are authorized now
            check = self._auth.authorize_check()
            if check:
                progress_dialog.close()
                kodiutils.notification(kodiutils.localize(30702))
                kodiutils.redirect(kodiutils.url_for('show_main_menu'))
                return

            # Sleep a bit
            sleep(delay)

        # Close progress indicator
        progress_dialog.close()

        kodiutils.ok_dialog(message=kodiutils.localize(30703))

    def clear_tokens(self):
        """ Clear the authentication tokens """
        self._auth.logout()
        kodiutils.notification(message=kodiutils.localize(30706))

    @staticmethod
    def clear_cache():
        """ Clear the cache """
        kodiutils.invalidate_cache()
        kodiutils.notification(message=kodiutils.localize(30707))
