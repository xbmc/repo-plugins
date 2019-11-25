from json import loads, dumps
import resources.lib.utils as utils
from resources.lib.requestapi import RequestAPI
import xbmc
import xbmcgui
import xbmcaddon
import datetime


class traktAPI(RequestAPI):
    def __init__(self, force=False):
        self.req_api_url = 'https://api.trakt.tv/'
        self.req_api_key = ''
        self.req_api_name = 'trakt'
        self.req_wait_time = 0
        self.cache_long = 1
        self.cache_short = 0.003
        self.access_token = ''
        self.addon_name = 'plugin.video.themoviedb.helper'
        self.client_id = 'e6fde6173adf3c6af8fd1b0694b9b84d7c519cefc24482310e1de06c6abe5467'
        self.client_secret = '15119384341d9a61c751d8d515acbc0dd801001d4ebe85d3eef9885df80ee4d9'
        self.headers = {'trakt-api-version': '2', 'trakt-api-key': self.client_id, 'Content-Type': 'application/json'}

        token = xbmcaddon.Addon().getSetting('trakt_token')
        token = loads(token) if token else None

        if token and type(token) is dict and token.get('access_token') and not force:
            self.authorization = token
            self.headers['Authorization'] = 'Bearer {0}'.format(self.authorization.get('access_token'))
        else:
            self.login()

    def login(self):
        self.code = self.get_api_request('https://api.trakt.tv/oauth/device/code', postdata={'client_id': self.client_id})
        if not self.code.get('user_code') or not self.code.get('device_code'):
            return  # TODO: DIALOG: Authentication Error
        self.progress = 0
        self.interval = self.code.get('interval', 5)
        self.expirein = self.code.get('expires_in', 0)
        self.auth_dialog = xbmcgui.DialogProgress()
        self.auth_dialog.create(
            'Trakt Authentication',
            'Go to [B]https://trakt.tv/activate[/B]',
            'Enter the code: [B]' + self.code.get('user_code') + '[/B]')
        self.poller()

    def refresh_token(self):
        postdata = {
            'refresh_token': self.authorization.get('refresh_token'),
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
            'grant_type': 'refresh_token'}
        self.authorization = self.get_api_request('https://api.trakt.tv/oauth/token', postdata=postdata)
        if not self.authorization or not self.authorization.get('access_token'):
            return
        self.on_authenticated(auth_dialog=False)

    def poller(self):
        if not self.on_poll():
            self.on_aborted()
            return
        if self.expirein <= self.progress:
            self.on_expired()
            return
        self.authorization = self.get_api_request('https://api.trakt.tv/oauth/device/token', postdata={'code': self.code.get('device_code'), 'client_id': self.client_id, 'client_secret': self.client_secret})
        if not self.authorization:
            xbmc.Monitor().waitForAbort(self.interval)
            if xbmc.Monitor().abortRequested():
                return
            self.poller()
        self.on_authenticated()

    def on_aborted(self):
        """Triggered when device authentication was aborted"""
        utils.kodi_log('Trakt Authentication Aborted!', 1)
        self.auth_dialog.close()

    def on_expired(self):
        """Triggered when the device authentication code has expired"""
        utils.kodi_log('Trakt Authentication Expired!', 1)
        self.auth_dialog.close()

    def on_authenticated(self, auth_dialog=True):
        """Triggered when device authentication has been completed"""
        utils.kodi_log('Trakt Authenticated Successfully!', 1)
        xbmcaddon.Addon().setSettingString('trakt_token', dumps(self.authorization))
        self.headers['Authorization'] = 'Bearer {0}'.format(self.authorization.get('access_token'))
        if auth_dialog:
            self.auth_dialog.close()

    def on_poll(self):
        """Triggered before each poll"""
        if self.auth_dialog.iscanceled():
            self.auth_dialog.close()
            return False
        else:
            self.progress += self.interval
            progress = (self.progress * 100) / self.expirein
            self.auth_dialog.update(int(progress))
            return True

    def get_response(self, *args, **kwargs):
        refreshcheck = kwargs.pop('refreshcheck', False)
        response = self.get_api_request(self.get_request_url(*args, **kwargs), headers=self.headers, dictify=False)
        if response.status_code == 401:
            self.refresh_token()
            if not refreshcheck:
                kwargs['refreshcheck'] = True
                self.get_response(*args, **kwargs)
        return response

    def get_itemlist(self, *args, **kwargs):
        keylist = kwargs.pop('keylist', ['dummy'])
        response = self.get_response(*args, **kwargs)
        itemlist = response.json()
        this_page = int(kwargs.get('page', 1))
        last_page = int(response.headers.get('X-Pagination-Page-Count', 0))
        next_page = ('next_page', this_page + 1, None) if this_page < last_page else False
        items = []
        for i in itemlist:
            for key in keylist:
                item = None
                myitem = i.get(key) or i
                if myitem:
                    tmdbtype = 'tv' if key == 'show' else 'movie'
                    if myitem.get('ids', {}).get('imdb'):
                        item = ('imdb', myitem.get('ids', {}).get('imdb'), tmdbtype)
                    elif myitem.get('ids', {}).get('tvdb'):
                        item = ('tvdb', myitem.get('ids', {}).get('tvdb'), tmdbtype)
                    if item:
                        items.append(item)
        if next_page:
            items.append(next_page)
        return items

    def get_listlist(self, request, key=None):
        response = self.get_response(request, limit=250).json()
        items = [i.get(key) or i for i in response if i.get(key) or i]
        return items

    def get_limitedlist(self, itemlist, itemtype, limit):
        items = []
        n = 0
        for i in itemlist:
            if limit and n >= limit:
                break
            item = (i.get(itemtype, {}).get('ids', {}).get('slug'), i.get(itemtype, {}).get('ids', {}).get('tmdb'))
            if item not in items:
                items.append(item)
                n += 1
        return items

    def get_mostwatched(self, userslug, itemtype, limit=None):
        history = self.get_response('users', userslug, 'watched', itemtype + 's').json()
        history = sorted(history, key=lambda i: i['plays'], reverse=True)
        return self.get_limitedlist(history, itemtype, limit)

    def get_recentlywatched(self, userslug, itemtype, limit=None):
        start_at = datetime.date.today() - datetime.timedelta(6 * 365 / 12)
        history = self.get_response('users', userslug, 'history', itemtype + 's', page=1, limit=200, start_at=start_at.strftime("%Y-%m-%d")).json()
        return self.get_limitedlist(history, itemtype, limit)

    def get_inprogress(self, userslug, limit=None):
        """
        Looks at user's most recently watched 200 episodes in last 6 months
        Adds each unique show to list in order then checks if show has an upnext episode
        Returns list of tmdb_ids representing shows with upnext episodes in recently watched order
        """
        recentshows = self.get_recentlywatched(userslug, 'show')
        items = []
        n = 0
        for i in recentshows:
            if limit and n >= limit:
                break
            progress = self.get_upnext(i[0], True)
            if progress and progress.get('next_episode'):
                items.append(i)
                n += 1
        return items

    def get_upnext(self, show_id, response_only=False):
        request = 'shows/{0}/progress/watched'.format(show_id)
        response = self.get_response(request).json()
        reset_at = utils.convert_timestamp(response.get('reset_at')) if response.get('reset_at') else None
        seasons = response.get('seasons', [])
        items = []
        for season in seasons:
            s_num = season.get('number')
            for episode in season.get('episodes', []):
                item = None
                e_num = episode.get('number')
                if episode.get('completed'):
                    if reset_at and utils.convert_timestamp(episode.get('last_watched_at')) < reset_at:
                        item = (s_num, e_num)
                else:
                    item = (s_num, e_num)
                if item:
                    if response_only:
                        return response
                    items.append(item)
        if not response_only:
            return items

    def get_usernameslug(self):
        item = self.get_response('users/settings').json()
        return item.get('user', {}).get('ids', {}).get('slug')

    def get_traktslug(self, item_type, id_type, id):
        item = self.get_response('search', id_type, id, '?' + item_type).json()
        return item[0].get(item_type, {}).get('ids', {}).get('slug')
