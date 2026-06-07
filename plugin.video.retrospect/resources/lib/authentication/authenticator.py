# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Optional

from .authenticationhandler import AuthenticationHandler
from .authenticationresult import AuthenticationResult
from ..logger import Logger
from ..vault import Vault
from ..xbmcwrapper import XbmcWrapper


class Authenticator(object):
    def __init__(self, handler: AuthenticationHandler):
        """ Main logic handler for authentication.

        :param AuthenticationHandler handler:   The authentication handler to use.

        """

        if handler is None:
            raise ValueError("No authenication handler specified.")

        if not isinstance(handler, AuthenticationHandler):
            raise ValueError("Invalid authenication handler specified.")

        self.__handler = handler

    def log_on(self, username: str, password: Optional[str] = None, setting_id: Optional[str] = None, channel_guid: Optional[str] = None):
        """ Performs the logon of a user. Either with the specified password or via a lookup. Also
        logs off a previous user if the username has changed from previous logins.

        :param username:        The username
        :param password:        The password to use
        :param setting_id:      The ID of the setting where the password is stored
        :param channel_guid:    The GUID of the channel, if the password is stored in a
                                channel setting.

        :returns: An indication of a successful login.

        """

        result = self.__handler.active_authentication()
        logged_on_user = result.username

        # Check if the existing login is the same as the requested one.
        if logged_on_user and (not username or logged_on_user.lower() != username.lower()):
            Logger.warning("Existing but different authenticated user (%s) found. Logging of first.",
                           self.__safe_log(logged_on_user))
            self.__handler.log_off(logged_on_user)

        elif logged_on_user and logged_on_user == username:
            Logger.info("Existing authenticated user (%s) found.", self.__safe_log(logged_on_user))
            return result

        if not username:
            Logger.warning("No username specified")
            return AuthenticationResult(None)

        Logger.info("Logging on user: %s", self.__safe_log(username))
        if password is None:
            Logger.info("Retrieving password for user: %s", self.__safe_log(username))
            v = Vault()
            if channel_guid:
                password = v.get_channel_setting(channel_guid, setting_id)
            else:
                password = v.get_setting(setting_id)

        if not password:
            Logger.error("No password specified")
            return AuthenticationResult(None)

        result = self.__handler.log_on(username, password)
        if result.error:
            XbmcWrapper.show_dialog(None, result.error)
        return result

    def active_authentication(self) -> AuthenticationResult:
        """ Check if the user with the given name is currently authenticated.

        :returns: a AuthenticationResult with the account data
        :rtype: AuthenticationResult

        """

        return self.__handler.active_authentication()

    def get_authentication_token(self) -> Optional[str]:
        """ Fetches an authentication token for the given login

        :return: token value

        """

        return self.__handler.get_authentication_token()

    def log_off(self, username, force=True):
        """ Logs off the currently authenticated user, clearing stored tokens.

        :param str username:    The username to log off.
        :param bool force:      If True, log off regardless of whether the stored
                                username matches the given one.

        """

        result = self.__handler.active_authentication()
        if not result.logged_on:
            Logger.debug("User was not logged on.")
            return

        logged_on_user = result.username
        if logged_on_user is not None and (force or logged_on_user == username):
            result = self.__handler.log_off(logged_on_user)
            if result:
                Logger.debug("Logged off successfully")
            else:
                Logger.error("Log off failed")

    def __safe_log(self, text):
        return "".join([text[i] if i % 2 == 0 else "*" for i in range(0, len(text))])
