import xbmc
import xbmcgui
import random
import resources.lib.container.pages as pages
from resources.lib.addon.window import get_property
from json import loads, dumps
from resources.lib.api.request import RequestAPI
from resources.lib.addon.plugin import ADDON, kodi_log
from resources.lib.container.pages import PaginatedItems
from resources.lib.trakt.items import TraktItems
from resources.lib.trakt.decorators import is_authorized, use_activity_cache
from resources.lib.trakt.progress import _TraktProgress
from resources.lib.addon.parser import try_int
from resources.lib.addon.cache import CACHE_SHORT, CACHE_LONG, use_simple_cache
from resources.lib.addon.timedate import set_timestamp, get_timestamp


API_URL = 'https://api.trakt.tv/'
CLIENT_ID = 'e6fde6173adf3c6af8fd1b0694b9b84d7c519cefc24482310e1de06c6abe5467'
CLIENT_SECRET = '15119384341d9a61c751d8d515acbc0dd801001d4ebe85d3eef9885df80ee4d9'


def get_sort_methods(default_only=False):
    items = [
        {
            'name': u'{}: {}'.format(ADDON.getLocalizedString(32287), ADDON.getLocalizedString(32286)),
            'params': {'sort_by': 'rank', 'sort_how': 'asc'}},
        {
            'name': u'{}: {}'.format(ADDON.getLocalizedString(32287), ADDON.getLocalizedString(32106)),
            'params': {'sort_by': 'added', 'sort_how': 'desc'}},
        {
            'name': u'{}: {}'.format(ADDON.getLocalizedString(32287), xbmc.getLocalizedString(369)),
            'params': {'sort_by': 'title', 'sort_how': 'asc'}},
        {
            'name': u'{}: {}'.format(ADDON.getLocalizedString(32287), xbmc.getLocalizedString(16102)),
            'params': {'sort_by': 'watched', 'sort_how': 'desc', 'extended': 'sync'}},
        {
            'name': u'{}: {}'.format(ADDON.getLocalizedString(32287), xbmc.getLocalizedString(563)),
            'params': {'sort_by': 'percentage', 'sort_how': 'desc', 'extended': 'full'}},
        {
            'name': u'{}: {}'.format(ADDON.getLocalizedString(32287), xbmc.getLocalizedString(345)),
            'params': {'sort_by': 'year', 'sort_how': 'desc'}},
        {
            'name': u'{}: {}'.format(ADDON.getLocalizedString(32287), ADDON.getLocalizedString(32377)),
            'params': {'sort_by': 'plays', 'sort_how': 'desc', 'extended': 'sync'}},
        {
            'name': u'{}: {}'.format(ADDON.getLocalizedString(32287), ADDON.getLocalizedString(32242)),
            'params': {'sort_by': 'released', 'sort_how': 'desc', 'extended': 'full'}},
        {
            'name': u'{}: {}'.format(ADDON.getLocalizedString(32287), xbmc.getLocalizedString(2050)),
            'params': {'sort_by': 'runtime', 'sort_how': 'desc', 'extended': 'full'}},
        {
            'name': u'{}: {}'.format(ADDON.getLocalizedString(32287), xbmc.getLocalizedString(205)),
            'params': {'sort_by': 'votes', 'sort_how': 'desc', 'extended': 'full'}},
        {
            'name': u'{}: {}'.format(ADDON.getLocalizedString(32287), ADDON.getLocalizedString(32175)),
            'params': {'sort_by': 'popularity', 'sort_how': 'desc', 'extended': 'full'}},
        {
            'name': u'{}: {}'.format(ADDON.getLocalizedString(32287), xbmc.getLocalizedString(590)),
            'params': {'sort_by': 'random'}}]
    if default_only:
        return [i for i in items if i['params']['sort_by'] in ['rank', 'added', 'title', 'year', 'random']]
    return items

