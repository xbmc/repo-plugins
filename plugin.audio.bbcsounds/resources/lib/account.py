# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

from __future__ import annotations
import re
import json
import time

from enum import IntEnum
from uuid import uuid4
from html import unescape
from urllib.parse import parse_qsl
from typing import TYPE_CHECKING

import requests
import xbmc
import xbmcgui
import xbmcaddon

from resources.lib import fetch
from resources.lib.log import log
from resources.lib import route
from resources.lib.exceptions import SignInError
from resources.lib.favourites import favourites

if TYPE_CHECKING:
    from resources.lib.plugin import Plugin


TXT_ENTER_EMAIL = 30301
TXT_ENTER_PASSW = 30302
TXT_ALREADY_SIGNED_IN = 30303
TXT_EMAIL_ADDR_UNKNOWN = 30304
TXT_LOGIN_SUCCESS = 30305
TXT_EMAIL_SENT = 30306
TXT_SIGN_IN_TIMED_OUT = 30307
TXT_SEND_NEW_LINK = 30308
TXT_SIGN_IN_CANCELLED = 30309
TXT_LOGOUT_SUCCESS = 30310
TXT_ALREADY_SIGNED_OUT = 30311

DLG_HEADER = 'BBC Account'
NOTIFY_TIME = 7000
REQ_TIMEOUT = (2.5, 4)
EMAIL_LINK_TIMEOUT = 15 * 60


def enter_email(plugin: Plugin, login_session: LoginSession, init_email: str = ''):
    """Ask the user to enter their email address.

     Check if the address is known to the BBC. If not, keep asking for the email address
     until the user cancels the keyboard.

    Return the email address or None if the user has cancelled.
    """
    email = init_email
    while True:
        email = xbmcgui.Dialog().input(plugin.translate(TXT_ENTER_EMAIL),
                                       email,
                                       xbmcgui.INPUT_ALPHANUM,
                                       autoclose=120000)
        if not email:
            return None
        if login_session.check_email(email):
            return email
        xbmcgui.Dialog().ok(DLG_HEADER, plugin.translate(TXT_EMAIL_ADDR_UNKNOWN))


@route.script
def login_with_passw(plugin: Plugin):
    """Ask the user to enter their email and password and try to log in.
    On failure, keep asking until login succeeds, or the user cancels the keyboard

    Entry point for the action 'log in with password' in settings.

    """
    log("Sign in with password")
    passw = ''

    with LoginSession() as login:
        login.initialise()
        email = enter_email(plugin, login)
        if email is None:
            return

        while True:
            passw = xbmcgui.Dialog().input(
                plugin.translate(TXT_ENTER_PASSW),
                passw,
                xbmcgui.INPUT_ALPHANUM,
                xbmcgui.ALPHANUM_HIDE_INPUT,
                autoclose=120000)
            if not passw:
                log("User has cancelled entering password.")
                return

            if login.sign_in_with_password(passw):
                plugin.settings.setBool('is-signed-in', True)
                xbmcgui.Dialog().notification(
                    DLG_HEADER,
                    plugin.translate(TXT_LOGIN_SUCCESS),
                    xbmcgui.NOTIFICATION_INFO,
                    time=NOTIFY_TIME)
                favourites.refresh()
                xbmc.executebuiltin('Container.Refresh')
                return


