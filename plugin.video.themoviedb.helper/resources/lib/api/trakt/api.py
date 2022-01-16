import random
from xbmc import Monitor
from xbmcgui import Dialog, DialogProgress
from resources.lib.files.futils import json_loads as data_loads
from resources.lib.files.futils import json_dumps as data_dumps
from resources.lib.addon.window import get_property
from resources.lib.addon.plugin import get_localized, get_setting, set_setting
from resources.lib.addon.parser import try_int
from resources.lib.addon.tmdate import set_timestamp, get_timestamp
from resources.lib.files.bcache import use_simple_cache
from resources.lib.items.pages import PaginatedItems, get_next_page
from resources.lib.api.request import RequestAPI
from resources.lib.api.trakt.items import TraktItems
from resources.lib.api.trakt.decorators import is_authorized, use_activity_cache, _is_property_lock, use_thread_lock
from resources.lib.api.trakt.progress import _TraktProgress
from resources.lib.addon.logger import kodi_log, TimerFunc
from resources.lib.addon.consts import CACHE_SHORT, CACHE_LONG


API_URL = 'https://api.trakt.tv/'
CLIENT_ID = 'e6fde6173adf3c6af8fd1b0694b9b84d7c519cefc24482310e1de06c6abe5467'
CLIENT_SECRET = '15119384341d9a61c751d8d515acbc0dd801001d4ebe85d3eef9885df80ee4d9'