class _TraktLists():
    def _merge_sync_sort(self, items):
        """ Get sync dict sorted by slugs then merge slug into list """
        sync = {}
        sync.update(self.get_sync('watched', 'show', 'slug'))
        sync.update(self.get_sync('watched', 'movie', 'slug'))
        return [dict(i, **sync.get(i.get(i.get('type'), {}).get('ids', {}).get('slug'), {})) for i in items]

    @use_simple_cache(cache_days=CACHE_SHORT)
    def get_sorted_list(self, path, sort_by=None, sort_how=None, extended=None, trakt_type=None, permitted_types=None, cache_refresh=False):
        response = self.get_response(path, extended=extended, limit=4095)
        if not response:
            return
        items = self._merge_sync_sort(response.json()) if extended == 'sync' else response.json()
        return TraktItems(items, headers=response.headers).build_items(
            sort_by=sort_by or response.headers.get('X-Sort-By'),
            sort_how=sort_how or response.headers.get('X-Sort-How'),
            permitted_types=permitted_types)

    @use_simple_cache(cache_days=CACHE_SHORT)
    def get_simple_list(self, *args, **kwargs):
        trakt_type = kwargs.pop('trakt_type', None)
        response = self.get_response(*args, **kwargs)
        if not response:
            return
        return TraktItems(response.json(), headers=response.headers, trakt_type=trakt_type).configure_items()

    @is_authorized
    def get_mixed_list(self, path, trakt_types=[], limit=20, extended=None, authorize=False):
        """ Returns a randomised simple list which combines movies and shows
        path uses {trakt_type} as format substitution for trakt_type in trakt_types
        """
        items = []
        for trakt_type in trakt_types:
            response = self.get_simple_list(
                path.format(trakt_type=trakt_type), extended=extended, page=1, limit=50, trakt_type=trakt_type) or {}
            items += response.get('items') or []
        if items:
            return random.sample(items, 20)

    @is_authorized
    def get_basic_list(self, path, trakt_type, page=1, limit=20, params=None, sort_by=None, sort_how=None, extended=None, authorize=False, randomise=False):
        # TODO: Add argument to check whether to refresh on first page (e.g. for user lists)
        # Also: Think about whether need to do it for standard respons
        cache_refresh = True if try_int(page, fallback=1) == 1 else False
        if randomise:
            response = self.get_simple_list(
                path, extended=extended, page=1, limit=50, trakt_type=trakt_type)
        elif sort_by is not None:  # Sorted list manually paginated because need to sort first
            response = self.get_sorted_list(path, sort_by, sort_how, extended, cache_refresh=cache_refresh)
            response = PaginatedItems(items=response['items'], page=page, limit=limit).get_dict()
        else:  # Unsorted lists can be paginated by the API
            response = self.get_simple_list(
                path, extended=extended, page=page, limit=limit, trakt_type=trakt_type)
        if response:
            if randomise and len(response['items']) > limit:
                items = random.sample(response['items'], limit)
                return items
            return response['items'] + pages.get_next_page(response['headers'])

    def get_custom_list(self, list_slug, user_slug=None, page=1, limit=20, params=None, authorize=False, sort_by=None, sort_how=None, extended=None, owner=False):
        if authorize and not self.authorize():
            return
        path = u'users/{}/lists/{}/items'.format(user_slug or 'me', list_slug)
        # Refresh cache on first page for user list because it might've changed
        cache_refresh = True if try_int(page, fallback=1) == 1 else False
        sorted_items = self.get_sorted_list(
            path, sort_by, sort_how, extended,
            permitted_types=['movie', 'show', 'person'],
            cache_refresh=cache_refresh) or {}
        paginated_items = PaginatedItems(
            items=sorted_items.get('items', []), page=page, limit=limit)
        return {
            'items': paginated_items.items,
            'movies': sorted_items.get('movies', []),
            'shows': sorted_items.get('shows', []),
            'persons': sorted_items.get('persons', []),
            'next_page': paginated_items.next_page}

    @use_activity_cache(cache_days=CACHE_SHORT)
    def _get_sync_list(self, sync_type, trakt_type, sort_by=None, sort_how=None):
        return TraktItems(
            items=self.get_sync(sync_type, trakt_type),
            trakt_type=trakt_type).build_items(sort_by, sort_how)

    def get_sync_list(self, sync_type, trakt_type, page=1, limit=20, params=None, sort_by=None, sort_how=None, next_page=True):
        response = self._get_sync_list(sync_type, trakt_type, sort_by=sort_by, sort_how=sort_how)
        if not response:
            return
        response = PaginatedItems(items=response['items'], page=page, limit=limit)
        return response.items if not next_page else response.items + response.next_page

    @is_authorized
    def get_list_of_lists(self, path, page=1, limit=250, authorize=False, next_page=True):
        response = self.get_response(path, page=page, limit=limit)
        like_list = True if path.startswith('lists/') else False
        delete_like = True if path.startswith('users/likes') else False
        if not response:
            return
        items = []
        for i in response.json():
            if i.get('list', {}).get('name'):
                i = i.get('list', {})
            elif not i.get('name'):
                continue

            item = {}
            item['label'] = i.get('name')
            item['infolabels'] = {'plot': i.get('description')}
            item['infoproperties'] = {k: v for k, v in i.items() if v and type(v) not in [list, dict]}
            item['art'] = {}
            item['params'] = {
                'info': 'trakt_userlist',
                'list_name': i.get('name'),
                'list_slug': i.get('ids', {}).get('slug'),
                'user_slug': i.get('user', {}).get('ids', {}).get('slug')}
            item['unique_ids'] = {
                'trakt': i.get('ids', {}).get('trakt'),
                'slug': i.get('ids', {}).get('slug'),
                'user': i.get('user', {}).get('ids', {}).get('slug')}
            item['infoproperties']['tmdbhelper.context.sorting'] = dumps(item['params'])

            # Add library context menu
            item['context_menu'] = [(
                xbmc.getLocalizedString(20444), u'Runscript(plugin.video.themoviedb.helper,{})'.format(
                    u'user_list={list_slug},user_slug={user_slug}'.format(**item['params'])))]

            # Unlike list context menu
            if path.startswith('users/likes'):
                item['context_menu'] += [(
                    ADDON.getLocalizedString(32319), u'Runscript(plugin.video.themoviedb.helper,{},delete)'.format(
                        u'like_list={list_slug},user_slug={user_slug}'.format(**item['params'])))]

            # Like list context menu
            elif path.startswith('lists/'):
                item['context_menu'] += [(
                    ADDON.getLocalizedString(32315), u'Runscript(plugin.video.themoviedb.helper,{})'.format(
                        u'like_list={list_slug},user_slug={user_slug}'.format(**item['params'])))]

            # Owner of list so set param to allow deleting later
            else:
                item['params']['owner'] = 'true'
                item['context_menu'] += [(
                    xbmc.getLocalizedString(118), u'Runscript(plugin.video.themoviedb.helper,{})'.format(
                        u'rename_list={list_slug}'.format(**item['params'])))]
                item['context_menu'] += [(
                    xbmc.getLocalizedString(117), u'Runscript(plugin.video.themoviedb.helper,{})'.format(
                        u'delete_list={list_slug}'.format(**item['params'])))]

            items.append(item)
        if not next_page:
            return items
        return items + pages.get_next_page(response.headers)

    @is_authorized
    def like_userlist(self, user_slug=None, list_slug=None, confirmation=False, delete=False):
        func = self.delete_response if delete else self.post_response
        response = func('users', user_slug, 'lists', list_slug, 'like')
        if confirmation:
            affix = ADDON.getLocalizedString(32320) if delete else ADDON.getLocalizedString(32321)
            body = [
                ADDON.getLocalizedString(32316).format(affix),
                ADDON.getLocalizedString(32168).format(list_slug, user_slug)] if response.status_code == 204 else [
                ADDON.getLocalizedString(32317).format(affix),
                ADDON.getLocalizedString(32168).format(list_slug, user_slug),
                ADDON.getLocalizedString(32318).format(response.status_code)]
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(32315), '\n'.join(body))
        if response.status_code == 204:
            return response