@route.script
def login_with_email_link(plugin: Plugin):
    """Signing in to BBC by email link.

    The user is to enter their email address and will receive an email with a link
    to sign in. Users have 15 minutes to click on the link in the email. During
    this time a progress dialog will be shown, while every 10 seconds a request wil be
    made to check if the user has clicked the link.

    When the 15 minutes have passed without the user clicking the link, the user will
    be asked whether they want to receive a new link.

    Users can cancel the sign-in process at any time by clicking on the 'Cancel' button
    on the progress dialog, or by closing the dialog.

    """
    log("Sign in by magic link")
    email_addr = ''

    with LoginSession() as login:
        login.initialise()

        email_addr = enter_email(plugin, login, email_addr)
        if not email_addr:
            return

        monitor = xbmc.Monitor()

        while True:
            login.request_email_link()

            dlg = xbmcgui.DialogProgress()
            dlg.create(
                DLG_HEADER,
                plugin.translate(TXT_EMAIL_SENT).format(email_addr=email_addr))
            dlg.update(100)

            try:
                end_t = time.monotonic() + EMAIL_LINK_TIMEOUT
                while time.monotonic() < end_t:
                    if monitor.waitForAbort(5) or dlg.iscanceled() or monitor.waitForAbort(5) or dlg.iscanceled():
                        if not monitor.abortRequested():
                            log("User cancelled waiting for login by email link.")
                            xbmcgui.Dialog().notification(
                                DLG_HEADER,
                                plugin.translate(TXT_SIGN_IN_CANCELLED),
                                xbmcgui.NOTIFICATION_INFO,
                                time=NOTIFY_TIME)
                        return

                    dlg.update(int(100 * (end_t - time.monotonic()) / EMAIL_LINK_TIMEOUT))

                    login_result = login.check_magic_link_status()
                    if login_result is True:
                        dlg.close()
                        plugin.settings.setBool('is-signed-in', True)
                        favourites.refresh()
                        xbmcgui.Dialog().ok(DLG_HEADER, plugin.translate(TXT_LOGIN_SUCCESS))
                        xbmc.executebuiltin('Container.Refresh')
                        return
                    elif login_result is False:
                        # The link probably timed out before just before our timer expired.
                        break
            finally:
                dlg.close()

            log("Magic link confirmation timed out - button in email is not pressed.")
            # Inform the user that the link has timed out and ask to send the link again.
            if xbmcgui.Dialog().yesno(
                    DLG_HEADER,
                    plugin.translate(TXT_SIGN_IN_TIMED_OUT)):
                log("User wants a new magic link.")
                # Re-initialise before looping over and send magic link again.
                login.check_email(email_addr)
            else:
                return


@route.script
def log_out(plugin: Plugin):
    """Entry point for the action 'log out' in settings."""

    currently_signed_in = plugin.settings.getBool('is-signed-in')
    # Always do a sign-out, just to be sure.
    perform_sign_out()
    plugin.settings.setBool('is-signed-in', False)
    favourites.clear()
    if currently_signed_in:
        log("log_out warning: The user was already signed out of their BBC account.")
        xbmcgui.Dialog().notification(DLG_HEADER,
                                      plugin.translate(TXT_LOGOUT_SUCCESS),
                                      xbmcgui.NOTIFICATION_INFO,
                                      time=7000)
    else:
        log("Signed out of BBC account.")
        xbmcgui.Dialog().notification(DLG_HEADER,
                                      plugin.translate(TXT_ALREADY_SIGNED_OUT),
                                      xbmcgui.NOTIFICATION_INFO,
                                      time=7000)


class LoginStatus(IntEnum):
    UNKNOWN = 0
    INITIALISED = 1
    EMAIL_ADDR_CHECKED = 2
    EMAIL_LINK_SENT = 3
    SIGNED_IN = 4
    FAILED = 5
    CANCELLED = 6


