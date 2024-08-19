from tmdbhelper.lib.api.trakt.decorators import use_activity_cache, is_authorized
from tmdbhelper.lib.addon.consts import CACHE_SHORT, CACHE_LONG
from tmdbhelper.lib.addon.thread import use_thread_lock


def get_ondeck_list(self, page=1, limit=None, sort_by=None, sort_how=None, trakt_type=None):
    from tmdbhelper.lib.api.trakt.items import TraktItems
    from tmdbhelper.lib.items.pages import PaginatedItems
    limit = limit or self.sync_item_limit
    response = self.get_inprogress_items('show' if trakt_type == 'episode' else trakt_type)
    response = TraktItems(response, trakt_type=trakt_type).build_items(
        sort_by=sort_by, sort_how=sort_how)
    response = PaginatedItems(response['items'], page=page, limit=limit)
    return response.items + response.next_page


def get_towatch_list(self, trakt_type, page=1, limit=None):
    from tmdbhelper.lib.api.trakt.items import TraktItems
    from tmdbhelper.lib.items.pages import PaginatedItems
    limit = limit or self.sync_item_limit
    items_ip = self.get_inprogress_shows() if trakt_type == 'show' else self.get_inprogress_items('movie')
    items_wl = self.get_sync('watchlist', trakt_type)
    response = TraktItems(items_ip + items_wl, trakt_type=trakt_type).build_items(sort_by='activity', sort_how='desc')
    response = PaginatedItems(response['items'], page=page, limit=limit)
    return response.items + response.next_page


def get_inprogress_items(self, sync_type, lowest=5, highest=95):
    from jurialmunkey.parser import try_int
    response = self.get_sync('playback', sync_type)
    return [i for i in response if lowest <= try_int(i.get('progress', 0)) <= highest]


def get_inprogress_shows_list(self, page=1, limit=None, params=None, next_page=True, sort_by=None, sort_how=None):
    from tmdbhelper.lib.api.trakt.items import TraktItems
    from tmdbhelper.lib.items.pages import PaginatedItems
    limit = limit or self.sync_item_limit
    response = self.get_upnext_episodes_listitems(sort_by='released') if sort_by == 'year' else self.get_inprogress_shows()
    response = TraktItems(response, trakt_type='show').build_items(
        params_def=params, sort_by=sort_by if sort_by != 'year' else 'unsorted', sort_how=sort_how)
    response = PaginatedItems(response['items'], page=page, limit=limit)
    if not next_page:
        return response.items
    return response.items + response.next_page


def get_inprogress_shows(self):
    from tmdbhelper.lib.addon.tmdate import date_in_range
    from tmdbhelper.lib.api.trakt.items import TraktItems
    from tmdbhelper.lib.addon.thread import ParallelThread
    from tmdbhelper.lib.addon.plugin import get_setting

    def _get_calendar_episodes(startdate=-14, days=15, id_type='slug'):
        response = self.get_calendar_episodes(startdate=startdate, days=days)
        if not response:
            return
        calendar = {}
        for i in response:
            try:
                if not date_in_range(i['first_aired'], utc_convert=True, start_date=startdate, days=days):
                    continue
                if i['episode']['season'] == 0:  # Ignore specials
                    continue
                show = calendar.setdefault(i['show']['ids'][id_type], {})
                show.setdefault(i['episode']['season'], []).append(i['episode']['number'])
            except KeyError:
                continue
        return calendar
    response = self.get_sync('watched', 'show', extended='full')
    response = TraktItems(response).sort_items('watched', 'desc')
    hidden_shows = self.get_hiddenitems('show')
    calendar_episodes = _get_calendar_episodes() if get_setting('nextepisodes_usecalendar') else None
    with ParallelThread(response, self.is_inprogress_show, hidden_shows, calendar_episodes) as pt:
        item_queue = pt.queue
    return [i for i in item_queue if i]