class _TraktSync():
    def get_sync_item(self, trakt_type, unique_id, id_type, season=None, episode=None):
        """ Gets an item configured for syncing as postdata """
        if not unique_id or not id_type or not trakt_type:
            return
        base_trakt_type = 'show' if trakt_type in ['season', 'episode'] else trakt_type
        if id_type != 'slug':
            unique_id = self.get_id(unique_id, id_type, base_trakt_type, output_type='slug')
        if not unique_id:
            return
        return self.get_details(base_trakt_type, unique_id, season=season, episode=episode, extended=None)

    def add_list_item(self, list_slug, trakt_type, unique_id, id_type, season=None, episode=None, user_slug=None, remove=False):
        item = self.get_sync_item(trakt_type, unique_id, id_type, season, episode)
        if not item:
            return
        user_slug = user_slug or 'me'
        return self.post_response(
            'users', user_slug, 'lists', list_slug, 'items/remove' if remove else 'items',
            postdata={u'{}s'.format(trakt_type): [item]})

    def sync_item(self, method, trakt_type, unique_id, id_type, season=None, episode=None):
        """
        methods = history watchlist collection recommendations
        trakt_type = movie, show, season, episode
        """
        item = self.get_sync_item(trakt_type, unique_id, id_type, season, episode)
        if not item:
            return
        return self.post_response('sync', method, postdata={u'{}s'.format(trakt_type): [item]})

    def _get_activity_timestamp(self, activities, activity_type=None, activity_key=None):
        if not activities:
            return
        if not activity_type:
            return activities.get('all', '')
        if not activity_key:
            return activities.get(activity_type, {})
        return activities.get(activity_type, {}).get(activity_key)

    # @timer_report('_get_last_activity')
    @is_authorized
    def _get_last_activity(self, activity_type=None, activity_key=None):
        if not self.last_activities:
            self.last_activities = self.get_response_json('sync/last_activities')
        return self._get_activity_timestamp(self.last_activities, activity_type=activity_type, activity_key=activity_key)

    @use_activity_cache(cache_days=CACHE_SHORT, pickle_object=False, allow_fallback=True)
    def _get_sync_response(self, path, extended=None):
        """ Quick sub-cache routine to avoid recalling full sync list if we also want to quicklist it """
        sync_name = u'sync_response.{}.{}'.format(path, extended)
        self.sync[sync_name] = self.sync.get(sync_name) or self.get_response_json(path, extended=extended)
        return self.sync[sync_name]

    @is_authorized
    def _get_sync(self, path, trakt_type, id_type=None, extended=None):
        """ Get sync list """
        response = self._get_sync_response(path, extended=extended)
        if not id_type:
            return response
        if response and trakt_type:
            return {
                i[trakt_type]['ids'][id_type]: i for i in response
                if i.get(trakt_type, {}).get('ids', {}).get(id_type)}

    def is_sync(self, trakt_type, unique_id, season=None, episode=None, id_type=None, sync_type=None):
        """ Returns True if item in sync list else False """
        if id_type in ['tmdb', 'tvdb', 'trakt']:
            unique_id = try_int(unique_id)
        if season is not None:
            season = try_int(season)
            episode = try_int(episode)
        sync_list = self.get_sync(sync_type, trakt_type, id_type)
        if unique_id in sync_list:
            if season is None:
                return True
            for i in sync_list.get(unique_id, {}).get('seasons', []):
                if season == i.get('number'):
                    if episode is None:
                        return True
                    for j in i.get('episodes', []):
                        if episode == j.get('number'):
                            return True

    @use_activity_cache('movies', 'watched_at', CACHE_LONG, pickle_object=False)
    def get_sync_watched_movies(self, trakt_type, id_type=None):
        return self._get_sync('sync/watched/movies', 'movie', id_type=id_type)

    # Watched shows sync uses short cache as needed for progress checks and new episodes might air tomorrow
    @use_activity_cache('episodes', 'watched_at', CACHE_SHORT, pickle_object=False)
    def get_sync_watched_shows(self, trakt_type, id_type=None):
        return self._get_sync('sync/watched/shows', 'show', id_type=id_type, extended='full')

    @use_activity_cache('movies', 'collected_at', CACHE_LONG, pickle_object=False)
    def get_sync_collection_movies(self, trakt_type, id_type=None):
        return self._get_sync('sync/collection/movies', 'movie', id_type=id_type)

    @use_activity_cache('episodes', 'collected_at', CACHE_LONG, pickle_object=False)
    def get_sync_collection_shows(self, trakt_type, id_type=None):
        return self._get_sync('sync/collection/shows', trakt_type, id_type=id_type)

    @use_activity_cache('movies', 'watched_at', CACHE_LONG, pickle_object=False)
    def get_sync_playback_movies(self, trakt_type, id_type=None):
        return self._get_sync('sync/playback/movies', 'movie', id_type=id_type)

    @use_activity_cache('episodes', 'watched_at', CACHE_LONG, pickle_object=False)
    def get_sync_playback_shows(self, trakt_type, id_type=None):
        return self._get_sync('sync/playback/episodes', trakt_type, id_type=id_type)

    @use_activity_cache('movies', 'watchlisted_at', CACHE_LONG, pickle_object=False)
    def get_sync_watchlist_movies(self, trakt_type, id_type=None):
        return self._get_sync('sync/watchlist/movies', 'movie', id_type=id_type)

    @use_activity_cache('shows', 'watchlisted_at', CACHE_LONG, pickle_object=False)
    def get_sync_watchlist_shows(self, trakt_type, id_type=None):
        return self._get_sync('sync/watchlist/shows', 'show', id_type=id_type)

    @use_activity_cache('movies', 'recommendations_at', CACHE_LONG, pickle_object=False)
    def get_sync_recommendations_movies(self, trakt_type, id_type=None):
        return self._get_sync('sync/recommendations/movies', 'movie', id_type=id_type)

    @use_activity_cache('shows', 'recommendations_at', CACHE_LONG, pickle_object=False)
    def get_sync_recommendations_shows(self, trakt_type, id_type=None):
        return self._get_sync('sync/recommendations/shows', 'show', id_type=id_type)

    def get_sync(self, sync_type, trakt_type, id_type=None):
        if sync_type == 'watched':
            func = self.get_sync_watched_movies if trakt_type == 'movie' else self.get_sync_watched_shows
        elif sync_type == 'collection':
            func = self.get_sync_collection_movies if trakt_type == 'movie' else self.get_sync_collection_shows
        elif sync_type == 'playback':
            func = self.get_sync_playback_movies if trakt_type == 'movie' else self.get_sync_playback_shows
        elif sync_type == 'watchlist':
            func = self.get_sync_watchlist_movies if trakt_type == 'movie' else self.get_sync_watchlist_shows
        elif sync_type == 'recommendations':
            func = self.get_sync_recommendations_movies if trakt_type == 'movie' else self.get_sync_recommendations_shows
        else:
            return
        sync_name = u'{}.{}.{}'.format(sync_type, trakt_type, id_type)
        self.sync[sync_name] = self.sync.get(sync_name) or func(trakt_type, id_type)
        return self.sync[sync_name] or {}


