from tmdbhelper.lib.api.trakt.decorators import is_authorized, use_activity_cache
from tmdbhelper.lib.addon.consts import CACHE_SHORT, CACHE_LONG
from tmdbhelper.lib.addon.thread import use_thread_lock


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


@is_authorized
def like_userlist(self, user_slug=None, list_slug=None, confirmation=False, delete=False):
    from tmdbhelper.lib.addon.plugin import get_localized
    func = self.delete_response if delete else self.post_response
    response = func('users', user_slug, 'lists', list_slug, 'like')
    if confirmation:
        from xbmcgui import Dialog
        affix = get_localized(32320) if delete else get_localized(32321)
        body = [
            get_localized(32316).format(affix),
            get_localized(32168).format(list_slug, user_slug)
        ] if response.status_code == 204 else [
            get_localized(32317).format(affix),
            get_localized(32168).format(list_slug, user_slug),
            get_localized(32318).format(response.status_code)
        ]
        Dialog().ok(get_localized(32315), '\n'.join(body))
    if response.status_code == 204:
        return response


def sync_item(self, method, trakt_type, unique_id, id_type, season=None, episode=None):
    """
    methods = history watchlist collection favorites
    trakt_type = movie, show, season, episode
    """
    item = self.get_sync_item(trakt_type, unique_id, id_type, season, episode)
    if not item:
        return
    return self.post_response('sync', method, postdata={f'{trakt_type}s': [item]})


@use_activity_cache(cache_days=CACHE_SHORT)
def get_sync_response(self, path, extended=None, allow_fallback=False):
    """ Quick sub-cache routine to avoid recalling full sync list if we also want to quicklist it """
    sync_name = f'sync_response.{path}.{extended}'
    self.sync[sync_name] = self.sync.get(sync_name) or self.get_response_json(path, extended=extended)
    return self.sync[sync_name]


@is_authorized
def get_sync_configured(self, path, trakt_type, id_type=None, extended=None, allow_fallback=False):
    """ Get sync list """
    response = self.get_sync_response(path, extended=extended, allow_fallback=allow_fallback)

    if not id_type:
        return response

    if not response or not trakt_type:
        return

    sync_dict = {}
    for i in response:

        # Only add items that have that have an ID for id_type
        try:
            key = i[trakt_type]['ids'][id_type]
        except KeyError:
            continue
        if not key:
            continue

        # If the item type matches the trakt_type then add dictionary and move on
        i_type = i.get('type')
        if trakt_type == i_type or not i_type:
            sync_dict[key] = i
            continue

        # Only reconfigure if we're setting up a show with seasons and episodes
        if trakt_type != 'show' or i_type not in ['season', 'episode']:
            continue

        base = sync_dict.setdefault(key, {trakt_type: i.get(trakt_type)})
        seasons_list = base.setdefault('seasons', [])

        if i_type == 'season':
            new_season_item = i
            new_season_item.update(i['season'])
            seasons_list.append(new_season_item)
            continue

        s_num = i['episode']['season']

        for season in seasons_list:
            if season.get('number') == s_num:
                episodes_list = season.setdefault('episodes', [])
                break
        else:
            episodes_list = []
            seasons_list.append({'number': s_num, 'episodes': episodes_list})

        new_episode_item = i
        new_episode_item.update(i['episode'])
        episodes_list.append(new_episode_item)

    return sync_dict


def is_sync(self, trakt_type, unique_id, season=None, episode=None, id_type=None, sync_type=None):
    """ Returns item if item in sync list else None """
    from jurialmunkey.parser import try_int

    def _is_nested():
        try:
            sync_item_seasons = sync_item['seasons']
        except (KeyError, AttributeError):
            return
        if not sync_item_seasons:
            return
        se_n, ep_n = try_int(season), try_int(episode)
        for i in sync_item_seasons:
            if se_n != i.get('number'):
                continue
            if ep_n is None:
                return i
            try:
                sync_item_episodes = i['episodes']
            except (KeyError, AttributeError):
                return
            if not sync_item_episodes:
                return
            for j in sync_item_episodes:
                if ep_n == j.get('number'):
                    return j

    sync_list = self.get_sync(sync_type, trakt_type, id_type)
    try:
        sync_item = sync_list[unique_id]
    except KeyError:
        return
    if season is None:
        return sync_item
    return _is_nested()