def is_inprogress_show(self, item, hidden_shows=None, calendar_episodes=None):
    """
    Checks whether the show passed is in progress by comparing total and watched
    Optionally can pass a list of hidden_shows trakt slugs to ignore
    """
    from jurialmunkey.parser import find_dict_list_index

    def _calendar_is_watched():
        if not calendar_episodes or slug not in calendar_episodes:
            return True
        for season in calendar_episodes[slug]:
            x = find_dict_list_index(item['seasons'], 'number', season)
            if x is None:
                return False  # New Season Airing
            episodes = item['seasons'][x]['episodes']
            for episode in calendar_episodes[slug][season]:
                x = find_dict_list_index(episodes, 'number', episode)
                if x is None:
                    return False  # New Episode Airing
        return True

    try:
        show = item['show']
        slug = show['ids']['slug']
    except KeyError:
        return

    if hidden_shows and slug in hidden_shows:
        return

    try:
        aired_episodes = show['aired_episodes']
    except KeyError:
        return
    if not aired_episodes:
        return

    from tmdbhelper.lib.api.trakt.decorators import use_lastupdated_cache
    watch_episodes = use_lastupdated_cache(
        self._cache, self.get_episodes_watchcount, slug, 'slug', tvshow=item, count_progress=True,
        cache_name=f'TraktAPI.get_episodes_watchcount.response.slug.{slug}.True',
        sync_info=item) or 0

    if aired_episodes <= watch_episodes and _calendar_is_watched():
        return

    return item


@use_activity_cache('episodes', 'watched_at', cache_days=CACHE_LONG)
def get_episodes_watchcount(
        self, unique_id, id_type, season=None, exclude_specials=True,
        tvshow=None, count_progress=False
):
    """
    Get the number of episodes watched in a show or season
    Pass tvshow dict directly for speed otherwise will look-up ID from watched sync list
    Use count_progress to check progress against reset_at value rather than just count watched
    """
    from jurialmunkey.parser import try_int
    from tmdbhelper.lib.addon.tmdate import convert_timestamp

    season = try_int(season) if season is not None else None
    if not tvshow and id_type and unique_id:
        tvshow = self.get_sync('watched', 'show', id_type, extended='full').get(unique_id)
    if not tvshow:
        return
    reset_at = None
    if count_progress and tvshow.get('reset_at'):
        reset_at = convert_timestamp(tvshow['reset_at'])
    count = 0
    for i in tvshow.get('seasons', []):
        if season is not None and i.get('number', -1) != season:
            continue
        if exclude_specials and i.get('number') == 0:
            continue
        # Reset_at is None so just count length of watched episode list
        if not reset_at:
            count += len(i.get('episodes', []))
            continue
        # Reset_at has a value so check progress rather than just watched count
        for j in i.get('episodes', []):
            if convert_timestamp(j.get('last_watched_at')) >= reset_at:
                continue
            count += 1
    return count


@use_activity_cache(cache_days=CACHE_LONG)
def get_hiddenitems(self, trakt_type, progress_watched=True, progress_collected=True, calendar=True, id_type='slug'):
    """ Get items that are hidden on Trakt """
    def _get_comp_item(i):
        try:
            return i[trakt_type]['ids'][id_type]
        except (KeyError, AttributeError):
            return
    if not trakt_type or not id_type:
        return []
    response = []
    if progress_watched:
        response += self.get_response_json('users', 'hidden', 'progress_watched', type=trakt_type, limit=4095)
    if progress_collected:
        response += self.get_response_json('users', 'hidden', 'progress_collected', type=trakt_type, limit=4095)
    if calendar:
        response += self.get_response_json('users', 'hidden', 'calendar', type=trakt_type, limit=4095)
    hidden_items = {j for j in (_get_comp_item(i) for i in response) if j}
    return list(hidden_items)


