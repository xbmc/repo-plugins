# -*- coding: utf-8 -*-
""" Profile module """

from __future__ import absolute_import, division, unicode_literals

import logging
from datetime import datetime, timedelta
from time import sleep

from resources.lib import kodiutils
from resources.lib.kodiutils import TitleItem
from resources.lib.streamz import PRODUCT_STREAMZ, PRODUCT_STREAMZ_KIDS
from resources.lib.streamz.auth import Auth

_LOGGER = logging.getLogger(__name__)


class Authentication:
    """ Code responsible for the Authentication """

    def __init__(self):
        """ Initialise object """
        self._auth = Auth(kodiutils.get_tokens_path())

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

    def select_profile(self, key=None):
        """ Show your profiles.
        :type key: str
        """
        profiles = self._auth.get_profiles()

        # Show warning when you have no profiles
        if not profiles:
            # Your account has no profiles defined. Please login on www.streamz.be/streamz and create a profile.
            kodiutils.ok_dialog(message=kodiutils.localize(30704))
            kodiutils.end_of_directory()
            return

        # Select the first profile when you only have one
        if len(profiles) == 1:
            key = profiles[0].key

        # Save the selected profile
        if key:
            profile = [x for x in profiles if x.key == key][0]
            _LOGGER.debug('Setting profile to %s', profile)
            self._auth.set_profile(profile.key, PRODUCT_STREAMZ_KIDS if profile.kids_profile else PRODUCT_STREAMZ)

            kodiutils.redirect(kodiutils.url_for('show_main_menu'))
            return

        # Show profile selection when you have multiple profiles
        listing = [
            TitleItem(
                title=self._get_profile_name(p),
                path=kodiutils.url_for('select_profile', key=p.key),
                art_dict=dict(
                    icon='DefaultUser.png'
                ),
                info_dict=dict(
                    plot=p.name,
                ),
            )
            for p in profiles
        ]

        kodiutils.show_listing(listing, sort=['unsorted'], category=30057)  # Select Profile

    @staticmethod
    def _get_profile_name(profile):
        """ Get a descriptive string of the profile.
        :type profile: resources.lib.streamz.Profile
        """
        title = profile.name

        # Convert the Streamz Profile color to a matching Kodi color
        color_map = {
            '#F20D3A': 'red',
            '#FF0A5A': 'crimson',
            '#FF4B00': 'darkorange',
            '#FED71F': 'gold',
            '#5EFF74': 'palegreen',
            '#0DF2E8': 'turquoise',
            '#226DFF': 'dodgerblue',
            '#6900CC': 'blueviolet',
        }
        if color_map.get(profile.color.upper()):
            title = '[COLOR %s]%s[/COLOR]' % (color_map.get(profile.color.upper()), kodiutils.to_unicode(title))

        # Append (Kids)
        if profile.kids_profile:
            title = "%s (Kids)" % title

        return title

    def clear_tokens(self):
        """ Clear the authentication tokens """
        self._auth.logout()
        kodiutils.notification(message=kodiutils.localize(30706))

    @staticmethod
    def clear_cache():
        """ Clear the cache """
        kodiutils.invalidate_cache()
        kodiutils.notification(message=kodiutils.localize(30707))
