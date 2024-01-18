# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Optional

from resources.lib.addonsettings import AddonSettings
from resources.lib.addonsettings import LOCAL
from resources.lib.authentication.authenticationresult import AuthenticationResult


class AuthenticationHandler(object):
    def __init__(self, realm: str, device_id: Optional[str]):
        """ Initializes a handler for the authentication provider

        :param realm:
        :param device_id:

        """

        if not realm:
            raise ValueError("Missing 'realm' initializer.")

        self._device_id = device_id
        self._realm = realm
        return

    @property
    def realm(self):
        return self._realm

    def log_on(self, username: str, password: str) -> AuthenticationResult:
        """ Peforms the logon of a user.

        :param username:    The username
        :param password:    The password to use

        :returns: a AuthenticationResult with the result of the log on

        """

        raise NotImplementedError

    def active_authentication(self) -> AuthenticationResult:
        """ Check if the user with the given name is currently authenticated.

        :returns: a AuthenticationResult with the account data.

        """

        raise NotImplementedError

    def log_off(self, username) -> bool:
        """ Check if the user with the given name is currently authenticated.

        :param str username:    The username to log off

        :returns: Indication of success

        """

        raise NotImplementedError

    def get_authentication_token(self) -> Optional[str]:
        """ Returns a token that can be used for authentication of the current session.

        The user needs to be logged in for this.

        :return: An authentication token.

        """

        raise NotImplementedError

    def _store_current_user_in_settings(self, username: str):
        """ Store the current user in the local settings.

        :param username: The currently authenticated user

        Can be used if there is no other means of retrieving the currently authenticated user.

        """

        store = AddonSettings.store(LOCAL)
        store.set_setting("{}:authenticated_user".format(self._realm), username)

    def _get_current_user_in_settings(self) -> str:
        """ Retrieves the current user in the local settings.

        Can be used if there is no other means of retrieving the currently authenticated user.

        """

        store = AddonSettings.store(LOCAL)
        return store.get_setting("{}:authenticated_user".format(self._realm), default=None)
