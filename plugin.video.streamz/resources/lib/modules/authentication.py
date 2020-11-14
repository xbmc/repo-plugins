# -*- coding: utf-8 -*-
""" Profile module """

from __future__ import absolute_import, division, unicode_literals

import logging

from requests import HTTPError

from resources.lib import kodiutils
from resources.lib.kodiutils import TitleItem
from resources.lib.streamz.api import Api
from resources.lib.streamz.auth import Auth
from resources.lib.streamz.exceptions import InvalidLoginException, LoginErrorException, NoStreamzSubscriptionException, NoTelenetSubscriptionException

_LOGGER = logging.getLogger(__name__)


class Authentication:
    """ Code responsible for the Authentication """

    def __init__(self):
        """ Initialise object """
        self._auth = Auth(kodiutils.get_setting('username'),
                          kodiutils.get_setting('password'),
                          kodiutils.get_setting('loginprovider'),
                          kodiutils.get_setting('profile'),
                          kodiutils.get_tokens_path())
        self._api = Api(self._auth)

    @staticmethod
    def verify_credentials():
        """ Verify if the user has credentials and if they are valid. """
        retry = False
        while True:

            # Check if the user has credentials
            if retry or not kodiutils.get_setting('username') or not kodiutils.get_setting('password'):

                # Ask user to fill in his credentials
                if not kodiutils.yesno_dialog(message=kodiutils.localize(30701)):  # You need to configure your credentials...
                    # The user doesn't want to do this. Abort to Home screen.
                    return False

                kodiutils.open_settings()

            try:
                # Create Auth object so we actually do a login.
                Auth(kodiutils.get_setting('username'),
                     kodiutils.get_setting('password'),
                     kodiutils.get_setting('loginprovider'),
                     kodiutils.get_setting('profile'),
                     kodiutils.get_tokens_path())
                return True

            except InvalidLoginException:
                kodiutils.ok_dialog(message=kodiutils.localize(30203))  # Your credentials are not valid!
                retry = True

            except NoStreamzSubscriptionException:
                kodiutils.ok_dialog(message=kodiutils.localize(30201))  # Your Streamz account has no valid subscription!
                retry = True

            except NoTelenetSubscriptionException:
                kodiutils.ok_dialog(message=kodiutils.localize(30202))  # Your Telenet account has no valid subscription!
                retry = True

            except LoginErrorException as exc:
                kodiutils.ok_dialog(message=kodiutils.localize(30702, code=exc.code))  # Unknown error while logging in: {code}
                return False

            except HTTPError as exc:
                kodiutils.ok_dialog(message=kodiutils.localize(30702, code='HTTP %d' % exc.response.status_code))  # Unknown error while logging in: {code}
                return False

    def select_profile(self, key=None):
        """ Show your profiles.

        :type key: str
        """
        profiles = self._auth.get_profiles()

        # Show warning when you have no profiles
        if not profiles:
            # Your account has no profiles defined. Please login on www.streamz.be/streamz and create a profile.
            kodiutils.ok_dialog(message=kodiutils.localize(30703))
            kodiutils.end_of_directory()
            return

        # Select the first profile when you only have one
        if len(profiles) == 1:
            key = profiles[0].key

        # Save the selected profile
        if key:
            profile = [x for x in profiles if x.key == key][0]
            _LOGGER.debug('Setting profile to %s', profile)
            kodiutils.set_setting('profile', '%s:%s' % (profile.key, profile.product))
            kodiutils.set_setting('profile_name', profile.name)

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
        if profile.product == 'STREAMZ_KIDS':
            title = "%s (Kids)" % title

        return title