def get_upnext_list(self, unique_id, id_type=None, page=1, limit=None):
    """ Gets the next episodes for a show that user should watch next """
    limit = limit or self.sync_item_limit
    if id_type != 'slug':
        unique_id = self.get_id(unique_id, id_type, 'show', output_type='slug')
    if not unique_id:
        return

    from tmdbhelper.lib.api.trakt.items import TraktItems
    from tmdbhelper.lib.items.pages import PaginatedItems

    showitem = self.get_details('show', unique_id)
    response = self.get_upnext_episodes(unique_id, showitem)
    response = TraktItems(response, trakt_type='episode').configure_items()
    response = PaginatedItems(response['items'], page=page, limit=limit)
    return response.items + response.next_page


def get_upnext_episodes_list(self, page=1, sort_by=None, sort_how='desc', limit=None):
    """ Gets a list of episodes for in-progress shows that user should watch next """
    from tmdbhelper.lib.api.trakt.items import TraktItems
    from tmdbhelper.lib.items.pages import PaginatedItems
    limit = limit or self.sync_item_limit
    response = self.get_upnext_episodes_listitems(sort_by=sort_by, sort_how=sort_how)
    response = TraktItems(response, trakt_type='episode').configure_items()
    response = PaginatedItems(response['items'], page=page, limit=limit)
    return response.items + response.next_page


def get_upnext_episodes_listitems(self, sort_by=None, sort_how='desc'):
    from tmdbhelper.lib.api.trakt.items import TraktItems
    from tmdbhelper.lib.addon.thread import ParallelThread

    shows = self.get_inprogress_shows() or []

    def _get_upnext_episodes(i, get_single_episode=True):
        """ Helper func for upnext episodes to pass through threaded """
        try:
            show = i['show']
            slug = show['ids']['slug']
        except (AttributeError, KeyError):
            return
        return self.get_upnext_episodes(slug, show, get_single_episode=get_single_episode)

    # Get upnext episodes threaded
    with ParallelThread(shows, _get_upnext_episodes) as pt:
        item_queue = pt.queue
    items = [i for i in item_queue if i]

    if not sort_by:
        return items

    with ParallelThread(items, self.get_showitem_details) as pt:
        item_queue = pt.queue
    items = [i for i in item_queue if i]

    items = TraktItems(items, trakt_type='episode').sort_items(sort_by, sort_how)
    return items


@use_activity_cache('episodes', 'watched_at', cache_days=CACHE_SHORT)
def get_show_progress(self, slug):
    if not slug:
        return
    from tmdbhelper.lib.api.trakt.decorators import use_lastupdated_cache
    return use_lastupdated_cache(
        self._cache, self.get_response_json, 'shows', slug, 'progress/watched',
        sync_info=self.get_sync('watched', 'show', 'slug', extended='full').get(slug),
        cache_name=f'TraktAPI.get_show_progress.response.{slug}')


@is_authorized
def get_upnext_episodes(self, slug, show, get_single_episode=False):
    """
    Get the next episode(s) to watch for a show
    Even though show dict is passed, slug is needed for cache naming purposes
    Set get_single_episode to only retrieve the next_episode value
    Otherwise returns a list of episodes to watch
    """
    # Get show progress
    response = self.get_show_progress(slug)
    if not response:
        return

    # For single episodes just grab next episode and add in show details as long as there's no reset_at date
    if get_single_episode and not response.get('reset_at') and response.get('next_episode'):
        return {'show': show, 'episode': response['next_episode']}

    # For list of episodes we need to build them by comparing against the reset_at date
    from tmdbhelper.lib.addon.tmdate import convert_timestamp
    reset_at = convert_timestamp(response['reset_at']) if response.get('reset_at') else None

    # Get next episode items as a generator for quicker next() item
    items = (
        {'show': show, 'episode': {'number': episode.get('number'), 'season': season.get('number')}}
        for season in response.get('seasons', []) for episode in season.get('episodes', [])
        if not episode.get('completed')
        or (reset_at and convert_timestamp(episode.get('last_watched_at')) < reset_at))

    # Only get next item in generator if getting a single episode to avoid unnecessarily checking all episodes
    if not get_single_episode:
        return items
    try:
        return next(items)
    except StopIteration:
        return


