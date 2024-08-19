from xbmcgui import Dialog, DialogProgress
from jurialmunkey.parser import try_int, boolean
from jurialmunkey.window import get_property
from tmdbhelper.lib.addon.plugin import get_localized, get_setting, ADDONPATH
from tmdbhelper.lib.api.request import RequestAPI
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.addon.thread import has_property_lock
from tmdbhelper.lib.api.api_keys.trakt import CLIENT_ID, CLIENT_SECRET, USER_TOKEN
from tmdbhelper.lib.api.trakt.content import TraktMethods


API_URL = 'https://api.trakt.tv/'


class TraktAPI(RequestAPI, TraktMethods):

    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    user_token = USER_TOKEN

    def __init__(
            self,
            client_id=None,
            client_secret=None,
            user_token=None,
            force=False,
            page_length=1):
        super(TraktAPI, self).__init__(req_api_url=API_URL, req_api_name='TraktAPI', timeout=20)
        self.authorization = ''
        self.attempted_login = boolean(get_property('TraktAttemptedLogin'))
        self.dialog_noapikey_header = f'{get_localized(32007)} {self.req_api_name} {get_localized(32011)}'
        self.dialog_noapikey_text = get_localized(32012)
        TraktAPI.client_id = client_id or self.client_id
        TraktAPI.client_secret = client_secret or self.client_secret
        TraktAPI.user_token = user_token or self.user_token
        self.headers = {'trakt-api-version': '2', 'trakt-api-key': self.client_id, 'Content-Type': 'application/json'}
        self.last_activities = {}
        self.sync_activities = {}
        self.sync = {}
        self.sync_item_limit = 20 * max(get_setting('pagemulti_sync', 'int'), page_length)
        self.item_limit = 20 * max(get_setting('pagemulti_trakt', 'int'), page_length)
        self.login() if force else self.authorize()

    def authorize(self, login=False, confirmation=False):
        # Already got authorization so return credentials
        if not confirmation and self.authorization:
            return self.authorization

        # Check for saved credentials from previous login
        token = self.get_token()

        # No saved credentials and user trying to use a feature that requires authorization so ask them to login
        if not token and login:
            self.ask_for_login()

        if not confirmation:
            return self.authorization

        return self.confirm_authorization()

    def ask_for_login(self):
        # We only ask once per instance to avoid spamming user with login prompts
        if self.attempted_login:
            return
        self.attempted_login = True
        x = Dialog().yesnocustom(
            self.dialog_noapikey_header,
            self.dialog_noapikey_text,
            nolabel=get_localized(222),
            yeslabel=get_localized(186),
            customlabel=get_localized(13170)
        )
        routes = {
            1: self.login,  # Yes (OK)
            2: lambda: get_property('TraktAttemptedLogin', 'True')  # Custom (Never)
        }
        try:
            return routes[x]()
        except KeyError:
            return

    def confirm_authorization(self):
        from tmdbhelper.lib.addon.tmdate import get_timestamp
        from jurialmunkey.window import WindowProperty

        if not self.authorization:
            return
        if boolean(get_property('TraktIsAuth')):
            return self.authorization
        if get_timestamp(get_property('TraktRefreshTimeStamp', is_type=float) or 0):
            return self.authorization

        if has_property_lock('TraktCheckingAuth'):  # Wait if another thread is checking authorization
            if boolean(get_property('TraktIsDown')):  # Check if other instance reported Trakt down
                return  # Trakt is down so do nothing
            self.get_token()  # Get the token set in the other thread
            return self.authorization  # Another thread checked token so return

        def _check_authorization(attempt=1):
            response = self.check_authorization()

            # Unauthorised so attempt a refresh
            if attempt == 1 and response in [None, 401]:
                kodi_log('Trakt unauthorized!', 1)
                if not self.refresh_token():
                    return
                return _check_authorization(attempt=attempt + 1)

            # Trakt database is down
            if response in [500, 503]:
                kodi_log('Trakt is currently down!', 1)
                get_property('TraktIsDown', 'True')
                return

            if not self.authorization:
                return

            kodi_log('Trakt user account authorized', 1)
            get_property('TraktIsDown', clear_property=True)
            return get_property('TraktIsAuth', 'True')

        def _confirm_authorization():
            from timeit import default_timer as timer
            from tmdbhelper.lib.addon.logger import TimerFunc
            with TimerFunc('Trakt authorization check took', inline=True) as tf:
                if not _check_authorization():
                    return
                if not get_setting('startup_notifications'):
                    return
                total_time = timer() - tf.timer_a
                notification = f'Trakt authorized in {total_time:.3f}s'
                Dialog().notification('TMDbHelper', notification, icon=f'{ADDONPATH}/icon.png')

        # Set a thread lock property
        with WindowProperty(('TraktCheckingAuth', 1)):
            _confirm_authorization()

        return self.authorization

    def check_authorization(self):
        url = 'https://api.trakt.tv/sync/last_activities'
        response = self.get_simple_api_request(url, headers=self.headers)
        try:
            return response.status_code
        except AttributeError:
            return

    def get_stored_token(self):
        from tmdbhelper.lib.files.futils import json_loads as data_loads
        try:
            token = data_loads(self.user_token.value) or {}
        except Exception as exc:
            token = {}
            kodi_log(exc, 1)
        return token

    def get_token(self):
        token = self.get_stored_token()
        if not token.get('access_token'):
            return
        self.authorization = token
        self.headers['Authorization'] = f'Bearer {self.authorization.get("access_token")}'
        return token

    def logout(self):
        token = self.get_stored_token()

        if not Dialog().yesno(get_localized(32212), get_localized(32213)):
            return

        if token:
            response = self.get_api_request('https://api.trakt.tv/oauth/revoke', postdata={
                'token': token.get('access_token', ''),
                'client_id': self.client_id,
                'client_secret': self.client_secret})
            if response and response.status_code == 200:
                msg = get_localized(32216)
                self.user_token.value = ''
            else:
                msg = get_localized(32215)
        else:
            msg = get_localized(32214)

        Dialog().ok(get_localized(32212), msg)

    def login(self, force=True):
        if not force:
            return

        self.code = self.get_api_request_json('https://api.trakt.tv/oauth/device/code', postdata={'client_id': self.client_id})
        if not self.code.get('user_code') or not self.code.get('device_code'):
            return  # TODO: DIALOG: Authentication Error

        self.progress = 0
        self.interval = self.code.get('interval', 5)
        self.expires_in = self.code.get('expires_in', 0)
        self.auth_dialog = DialogProgress()
        self.auth_dialog.create(get_localized(32097), f'{get_localized(32096)}\n{get_localized(32095)}: [B]{self.code.get("user_code")}[/B]')
        self.poller()

    def refresh_token(self):
        # Check we haven't attempted too many refresh attempts
        from tmdbhelper.lib.addon.tmdate import set_timestamp
        refresh_attempts = try_int(get_property('TraktRefreshAttempts')) + 1
        if refresh_attempts > 5:
            kodi_log('Trakt Unauthorised!\nExceeded refresh_token attempt limit\nSuppressing retries for 10 minutes', 1)
            get_property('TraktRefreshTimeStamp', set_timestamp(600))
            get_property('TraktRefreshAttempts', 0)  # Reset refresh attempts
            return
        get_property('TraktRefreshAttempts', refresh_attempts)

        kodi_log('Attempting to refresh Trakt token', 2)
        if not self.authorization or not self.authorization.get('refresh_token'):
            kodi_log('Trakt refresh token not found!', 1)
            return
        postdata = {
            'refresh_token': self.authorization.get('refresh_token'),
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
            'grant_type': 'refresh_token'}
        self.authorization = self.get_api_request_json('https://api.trakt.tv/oauth/token', postdata=postdata)
        if not self.authorization or not self.authorization.get('access_token'):
            kodi_log('Failed to refresh Trakt token!', 2)
            return
        self.on_authenticated(auth_dialog=False)
        kodi_log('Trakt token refreshed', 1)
        return self.authorization

    def poller(self):
        if not self.on_poll():
            self.on_aborted()
            return
        if self.expires_in <= self.progress:
            self.on_expired()
            return
        self.authorization = self.get_api_request_json('https://api.trakt.tv/oauth/device/token', postdata={'code': self.code.get('device_code'), 'client_id': self.client_id, 'client_secret': self.client_secret})
        if self.authorization:
            self.on_authenticated()
            return
        from xbmc import Monitor
        Monitor().waitForAbort(self.interval)
        if Monitor().abortRequested():
            return
        self.poller()

    def on_aborted(self):
        """Triggered when device authentication was aborted"""
        kodi_log(u'Trakt authentication aborted!', 1)
        self.auth_dialog.close()

    def on_expired(self):
        """Triggered when the device authentication code has expired"""
        kodi_log(u'Trakt authentication expired!', 1)
        self.auth_dialog.close()

    def on_authenticated(self, auth_dialog=True):
        """Triggered when device authentication has been completed"""
        kodi_log(u'Trakt authenticated successfully!', 1)
        from tmdbhelper.lib.files.futils import json_dumps as data_dumps
        self.user_token.value = data_dumps(self.authorization)
        self.headers['Authorization'] = f'Bearer {self.authorization.get("access_token")}'
        if auth_dialog:
            self.auth_dialog.close()

    def on_poll(self):
        """Triggered before each poll"""
        if self.auth_dialog.iscanceled():
            self.auth_dialog.close()
            return False
        else:
            self.progress += self.interval
            progress = (self.progress * 100) / self.expires_in
            self.auth_dialog.update(int(progress))
            return True

    def delete_response(self, *args, **kwargs):
        return self.get_simple_api_request(
            self.get_request_url(*args, **kwargs),
            headers=self.headers,
            method='delete')

    def post_response(self, *args, postdata=None, response_method='post', **kwargs):
        from tmdbhelper.lib.files.futils import json_dumps as data_dumps
        return self.get_simple_api_request(
            self.get_request_url(*args, **kwargs),
            headers=self.headers,
            postdata=data_dumps(postdata) if postdata else None,
            method=response_method)

    def get_response(self, *args, **kwargs):
        return self.get_api_request(self.get_request_url(*args, **kwargs), headers=self.headers)

    def get_response_json(self, *args, **kwargs):
        try:
            return self.get_api_request(self.get_request_url(*args, **kwargs), headers=self.headers).json()
        except ValueError:
            return {}
        except AttributeError:
            return {}
