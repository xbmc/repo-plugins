# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib.addonsettings import AddonSettings
from resources.lib.addonsettings import LOCAL
from resources.lib.authentication.authenticationresult import AuthenticationResult


class AuthenticationHandler(object):
    def __init__(self, realm, device_id):
        """ Initializes a handler for the authentication provider

        :param str realm:
        :param str|None device_id:

        """

        if not realm:
            raise ValueError("Missing 'realm' initializer.")

        self._device_id = device_id
        self._realm = realm
        return

    @property
    def realm(self):
        return self._realm

    def log_on(self, username, password):
        """ Peforms the logon of a user.

        :param str username:    The username
        :param str password:    The password to use

        :returns: a AuthenticationResult with the result of the log on
        :rtype: AuthenticationResult

        """
        raise NotImplementedError

    def active_authentication(self):
        """ Check if the user with the given name is currently authenticated.

        :returns: a AuthenticationResult with the account data.
        :rtype: AuthenticationResult

        """

        raise NotImplementedError

    def log_off(self, username):
        """ Check if the user with the given name is currently authenticated.

        :param str username:    The username to log off

        :returns: Indication of success
        :rtype: bool

        """

        raise NotImplementedError

    def get_authentication_token(self):
        """ Returns a token that can be used for authentication of the current session.

        The user needs to be logged in for this.

        :return: An authentication token.
        :rtype: str

        """
        raise NotImplementedError

    def _store_current_user_in_settings(self, username):
        """ Store the current user in the local settings.

        :param str|None username: The currently authenticated user

        Can be used if there is no other means of retrieving the currently authenticated user.

        """

        store = AddonSettings.store(LOCAL)
        store.set_setting("{}:authenticated_user".format(self._realm), username)

    def _get_current_user_in_settings(self):
        """ Retrieves the current user in the local settings.

        Can be used if there is no other means of retrieving the currently authenticated user.

        """

        store = AddonSettings.store(LOCAL)
        return store.get_setting("{}:authenticated_user".format(self._realm), default=None)