class LoginSession:
    ACCOUNT_DOMAIN = 'https://account.bbc.com'
    HEADERS = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0'}

    def __init__(self):
        self._cookies = fetch.cookie_jar()
        self._http_session = requests.Session()
        self._http_session.cookies = self._cookies
        self._email = None
        self._query_params = {}
        self._jti = None
        self._state = LoginStatus.UNKNOWN
        self._http_session.headers.update(self.HEADERS)

    @property
    def status(self):
        return self._state

    def initialise(self):
        resp = self._http_session.get('https://session.bbc.co.uk/session',
                                      params={'sequenceId': str(uuid4())},
                                      timeout=REQ_TIMEOUT)
        if resp.url.startswith('https://www.bbc.co.uk/'):
            # Being redirected to the main page: already signed-in, or expired tokens have been refreshed
            log("Account sign-in aborted; this device is already signed in to a BBC account.")
            localise = xbmcaddon.Addon().getLocalizedString
            raise SignInError(localise(TXT_ALREADY_SIGNED_IN))
        querystring = unescape(resp.url.split('?')[1])
        self._query_params = dict(parse_qsl(querystring))
        self._query_params.pop('jsEnabled', None)       # No longer present, but just in case.
        self._query_params.pop('purpose', None)         # param purpose=free found on international access.
        self._query_params.update({
            'journeyGroupType': 'sign-in',
            'ab': 'o13',
            'ptrt': 'https://www.bbc.co.uk/'
        })
        self._state = LoginStatus.INITIALISED
        return True

    def check_email(self, email):
        """Check if the email address is known to the BBC.

        """
        if self._state is not LoginStatus.INITIALISED:
            self.initialise()
        resp = self._http_session.post(self.ACCOUNT_DOMAIN + '/auth',
                                       params=self._query_params,
                                       data={'username': email},
                                       timeout=REQ_TIMEOUT,
                                       allow_redirects=False)
        resp.raise_for_status()
        # Both valid in invalid email addresses just return 200 OK. Serious errors, like invalid
        # parameters, may be redirected via session.bbc.co.uk back to /auth.
        if resp.status_code == 200:
            match = re.search(r'window.bbcAccount.locals\s?=\s?{(.+?)};', resp.text, re.DOTALL)
            # noinspection unresolved-references
            data = json.loads('{' + match[1] + '}')
            errors = data['signIn']['initialErrors']
            # On success, `errors` is an empty dict.
            if not errors:
                self._email = email
                self._state = LoginStatus.EMAIL_ADDR_CHECKED
                return True
        self._state = LoginStatus.FAILED
        return False

    def sign_in_with_password(self, password):
        """Sign in to the BBC account by providing an email address and password.

        """
        if self._state is not LoginStatus.EMAIL_ADDR_CHECKED:
            raise RuntimeError(f'Invalid LoginSession status: {self._state} - '
                               'Can only perform password sign in right after the email address has been checked.')
        resp = self._http_session.post(self.ACCOUNT_DOMAIN + '/auth/password',
                                       params=self._query_params,
                                       data={'username': self._email, 'password': password},
                                       timeout=REQ_TIMEOUT)
        resp.raise_for_status()
        # If sign in is successful, the response should redirect several times and end up on
        # www.bbc.co.uk. The authentication cookies are set in the intermediate responses.
        # Authentication failures are redirected to account.bbc.co.uk/auth.
        if not resp.url.startswith('https://www.bbc.co.uk/'):
            return False
        self._state = LoginStatus.SIGNED_IN
        return True

    def request_email_link(self):
        """Ask the BBC to send an email with a link to sign in."""

        # Post a form to allow the BBC to send a link to the user's email.
        if self._state is not LoginStatus.EMAIL_ADDR_CHECKED:
            raise RuntimeError(f'Invalid LoginSession status: {self._state} - '
                               'Can only request email link right after the email address has been checked.')

        params = {'userJourney': 'magicLink'}
        params.update(self._query_params)
        resp = self._http_session.post(self.ACCOUNT_DOMAIN + '/auth',
                                       params=params,
                                       data={'username': self._email,
                                             'showExperimentError': 'false'},
                                       timeout=REQ_TIMEOUT)
        resp.raise_for_status()
        if resp.status_code == 200:
            match = re.search(r'"jti":\s?"([^"]+)"', resp.text)
            # noinspection unresolved-references
            self._jti = match[1]
            self._state = LoginStatus.EMAIL_LINK_SENT
        else:
            self._state = LoginStatus.FAILED

    def check_magic_link_status(self):
        """Check if the user has clicked the magic link in their email.

        """
        if self._state is not LoginStatus.EMAIL_LINK_SENT:
            raise RuntimeError(f'Invalid LoginSession status: {self._state} - '
                               'Can only perform link verification after the link has been sent.')

        verify_params = {'authorise': 'true', 'userJourney': 'magicLink', 'showExperimentError': 'false'}
        verify_params.update(self._query_params)
        resp = self._http_session.post(
            self.ACCOUNT_DOMAIN + '/api/magic-link/authenticate',
            params=verify_params,
            json={'email': self._email, 'jti': self._jti},
            timeout=REQ_TIMEOUT)

        if resp.status_code == 200:
            resp_data = json.loads(resp.content)
            resp = self._http_session.get(resp_data['redirectUrl'], timeout=REQ_TIMEOUT)
            if resp.url.startswith('https://www.bbc.co.uk/'):
                self._state = LoginStatus.SIGNED_IN
                return True
            else:
                log('LoginSession._check_magic_link_response: Unexpected redirect: %s', resp.url)
                raise SignInError("Unexpected sign in result, Check the log for more details.")
        if resp.status_code == 401:
            resp_data = json.loads(resp.content)
            if resp_data.get('message') != 'notValidatedTokenError':
                # The link probably timed out just before our timer expired.
                log('LoginSession._check_magic_link_response: Unexpected 401 message: %s', resp_data.get('message'))
                self._state = LoginStatus.FAILED
                return False
        else:
            resp.raise_for_status()
        return None

    def close(self):
        self._http_session.close()
        if self._state is LoginStatus.SIGNED_IN:
            self._cookies.save(ignore_discard=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def perform_sign_out():
    """Sign out from your BBC account

    Clearing the cookie jar is absolutely enough to get signed out, but
    informing the BBC may revoke existing auth cookies and prevent misuse.

    """
    sign_out_url = "https://account.bbc.com/signout"
    try:
        fetch.get(sign_out_url, timeout=(2.5, 2))
    except Exception as err:
        log("Failed to logout at the BCC: %r", err)
    cookie_jar = fetch.cookie_jar()
    cookie_jar.clear()
    cookie_jar.save()