def get_sort_methods(default_only=False):
    items = [
        {
            'name': f'{get_localized(32287)}: {get_localized(32286)}',
            'params': {'sort_by': 'rank', 'sort_how': 'asc'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(32106)}',
            'params': {'sort_by': 'added', 'sort_how': 'desc'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(369)}',
            'params': {'sort_by': 'title', 'sort_how': 'asc'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(16102)}',
            'params': {'sort_by': 'watched', 'sort_how': 'desc', 'extended': 'sync'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(563)}',
            'params': {'sort_by': 'percentage', 'sort_how': 'desc', 'extended': 'full'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(345)}',
            'params': {'sort_by': 'year', 'sort_how': 'desc'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(32377)}',
            'params': {'sort_by': 'plays', 'sort_how': 'desc', 'extended': 'sync'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(32242)}',
            'params': {'sort_by': 'released', 'sort_how': 'desc', 'extended': 'full'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(2050)}',
            'params': {'sort_by': 'runtime', 'sort_how': 'desc', 'extended': 'full'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(205)}',
            'params': {'sort_by': 'votes', 'sort_how': 'desc', 'extended': 'full'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(32175)}',
            'params': {'sort_by': 'popularity', 'sort_how': 'desc', 'extended': 'full'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(575)}',
            'params': {'sort_by': 'watched', 'sort_how': 'desc', 'extended': 'inprogress'}},
        {
            'name': f'{get_localized(32287)}: {get_localized(590)}',
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

    def _filter_inprogress(self, items):
        """ Filter list so that it only returns inprogress shows """
        inprogress = self._get_inprogress_shows() or []
        inprogress = [i['show']['ids']['slug'] for i in inprogress if i.get('show', {}).get('ids', {}).get('slug')]
        if not inprogress:
            return
        items = [i for i in items if i.get('show', {}).get('ids', {}).get('slug') in inprogress]
        return items

    @use_simple_cache(cache_days=CACHE_SHORT)
    def get_sorted_list(self, path, sort_by=None, sort_how=None, extended=None, trakt_type=None, permitted_types=None, cache_refresh=False):
        response = self.get_response(path, extended=extended, limit=4095)
        if not response:
            return

        if extended == 'sync':
            items = self._merge_sync_sort(response.json())
        elif extended == 'inprogress':
            items = self._filter_inprogress(self._merge_sync_sort(response.json()))
        else:
            items = response.json()

        return TraktItems(items, headers=response.headers).build_items(
            sort_by=sort_by or response.headers.get('x-sort-by'),
            sort_how=sort_how or response.headers.get('x-sort-how'),
            permitted_types=permitted_types)

    @use_simple_cache(cache_days=CACHE_SHORT)
    def get_simple_list(self, *args, trakt_type=None, **kwargs):
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
                path.format(trakt_type=trakt_type), extended=extended, page=1, limit=limit * 2, trakt_type=trakt_type) or {}
            items += response.get('items') or []
        if items:
            return random.sample(items, limit)

    @is_authorized
    def get_basic_list(self, path, trakt_type, page=1, limit=20, params=None, sort_by=None, sort_how=None, extended=None, authorize=False, randomise=False, always_refresh=True):
        # TODO: Add argument to check whether to refresh on first page (e.g. for user lists)
        # Also: Think about whether need to do it for standard respons
        cache_refresh = True if always_refresh and try_int(page, fallback=1) == 1 else False
        if randomise:
            response = self.get_simple_list(
                path, extended=extended, page=1, limit=limit * 2, trakt_type=trakt_type)
        elif sort_by is not None:  # Sorted list manually paginated because need to sort first
            response = self.get_sorted_list(path, sort_by, sort_how, extended, cache_refresh=cache_refresh)
            response = PaginatedItems(items=response['items'], page=page, limit=limit).get_dict()
        else:  # Unsorted lists can be paginated by the API
            response = self.get_simple_list(path, extended=extended, page=page, limit=limit, trakt_type=trakt_type)
        if response:
            if randomise and len(response['items']) > limit:
                items = random.sample(response['items'], limit)
                return items
            return response['items'] + get_next_page(response['headers'])

    @is_authorized
    def get_stacked_list(self, path, trakt_type, page=1, limit=20, params=None, sort_by=None, sort_how=None, extended=None, authorize=False, always_refresh=True, **kwargs):
        """ Get Basic list but stack repeat TV Shows """
        cache_refresh = True if always_refresh and try_int(page, fallback=1) == 1 else False
        response = self.get_simple_list(path, extended=extended, limit=4095, trakt_type=trakt_type, cache_refresh=cache_refresh)
        response['items'] = self._stack_calendar_tvshows(response['items'])
        response = PaginatedItems(items=response['items'], page=page, limit=limit).get_dict()
        if response:
            return response['items'] + get_next_page(response['headers'])

    def get_custom_list(self, list_slug, user_slug=None, page=1, limit=20, params=None, authorize=False, sort_by=None, sort_how=None, extended=None, owner=False, always_refresh=True):
        if authorize and not self.authorize():
            return
        if user_slug == 'official':
            path = f'lists/{list_slug}/items'
        else:
            path = f'users/{user_slug or "me"}/lists/{list_slug}/items'
        # Refresh cache on first page for user list because it might've changed
        cache_refresh = True if always_refresh and try_int(page, fallback=1) == 1 else False
        sorted_items = self.get_sorted_list(
            path, sort_by, sort_how, extended,
            permitted_types=['movie', 'show', 'person', 'episode'],
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
    def _get_sync_list(self, sync_type, trakt_type, sort_by=None, sort_how=None, decorator_cache_refresh=False):
        get_property('TraktSyncLastActivities.Expires', clear_property=True)  # Wipe last activities cache to update now
        func = TraktItems(items=self.get_sync(sync_type, trakt_type), trakt_type=trakt_type).build_items
        return func(sort_by, sort_how)

    def get_sync_list(self, sync_type, trakt_type, page=1, limit=None, params=None, sort_by=None, sort_how=None, next_page=True, always_refresh=True):
        limit = limit or self.item_limit
        cache_refresh = True if always_refresh and try_int(page, fallback=1) == 1 else False
        response = self._get_sync_list(sync_type, trakt_type, sort_by=sort_by, sort_how=sort_how, decorator_cache_refresh=cache_refresh)
        if not response:
            return
        response = PaginatedItems(items=response['items'], page=page, limit=limit)
        return response.items if not next_page else response.items + response.next_page

    @is_authorized
    def get_list_of_lists(self, path, page=1, limit=250, authorize=False, next_page=True, sort_likes=False):
        response = self.get_response(path, page=page, limit=limit)
        if not response:
            return
        items = []
        sorted_list = sorted(response.json(), key=lambda i: i.get('likes', 0) or i.get('list', {}).get('likes', 0), reverse=True) if sort_likes else response.json()
        for i in sorted_list:
            if i.get('list') and i['list'].get('name'):
                i = i['list']
            elif not i.get('name'):
                continue

            i_name = i.get('name')
            i_usr = i.get('user') or {}
            i_ids = i.get('ids') or {}
            i_usr_ids = i_usr.get('ids') or {}
            i_usr_slug = 'official' if i.get('type') == 'official' else i_usr_ids.get('slug')
            i_lst_slug = i_ids.get('slug')
            i_lst_trakt = i_ids.get('trakt')

            item = {}
            item['label'] = f"{i.get('name')}"
            item['infolabels'] = {'plot': i.get('description'), 'studio': [i_usr.get('name') or i_usr_ids.get('slug')]}
            item['infoproperties'] = {k: v for k, v in i.items() if v and type(v) not in [list, dict]}
            item['art'] = {}
            item['params'] = {
                'info': 'trakt_userlist',
                'list_name': i_name,
                'list_slug': i_lst_slug,
                'user_slug': i_usr_slug,
                'plugin_category': i_name}
            item['unique_ids'] = {
                'trakt': i_lst_trakt,
                'slug': i_lst_slug,
                'user': i_usr_slug}
            item['infoproperties']['tmdbhelper.context.sorting'] = data_dumps(item['params'])

            # Add library context menu
            item['context_menu'] = [(
                get_localized(20444), u'Runscript(plugin.video.themoviedb.helper,{})'.format(
                    u'user_list={list_slug},user_slug={user_slug}'.format(**item['params'])))]

            # Unlike list context menu
            if path.startswith('users/likes'):
                item['context_menu'] += [(
                    get_localized(32319), u'Runscript(plugin.video.themoviedb.helper,{},delete)'.format(
                        u'like_list={list_slug},user_slug={user_slug}'.format(**item['params'])))]

            # Like list context menu
            elif path.startswith('lists/'):
                item['context_menu'] += [(
                    get_localized(32315), u'Runscript(plugin.video.themoviedb.helper,{})'.format(
                        u'like_list={list_slug},user_slug={user_slug}'.format(**item['params'])))]

            # Owner of list so set param to allow deleting later
            else:
                item['params']['owner'] = 'true'
                item['context_menu'] += [(
                    get_localized(118), u'Runscript(plugin.video.themoviedb.helper,{})'.format(
                        u'rename_list={list_slug}'.format(**item['params'])))]
                item['context_menu'] += [(
                    get_localized(117), u'Runscript(plugin.video.themoviedb.helper,{})'.format(
                        u'delete_list={list_slug}'.format(**item['params'])))]

            items.append(item)
        if not next_page:
            return items
        return items + get_next_page(response.headers)

    @is_authorized
    def like_userlist(self, user_slug=None, list_slug=None, confirmation=False, delete=False):
        func = self.delete_response if delete else self.post_response
        response = func('users', user_slug, 'lists', list_slug, 'like')
        if confirmation:
            affix = get_localized(32320) if delete else get_localized(32321)
            body = [
                get_localized(32316).format(affix),
                get_localized(32168).format(list_slug, user_slug)] if response.status_code == 204 else [
                get_localized(32317).format(affix),
                get_localized(32168).format(list_slug, user_slug),
                get_localized(32318).format(response.status_code)]
            Dialog().ok(get_localized(32315), '\n'.join(body))
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
            postdata={f'{trakt_type}s': [item]})

    def sync_item(self, method, trakt_type, unique_id, id_type, season=None, episode=None):
        """
        methods = history watchlist collection recommendations
        trakt_type = movie, show, season, episode
        """
        item = self.get_sync_item(trakt_type, unique_id, id_type, season, episode)
        if not item:
            return
        return self.post_response('sync', method, postdata={f'{trakt_type}s': [item]})

    def _get_activity_timestamp(self, activities, activity_type=None, activity_key=None):
        if not activities:
            return
        if not activity_type:
            return activities.get('all', '')
        if not activity_key:
            return activities.get(activity_type, {})
        return activities.get(activity_type, {}).get(activity_key)

    @is_authorized
    def _get_last_activity(self, activity_type=None, activity_key=None, cache_refresh=False):
        def _cache_expired():
            """ Check if the cached last_activities has expired """
            last_exp = get_property('TraktSyncLastActivities.Expires', is_type=int)
            if not last_exp or last_exp < set_timestamp(0, True):  # Expired
                return True
            return False

        def _cache_activity():
            """ Get last_activities from Trakt and add to cache while locking other lookup threads """
            get_property('TraktSyncLastActivities.Locked', 1)  # Lock other threads
            response = self.get_response_json('sync/last_activities')  # Retrieve data from Trakt
            if response:
                get_property('TraktSyncLastActivities', set_property=data_dumps(response))  # Dump data to property
                get_property('TraktSyncLastActivities.Expires', set_property=set_timestamp(90, True))  # Set activity expiry
            get_property('TraktSyncLastActivities.Locked', clear_property=True)  # Clear thread lock
            return response

        def _cache_router():
            """ Routes between getting cached object or new lookup """
            if not _cache_expired():
                return data_loads(get_property('TraktSyncLastActivities'))
            if _is_property_lock('TraktSyncLastActivities.Locked'):  # Other thread getting data so wait for it
                return data_loads(get_property('TraktSyncLastActivities'))
            return _cache_activity()

        if not self.last_activities:
            self.last_activities = _cache_router()

        return self._get_activity_timestamp(self.last_activities, activity_type=activity_type, activity_key=activity_key)

    @use_activity_cache(cache_days=CACHE_SHORT)
    def _get_sync_response(self, path, extended=None, allow_fallback=False):
        """ Quick sub-cache routine to avoid recalling full sync list if we also want to quicklist it """
        sync_name = f'sync_response.{path}.{extended}'
        self.sync[sync_name] = self.sync.get(sync_name) or self.get_response_json(path, extended=extended)
        return self.sync[sync_name]

    @is_authorized
    def _get_sync(self, path, trakt_type, id_type=None, extended=None, allow_fallback=False):
        """ Get sync list """
        response = self._get_sync_response(path, extended=extended, allow_fallback=allow_fallback)
        if not id_type:
            return response
        if response and trakt_type:
            return {
                i[trakt_type]['ids'][id_type]: i for i in response
                if i.get(trakt_type, {}).get('ids', {}).get(id_type)}

    def is_sync(self, trakt_type, unique_id, season=None, episode=None, id_type=None, sync_type=None):
        """ Returns True if item in sync list else False """

        def _is_nested():
            try:
                sync_item_seasons = sync_list[unique_id]['seasons']
            except (KeyError, AttributeError):
                return
            if not sync_item_seasons:
                return
            se_n, ep_n = try_int(season), try_int(episode)
            for i in sync_item_seasons:
                if se_n != i.get('number'):
                    continue
                if ep_n is None:
                    return True
                try:
                    sync_item_episodes = i['episodes']
                except (KeyError, AttributeError):
                    return
                if not sync_item_episodes:
                    return
                for j in sync_item_episodes:
                    if ep_n == j.get('number'):
                        return True
        sync_list = self.get_sync(sync_type, trakt_type, id_type)
        if unique_id not in sync_list:
            return
        if season is None:
            return True
        return _is_nested()

    @use_activity_cache('movies', 'watched_at', CACHE_LONG)
    def get_sync_watched_movies(self, trakt_type, id_type=None):
        return self._get_sync('sync/watched/movies', 'movie', id_type=id_type, allow_fallback=True)

    # Watched shows sync uses short cache as needed for progress checks and new episodes might air tomorrow
    @use_activity_cache('episodes', 'watched_at', CACHE_SHORT)
    def get_sync_watched_shows(self, trakt_type, id_type=None):
        return self._get_sync('sync/watched/shows', 'show', id_type=id_type, extended='full', allow_fallback=True)

    @use_activity_cache('movies', 'collected_at', CACHE_LONG)
    def get_sync_collection_movies(self, trakt_type, id_type=None):
        return self._get_sync('sync/collection/movies', 'movie', id_type=id_type)

    @use_activity_cache('episodes', 'collected_at', CACHE_LONG)
    def get_sync_collection_shows(self, trakt_type, id_type=None):
        return self._get_sync('sync/collection/shows', trakt_type, id_type=id_type)

    @use_activity_cache('movies', 'paused_at', CACHE_LONG)
    def get_sync_playback_movies(self, trakt_type, id_type=None):
        return self._get_sync('sync/playback/movies', 'movie', id_type=id_type)

    @use_activity_cache('episodes', 'paused_at', CACHE_LONG)
    def get_sync_playback_shows(self, trakt_type, id_type=None):
        return self._get_sync('sync/playback/episodes', trakt_type, id_type=id_type)

    @use_activity_cache('movies', 'watchlisted_at', CACHE_LONG)
    def get_sync_watchlist_movies(self, trakt_type, id_type=None):
        return self._get_sync('sync/watchlist/movies', 'movie', id_type=id_type)

    @use_activity_cache('shows', 'watchlisted_at', CACHE_LONG)
    def get_sync_watchlist_shows(self, trakt_type, id_type=None):
        return self._get_sync('sync/watchlist/shows', 'show', id_type=id_type)

    @use_activity_cache('movies', 'recommendations_at', CACHE_LONG)
    def get_sync_recommendations_movies(self, trakt_type, id_type=None):
        return self._get_sync('sync/recommendations/movies', 'movie', id_type=id_type)

    @use_activity_cache('shows', 'recommendations_at', CACHE_LONG)
    def get_sync_recommendations_shows(self, trakt_type, id_type=None):
        return self._get_sync('sync/recommendations/shows', 'show', id_type=id_type)

    @use_thread_lock('TraktAPI.get_sync.Locked', timeout=10, polling=0.05, combine_name=True)
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
        sync_name = f'{sync_type}.{trakt_type}.{id_type}'
        self.sync[sync_name] = self.sync.get(sync_name) or func(trakt_type, id_type)
        return self.sync[sync_name] or {}


class TraktAPI(RequestAPI, _TraktSync, _TraktLists, _TraktProgress):
    def __init__(self, force=False, delay_write=False):
        super(TraktAPI, self).__init__(req_api_url=API_URL, req_api_name='TraktAPI', timeout=20, delay_write=delay_write)
        self.authorization = ''
        self.attempted_login = False
        self.dialog_noapikey_header = f'{get_localized(32007)} {self.req_api_name} {get_localized(32011)}'
        self.dialog_noapikey_text = get_localized(32012)
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.headers = {'trakt-api-version': '2', 'trakt-api-key': self.client_id, 'Content-Type': 'application/json'}
        self.last_activities = {}
        self.sync_activities = {}
        self.sync = {}
        self.item_limit = 83 if get_setting('trakt_expandedlimit') else 20  # 84 (83+NextPage) has common factors 4,6,7,8 suitable for wall views
        self.login() if force else self.authorize()

    def authorize(self, login=False):
        def _get_token():
            token = self.get_stored_token()
            if not token.get('access_token'):
                return
            self.authorization = token
            self.headers['Authorization'] = f'Bearer {self.authorization.get("access_token")}'
            return token

        # Already got authorization so return credentials
        if self.authorization:
            return self.authorization

        # Check for saved credentials from previous login
        token = _get_token()

        # No saved credentials and user trying to use a feature that requires authorization so ask them to login
        if not token and login:
            if not self.attempted_login and Dialog().yesno(
                    self.dialog_noapikey_header,
                    self.dialog_noapikey_text,
                    nolabel=get_localized(222),
                    yeslabel=get_localized(186)):
                self.login()
            self.attempted_login = True

        # First time authorization in this session so let's confirm
        if self.authorization and get_property('TraktIsAuth') != 'True':
            if not get_timestamp(get_property('TraktRefreshTimeStamp', is_type=float) or 0):
                if _is_property_lock('TraktCheckingAuth'):  # Wait if another thread is checking authorization
                    _get_token()  # Get the token set in the other thread
                    return self.authorization  # Another thread checked token so return

                get_property('TraktCheckingAuth', 1)  # Set Thread lock property
                kodi_log('Trakt authorization started', 1)

                # Check if we can get a response from user account
                with TimerFunc('Trakt authorization took', inline=True):
                    response = self.get_simple_api_request('https://api.trakt.tv/sync/last_activities', headers=self.headers)
                    if not response or response.status_code == 401:  # 401 is unauthorized error code so let's try refreshing the token
                        kodi_log('Trakt unauthorized!', 1)
                        self.authorization = self.refresh_token()
                    if self.authorization:  # Authorization confirmed so let's set a window property for future reference in this session
                        kodi_log('Trakt user account authorized', 1)
                        get_property('TraktIsAuth', 'True')
                    get_property('TraktCheckingAuth', clear_property=True)
        return self.authorization

    def get_stored_token(self):
        try:
            token = data_loads(get_setting('trakt_token', 'str')) or {}
        except Exception as exc:
            token = {}
            kodi_log(exc, 1)
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
                set_setting('trakt_token', '', 'str')
            else:
                msg = get_localized(32215)
        else:
            msg = get_localized(32214)

        Dialog().ok(get_localized(32212), msg)

    def login(self):
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
        set_setting('trakt_token', data_dumps(self.authorization), 'str')
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

    def _get_id(self, unique_id, id_type, trakt_type=None, output_type=None):
        response = self.get_request_lc('search', id_type, unique_id, type=trakt_type)
        for i in response:
            if i.get('type') != trakt_type:
                continue
            if f'{i.get(trakt_type, {}).get("ids", {}).get(id_type)}' != f'{unique_id}':
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
            cache_name=f'trakt_get_id.{id_type}.{unique_id}.{trakt_type}.{output_type}',
            cache_days=CACHE_LONG)

    def get_details(self, trakt_type, id_num, season=None, episode=None, extended='full'):
        if not season or not episode:
            return self.get_request_lc(trakt_type + 's', id_num, extended=extended)
        return self.get_request_lc(trakt_type + 's', id_num, 'seasons', season, 'episodes', episode, extended=extended)

    @use_simple_cache(cache_days=CACHE_SHORT)
    def get_imdb_top250(self, id_type=None, trakt_type='movie'):
        paths = {
            'movie': 'users/justin/lists/imdb-top-rated-movies/items',
            'show': 'users/justin/lists/imdb-top-rated-tv-shows/items'}
        try:
            response = self.get_response(paths[trakt_type], limit=4095)
            sorted_items = TraktItems(response.json() if response else []).sort_items('rank', 'asc') or []
            return [i[trakt_type]['ids'][id_type] for i in sorted_items]
        except KeyError:
            return []

    @use_simple_cache(cache_days=CACHE_SHORT)
    def get_ratings(self, trakt_type, imdb_id=None, trakt_id=None, slug_id=None, season=None, episode=None):
        slug = slug_id or trakt_id or imdb_id
        if not slug:
            return
        if episode and season:
            url = f'shows/{slug}/seasons/{season}/episodes/{episode}/ratings'
        elif season:
            url = f'shows/{slug}/seasons/{season}/ratings'
        else:
            url = f'{trakt_type}s/{slug}/ratings'
        response = self.get_response_json(url)
        if not response:
            return
        return {
            'trakt_rating': f'{response.get("rating") or 0.0:0.1f}',
            'trakt_votes': f'{response.get("votes") or 0.0:0,.0f}'}
