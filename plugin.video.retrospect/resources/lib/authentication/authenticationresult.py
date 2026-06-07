# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Optional


class AuthenticationResult:
    username: str
    logged_on: bool
    existing_login: bool
    has_premium: bool
    uid: Optional[str]
    error: Optional[str]
    jwt: Optional[str]

    def __init__(self, username: str, has_premium: bool = False, existing_login: bool = False,
                 uid: Optional[str] = None, error: Optional[str] = None, jwt: Optional[str] = None):
        """ Log on result object

        :param username:       The user name that is used for logging in.
        :param existing_login: Indication whether the user was already logged in and this
                               was just a the renew of the authentication session.
        :param has_premium:    Indication whether the user has a premium/paid account.
        :param uid:            The internal user id for the username
        :param error:          Error value
        :param jwt             A possible JWT value.

        """

        self.username = username
        self.logged_on = bool(username)
        self.existing_login = existing_login
        self.has_premium = has_premium
        self.uid = uid
        self.error = error
        self.jwt = jwt

    def __str__(self) -> str:
        if not self.logged_on:
            return "Not logged on"

        return "Logged on with premium rights" if self.has_premium else "Logged on as normal user"