def get_movie_playcount(self, unique_id, id_type):
    try:
        return self.get_sync('watched', 'movie', id_type)[unique_id]['plays']
    except (AttributeError, KeyError):
        return


def get_movie_playprogress(self, unique_id, id_type, key='progress'):
    try:
        return self.get_sync('playback', 'movie', id_type)[unique_id][key]
    except (AttributeError, KeyError):
        return


@use_thread_lock("TraktAPI.get_episode_playprogress_list.Locked", timeout=10, polling=0.05)
@use_activity_cache('episodes', 'paused_at', cache_days=CACHE_LONG)
def get_episode_playprogress_list(self, id_type):
    from tmdbhelper.lib.files.futils import pickle_deepcopy

    sync_list = self.get_sync('playback', 'show')
    if not sync_list:
        return {}

    main_list = {}

    def _get_tv_show():
        try:
            return main_list[show_id]
        except KeyError:
            pass
        try:
            return pickle_deepcopy(i['show'])
        except KeyError:
            return {}

    def _get_episode():
        try:
            return pickle_deepcopy(i['episode'])
        except KeyError:
            return {}

    for i in sync_list:
        try:
            show_id = i['show']['ids'][id_type]
        except KeyError:
            continue

        tv_show = _get_tv_show()
        seasons = tv_show.setdefault('seasons', {})
        episode = _get_episode()
        season = seasons.setdefault(episode.get('season', 0), {})
        season[episode.get('number', 0)] = i
        main_list[show_id] = tv_show

    return main_list


@use_activity_cache('episodes', 'paused_at', cache_days=CACHE_LONG)
def get_episode_playprogress(self, unique_id, id_type, season, episode, key='progress'):
    from jurialmunkey.parser import try_int
    season = try_int(season, fallback=-2)  # Make fallback -2 to prevent matching on 0
    episode = try_int(episode, fallback=-2)  # Make fallback -2 to prevent matching on 0
    playprogress = self.get_episode_playprogress_list(id_type)
    if not playprogress or unique_id not in playprogress:
        return
    try:
        return playprogress[unique_id]['seasons'][season][episode][key]
    except (KeyError, AttributeError):
        return


@use_activity_cache('episodes', 'watched_at', cache_days=CACHE_LONG)
def get_episode_playcount(self, unique_id, id_type, season, episode):
    from jurialmunkey.parser import try_int
    season = try_int(season, fallback=-2)  # Make fallback -2 to prevent matching on 0
    episode = try_int(episode, fallback=-2)  # Make fallback -2 to prevent matching on 0
    try:
        response = self.get_sync('watched', 'show', id_type, extended='full')[unique_id]['seasons']
    except (KeyError, AttributeError):
        return
    for i in response:
        if i.get('number', -1) != season:
            continue
        try:
            episodes = i['episodes']
        except KeyError:
            continue
        for j in episodes:
            if j.get('number', -1) == episode:
                return j.get('plays', 1)


def get_episodes_airedcount(self, unique_id, id_type, season=None):
    """ Gets the number of aired episodes for a tvshow """
    try:
        tv_sync = self.get_sync('watched', 'show', id_type, extended='full')[unique_id]['show']
        aired_episodes = tv_sync['aired_episodes']
    except (KeyError, AttributeError):
        return
    if season is None or not aired_episodes:
        return aired_episodes
    try:
        trakt_id = tv_sync['ids']['trakt']
    except KeyError:
        trakt_id = None
    return self.get_season_episodes_airedcount(unique_id, id_type, season, trakt_id=trakt_id)


@use_activity_cache('episodes', 'watched_at', cache_days=CACHE_SHORT)
def get_season_episodes_airedcount(self, unique_id, id_type, season, trakt_id=None):
    from jurialmunkey.parser import try_int
    season = try_int(season, fallback=-2)
    if not trakt_id:
        trakt_id = self.get_id(unique_id, id_type, trakt_type='show', output_type='trakt')
    for i in self.get_request_sc('shows', trakt_id, 'seasons', extended='full'):
        if i.get('number', -1) == season:
            return i.get('aired_episodes')