class TraktAPI(RequestAPI, _TraktSync, _TraktLists, _TraktProgress):
    def __init__(self, force=False):
        super(TraktAPI, self).__init__(req_api_url=API_URL, req_api_name='TraktAPI', timeout=20)
        self.authorization = ''
        self.attempted_login = False
        self.dialog_noapikey_header = u'{0} {1} {2}'.format(ADDON.getLocalizedString(32007), self.req_api_name, ADDON.getLocalizedString(32011))
        self.dialog_noapikey_text = ADDON.getLocalizedString(32012)
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.headers = {'trakt-api-version': '2', 'trakt-api-key': self.client_id, 'Content-Type': 'application/json'}
        self.last_activities = {}
        self.sync_activities = {}
        self.sync = {}
        self.login() if force else self.authorize()

    def authorize(self, login=False):
        # Already got authorization so return credentials
        if self.authorization:
            return self.authorization

        # Get our saved credentials from previous login
        token = self.get_stored_token()
        if token.get('access_token'):
            self.authorization = token
            self.headers['Authorization'] = u'Bearer {0}'.format(self.authorization.get('access_token'))

        # No saved credentials and user trying to use a feature that requires authorization so ask them to login
        elif login:
            if not self.attempted_login and xbmcgui.Dialog().yesno(
                    self.dialog_noapikey_header,
                    self.dialog_noapikey_text,
                    nolabel=xbmc.getLocalizedString(222),
                    yeslabel=xbmc.getLocalizedString(186)):
                self.login()
            self.attempted_login = True

        # First time authorization in this session so let's confirm
        if self.authorization and get_property('TraktIsAuth') != 'True':
            if not get_timestamp(get_property('TraktRefreshTimeStamp', is_type=float) or 0):
                # Check if we can get a response from user account
                kodi_log('Checking Trakt authorization', 2)
                response = self.get_simple_api_request('https://api.trakt.tv/sync/last_activities', headers=self.headers)
                # 401 is unauthorized error code so let's try refreshing the token
                if not response or response.status_code == 401:
                    kodi_log('Trakt unauthorized!', 2)
                    self.authorization = self.refresh_token()
                # Authorization confirmed so let's set a window property for future reference in this session
                if self.authorization:
                    kodi_log('Trakt user account authorized', 1)
                    get_property('TraktIsAuth', 'True')

        return self.authorization

    def get_stored_token(self):
        try:
            token = loads(ADDON.getSettingString('trakt_token')) or {}
        except Exception as exc:
            token = {}
            kodi_log(exc, 1)
        return token

    def logout(self):
        token = self.get_stored_token()

        if not xbmcgui.Dialog().yesno(ADDON.getLocalizedString(32212), ADDON.getLocalizedString(32213)):
            return

        if token:
            response = self.get_api_request('https://api.trakt.tv/oauth/revoke', postdata={
                'token': token.get('access_token', ''),
                'client_id': self.client_id,
                'client_secret': self.client_secret})
            if response and response.status_code == 200:
                msg = ADDON.getLocalizedString(32216)
                ADDON.setSettingString('trakt_token', '')
            else:
                msg = ADDON.getLocalizedString(32215)
        else:
            msg = ADDON.getLocalizedString(32214)

        xbmcgui.Dialog().ok(ADDON.getLocalizedString(32212), msg)

    def login(self):
        self.code = self.get_api_request_json('https://api.trakt.tv/oauth/device/code', postdata={'client_id': self.client_id})
        if not self.code.get('user_code') or not self.code.get('device_code'):
            return  # TODO: DIALOG: Authentication Error
        self.progress = 0
        self.interval = self.code.get('interval', 5)
        self.expires_in = self.code.get('expires_in', 0)
        self.auth_dialog = xbmcgui.DialogProgress()
        self.auth_dialog.create(ADDON.getLocalizedString(32097), u'{}\n{}: [B]{}[/B]'.format(
            ADDON.getLocalizedString(32096), ADDON.getLocalizedString(32095), self.code.get('user_code')))
        self.poller()

    def refresh_token(self):
        # Check we haven't attempted too many refresh attempts
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
        xbmc.Monitor().waitForAbort(self.interval)
        if xbmc.Monitor().abortRequested():
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
        ADDON.setSettingString('trakt_token', dumps(self.authorization))
        self.headers['Authorization'] = u'Bearer {0}'.format(self.authorization.get('access_token'))
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

    def post_response(self, *args, **kwargs):
        postdata = kwargs.pop('postdata', None)
        response_method = kwargs.pop('response_method', 'post')
        return self.get_simple_api_request(
            self.get_request_url(*args, **kwargs),
            headers=self.headers,
            postdata=dumps(postdata) if postdata else None,
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

    def _get_id(self, unique_id, id_type, trakt_type=None, output_type=None):
        response = self.get_request_lc('search', id_type, unique_id, type=trakt_type)
        for i in response:
            if i.get('type') != trakt_type:
                continue
            if u'{}'.format(i.get(trakt_type, {}).get('ids', {}).get(id_type)) != u'{}'.format(unique_id):
                continue
            if not output_type:
                return i.get(trakt_type, {}).get('ids', {})
            return i.get(trakt_type, {}).get('ids', {}).get(output_type)

    def get_id(self, unique_id, id_type, trakt_type=None, output_type=None):
        """
        trakt_type: movie, show, episode, person, list
        output_type: trakt, slug, imdb, tmdb, tvdb
        """
        return self._cache.use_cache(
            self._get_id, unique_id, id_type, trakt_type=trakt_type, output_type=output_type,
            cache_name=u'trakt_get_id.{}.{}.{}.{}'.format(id_type, unique_id, trakt_type, output_type),
            cache_days=CACHE_LONG)

    def get_details(self, trakt_type, id_num, season=None, episode=None, extended='full'):
        if not season or not episode:
            return self.get_request_lc(trakt_type + 's', id_num, extended=extended)
        return self.get_request_lc(trakt_type + 's', id_num, 'seasons', season, 'episodes', episode, extended=extended)

    @use_simple_cache(cache_days=CACHE_SHORT)
    def get_imdb_top250(self, id_type=None):
        path = 'users/justin/lists/imdb-top-rated-movies/items'
        response = self.get_response(path, limit=4095)
        sorted_items = TraktItems(response.json() if response else []).sort_items('rank', 'asc') or []
        return [i['movie']['ids'][id_type] for i in sorted_items]

    @use_simple_cache(cache_days=CACHE_SHORT)
    def get_ratings(self, trakt_type, imdb_id=None, trakt_id=None, slug_id=None, season=None, episode=None):
        slug = slug_id or trakt_id or imdb_id
        if not slug:
            return
        if episode and season:
            url = u'shows/{}/seasons/{}/episodes/{}/ratings'.format(slug, season, episode)
        elif season:
            url = u'shows/{}/seasons/{}/ratings'.format(slug, season)
        else:
            url = u'{}s/{}/ratings'.format(trakt_type, slug)
        response = self.get_response_json(url)
        if not response:
            return
        return {
            'trakt_rating': u'{:0.1f}'.format(response.get('rating') or 0.0),
            'trakt_votes': u'{:0,.0f}'.format(response.get('votes') or 0.0)}