@use_activity_cache('movies', 'watched_at', CACHE_LONG)
def get_sync_watched_movies(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/watched/movies', 'movie', id_type=id_type, extended=extended, allow_fallback=True)


@use_activity_cache('episodes', 'watched_at', CACHE_SHORT)  # Use short-cache to make sure we get newly aired metadata
def get_sync_watched_shows(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/watched/shows', 'show', id_type=id_type, extended=extended, allow_fallback=True)


@use_activity_cache('movies', 'collected_at', CACHE_LONG)
def get_sync_collection_movies(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/collection/movies', 'movie', id_type=id_type, extended=extended)


@use_activity_cache('episodes', 'collected_at', CACHE_LONG)
def get_sync_collection_shows(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/collection/shows', 'show', id_type=id_type, extended=extended)


@use_activity_cache('movies', 'paused_at', CACHE_LONG)
def get_sync_playback_movies(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/playback/movies', 'movie', id_type=id_type, extended=extended)


@use_activity_cache('episodes', 'paused_at', CACHE_LONG)
def get_sync_playback_shows(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/playback/episodes', 'show', id_type=id_type, extended=extended)


@use_activity_cache('movies', 'watchlisted_at', CACHE_LONG)
def get_sync_watchlist_movies(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/watchlist/movies', 'movie', id_type=id_type, extended=extended)


@use_activity_cache('shows', 'watchlisted_at', CACHE_LONG)
def get_sync_watchlist_shows(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/watchlist/shows', 'show', id_type=id_type, extended=extended)


@use_activity_cache('seasons', 'watchlisted_at', CACHE_LONG)
def get_sync_watchlist_seasons(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/watchlist/seasons', 'show', id_type=id_type, extended=extended)


@use_activity_cache('episodes', 'watchlisted_at', CACHE_LONG)
def get_sync_watchlist_episodes(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/watchlist/episodes', 'show', id_type=id_type, extended=extended)


@use_activity_cache('movies', 'favorited_at', CACHE_LONG)
def get_sync_favorites_movies(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/favorites/movies', 'movie', id_type=id_type, extended=extended)


@use_activity_cache('shows', 'favorited_at', CACHE_LONG)
def get_sync_favorites_shows(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/favorites/shows', 'show', id_type=id_type, extended=extended)


@use_activity_cache('movies', 'rated_at', CACHE_LONG)
def get_sync_ratings_movies(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/ratings/movies', 'movie', id_type=id_type, extended=extended)


@use_activity_cache('shows', 'rated_at', CACHE_LONG)
def get_sync_ratings_shows(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/ratings/shows', 'show', id_type=id_type, extended=extended)


@use_activity_cache('seasons', 'rated_at', CACHE_LONG)
def get_sync_ratings_seasons(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/ratings/seasons', 'show', id_type=id_type, extended=extended)


@use_activity_cache('episodes', 'rated_at', CACHE_LONG)
def get_sync_ratings_episodes(self, trakt_type, id_type=None, extended=None):
    return self.get_sync_configured('sync/ratings/episodes', 'show', id_type=id_type, extended=extended)


@use_thread_lock('TraktAPI.get_sync.Locked', timeout=10, polling=0.05, combine_name=True)
def get_sync(self, sync_type, trakt_type, id_type=None, extended=None):

    routes = {
        'watched': {
            'movie': self.get_sync_watched_movies,
            'show': self.get_sync_watched_shows,
        },
        'collection': {
            'movie': self.get_sync_collection_movies,
            'show': self.get_sync_collection_shows,
        },
        'playback': {
            'movie': self.get_sync_playback_movies,
            'show': self.get_sync_playback_shows,
        },
        'watchlist': {
            'movie': self.get_sync_watchlist_movies,
            'show': self.get_sync_watchlist_shows,
            'season': self.get_sync_watchlist_seasons,
            'episode': self.get_sync_watchlist_episodes,
        },
        'favorites': {
            'movie': self.get_sync_favorites_movies,
            'show': self.get_sync_favorites_shows,
        },
        'ratings': {
            'movie': self.get_sync_ratings_movies,
            'show': self.get_sync_ratings_shows,
            'season': self.get_sync_ratings_seasons,
            'episode': self.get_sync_ratings_episodes,
        },
    }

    func = routes[sync_type][trakt_type]
    fallback = {} if id_type else []  # ID Type lookup via dict whilst raw response is list
    sync_name = f'{sync_type}.{trakt_type}.{id_type}.{extended}'
    self.sync[sync_name] = self.sync.get(sync_name) or func(trakt_type, id_type, extended)
    return self.sync[sync_name] or fallback
