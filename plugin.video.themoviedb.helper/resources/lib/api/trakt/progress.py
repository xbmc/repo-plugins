import xbmc
import xbmcaddon
from resources.lib.addon.parser import try_int
from resources.lib.addon.timedate import convert_timestamp, date_in_range, get_region_date, get_datetime_today, get_timedelta
from resources.lib.files.cache import CACHE_SHORT, CACHE_LONG, use_simple_cache
from resources.lib.items.pages import PaginatedItems
from resources.lib.api.mapping import get_empty_item
from resources.lib.api.trakt.items import TraktItems, EPISODE_PARAMS
from resources.lib.api.trakt.decorators import is_authorized, use_activity_cache, use_lastupdated_cache
from resources.lib.addon.decorators import ParallelThread

ADDON = xbmcaddon.Addon('plugin.video.themoviedb.helper')


class _TraktProgress():
    @is_authorized
    def get_ondeck_list(self, page=1, limit=None, sort_by=None, sort_how=None, trakt_type=None):
        limit = limit or self.item_limit
        self._cache.del_cache('trakt.last_activities')  # Wipe last activities cache to update now
        response = self._get_inprogress_items('show' if trakt_type == 'episode' else trakt_type)
        response = TraktItems(response, trakt_type=trakt_type).build_items(
            sort_by=sort_by, sort_how=sort_how,
            params_def=EPISODE_PARAMS if trakt_type == 'episode' else None)
        response = PaginatedItems(response['items'], page=page, limit=limit)
        return response.items + response.next_page

    @is_authorized
    def get_towatch_list(self, trakt_type, page=1, limit=None):
        limit = limit or self.item_limit
        self._cache.del_cache('trakt.last_activities')  # Wipe last activities cache to update now
        items_ip = self._get_inprogress_shows() if trakt_type == 'show' else self._get_inprogress_items('movie')
        items_wl = self.get_sync('watchlist', trakt_type)
        response = TraktItems(items_ip + items_wl, trakt_type=trakt_type).build_items(sort_by='activity', sort_how='desc')
        response = PaginatedItems(response['items'], page=page, limit=limit)
        return response.items + response.next_page

    def _get_inprogress_items(self, sync_type, lowest=5, highest=95):
        self._cache.del_cache('trakt.last_activities')  # Wipe last activities cache to update now
        response = self.get_sync('playback', sync_type)
        return [i for i in response if lowest <= try_int(i.get('progress', 0)) <= highest]

    @is_authorized
    def get_inprogress_shows_list(self, page=1, limit=None, params=None, next_page=True, sort_by=None, sort_how=None):
        limit = limit or self.item_limit
        self._cache.del_cache('trakt.last_activities')  # Wipe last activities cache to update now
        response = self._get_upnext_episodes_list(sort_by_premiered=True) if sort_by == 'year' else self._get_inprogress_shows()
        response = TraktItems(response, trakt_type='show').build_items(
            params_def=params, sort_by=sort_by if sort_by != 'year' else 'unsorted', sort_how=sort_how)
        response = PaginatedItems(response['items'], page=page, limit=limit)
        if not next_page:
            return response.items
        return response.items + response.next_page

    def _get_inprogress_shows(self):
        response = self.get_sync('watched', 'show')
        response = TraktItems(response).sort_items('watched', 'desc')
        hidden_shows = self.get_hiddenitems('show')
        # return [i for i in response if self._is_inprogress_show(i, hidden_shows)]
        with ParallelThread(response, self._is_inprogress_show, hidden_shows) as pt:
            item_queue = pt.queue
        return [i for i in item_queue if i]

    def _is_inprogress_show(self, item, hidden_shows=None):
        """
        Checks whether the show passed is in progress by comparing total and watched
        Optionally can pass a list of hidden_shows trakt slugs to ignore
        """
        slug = item.get('show', {}).get('ids', {}).get('slug')
        if hidden_shows and slug in hidden_shows:
            return
        aired_episodes = item.get('show', {}).get('aired_episodes', 0)
        if not aired_episodes:
            return
        watch_episodes = use_lastupdated_cache(
            self._cache, self.get_episodes_watchcount, slug, 'slug', tvshow=item, count_progress=True,
            cache_name=u'TraktAPI.get_episodes_watchcount.response.slug.{}.True'.format(slug),
            sync_info=item) or 0
        if aired_episodes <= watch_episodes:
            return
        return item

    @is_authorized
    @use_activity_cache('episodes', 'watched_at', cache_days=CACHE_LONG)
    def get_episodes_watchcount(
            self, unique_id, id_type, season=None, exclude_specials=True,
            tvshow=None, count_progress=False):
        """
        Get the number of episodes watched in a show or season
        Pass tvshow dict directly for speed otherwise will look-up ID from watched sync list
        Use count_progress to check progress against reset_at value rather than just count watched
        """
        season = try_int(season) if season is not None else None
        if not tvshow and id_type and unique_id:
            tvshow = self.get_sync('watched', 'show', id_type).get(unique_id)
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

    @is_authorized
    @use_activity_cache(cache_days=CACHE_LONG)
    def get_hiddenitems(
            self, trakt_type, progress_watched=True, progress_collected=True,
            calendar=True, id_type='slug'):
        """ Get items that are hidden on Trakt """
        hidden_items = set()
        if not trakt_type or not id_type:
            return hidden_items
        if progress_watched:
            response = self.get_response_json('users', 'hidden', 'progress_watched', type=trakt_type, limit=4095)
            hidden_items |= {i.get(trakt_type, {}).get('ids', {}).get(id_type) for i in response}
        if progress_collected:
            response = self.get_response_json('users', 'hidden', 'progress_collected', type=trakt_type, limit=4095)
            hidden_items |= {i.get(trakt_type, {}).get('ids', {}).get(id_type) for i in response}
        if calendar:
            response = self.get_response_json('users', 'hidden', 'calendar', type=trakt_type, limit=4095)
            hidden_items |= {i.get(trakt_type, {}).get('ids', {}).get(id_type) for i in response}
        return list(hidden_items)

    @is_authorized
    # @use_activity_cache('episodes', 'watched_at', cache_days=CACHE_SHORT)
    def get_upnext_list(self, unique_id, id_type=None, page=1, limit=None):
        """ Gets the next episodes for a show that user should watch next """
        limit = limit or self.item_limit
        if id_type != 'slug':
            unique_id = self.get_id(unique_id, id_type, 'show', output_type='slug')
        if unique_id:
            showitem = self.get_details('show', unique_id)
            response = self.get_upnext_episodes(unique_id, showitem)
            response = TraktItems(response, trakt_type='episode').configure_items(params_def=EPISODE_PARAMS)
            response = PaginatedItems(response['items'], page=page, limit=limit)
            return response.items + response.next_page

    @is_authorized
    def get_upnext_episodes_list(self, page=1, sort_by_premiered=False, limit=None):
        """ Gets a list of episodes for in-progress shows that user should watch next """
        limit = limit or self.item_limit
        self._cache.del_cache('trakt.last_activities')  # Wipe last activities cache to update now
        response = self._get_upnext_episodes_list(sort_by_premiered=sort_by_premiered)
        response = TraktItems(response, trakt_type='episode').configure_items(params_def=EPISODE_PARAMS)
        response = PaginatedItems(response['items'], page=page, limit=limit)
        return response.items + response.next_page

    @is_authorized
    def _get_upnext_episodes_list(self, sort_by_premiered=False):
        shows = self._get_inprogress_shows() or []

        # items = [j for j in (self.get_upnext_episodes(
        #     i.get('show', {}).get('ids', {}).get('slug'), i.get('show', {}), get_single_episode=True)
        #     for i in shows) if j]
        # Get upnext episodes threaded
        with ParallelThread(shows, self._get_upnext_episodes) as pt:
            item_queue = pt.queue
        items = [i for i in item_queue if i]

        if not sort_by_premiered:
            return items

        with ParallelThread(items, self._get_item_details) as pt:
            item_queue = pt.queue
        items = [i for i in item_queue if i]

        items = TraktItems(items, trakt_type='episode').sort_items('released', 'desc')
        return items

    def _get_item_details(self, i):
        return {
            'show': i.get('show'),
            'episode': self.get_details(
                'show', i.get('show', {}).get('ids', {}).get('slug'),
                season=i.get('episode', {}).get('season'),
                episode=i.get('episode', {}).get('number')) or i.get('episode')}

    @is_authorized
    @use_activity_cache('episodes', 'watched_at', cache_days=CACHE_SHORT)
    def get_show_progress(self, slug):
        if not slug:
            return
        return use_lastupdated_cache(
            self._cache, self.get_response_json, 'shows', slug, 'progress/watched',
            sync_info=self.get_sync('watched', 'show', 'slug').get(slug),
            cache_name=u'TraktAPI.get_show_progress.response.{}'.format(slug))

    def _get_upnext_episodes(self, i, get_single_episode=True):
        """ Helper func for upnext episodes to pass through threaded """
        slug = i.get('show', {}).get('ids', {}).get('slug')
        show = i.get('show', {})
        return self.get_upnext_episodes(slug, show, get_single_episode=get_single_episode)

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
        # For single episodes just grab next episode and add in show details
        if get_single_episode:
            if not response.get('next_episode'):
                return
            return {'show': show, 'episode': response['next_episode']}
        # For list of episodes we need to build them
        # Get show reset_at value
        reset_at = None
        if response.get('reset_at'):
            reset_at = convert_timestamp(response['reset_at'])
        # Get next episode items
        return [
            {'show': show, 'episode': {'number': episode.get('number'), 'season': season.get('number')}}
            for season in response.get('seasons', []) for episode in season.get('episodes', [])
            if not episode.get('completed')
            or (reset_at and convert_timestamp(episode.get('last_watched_at')) < reset_at)]

    @is_authorized
    def get_movie_playcount(self, unique_id, id_type):
        return self.get_sync('watched', 'movie', id_type).get(unique_id, {}).get('plays')

    @is_authorized
    def get_movie_playprogress(self, unique_id, id_type):
        return self.get_sync('playback', 'movie', id_type).get(unique_id, {}).get('progress')

    @is_authorized
    @use_activity_cache('episodes', 'watched_at', cache_days=CACHE_LONG)
    def _get_episode_playprogress(self, id_type):
        sync_list = self.get_sync('playback', 'show')
        if not sync_list:
            return []
        main_list = {}
        for i in sync_list:
            show_id = i.get('show', {}).get('ids', {}).get(id_type)
            if not show_id:
                continue
            show_item = main_list.get(show_id) or i.pop('show', None) or {}
            seasons = show_item.setdefault('seasons', {})
            season = seasons.setdefault(i.get('episode', {}).get('season', 0), {})
            season[i.get('episode', {}).get('number', 0)] = i
            main_list[show_id] = show_item
        return main_list

    @is_authorized
    @use_activity_cache('episodes', 'watched_at', cache_days=CACHE_LONG)
    def get_episode_playprogress(self, unique_id, id_type, season, episode):
        season = try_int(season, fallback=-2)  # Make fallback -2 to prevent matching on 0
        episode = try_int(episode, fallback=-2)  # Make fallback -2 to prevent matching on 0
        return self._get_episode_playprogress(id_type).get(
            unique_id, {}).get('seasons', {}).get(season, {}).get(episode, {}).get('progress')

    @is_authorized
    @use_activity_cache('episodes', 'watched_at', cache_days=CACHE_LONG)
    def get_episode_playcount(self, unique_id, id_type, season, episode):
        season = try_int(season, fallback=-2)  # Make fallback -2 to prevent matching on 0
        episode = try_int(episode, fallback=-2)  # Make fallback -2 to prevent matching on 0
        for i in self.get_sync('watched', 'show', id_type).get(unique_id, {}).get('seasons', []):
            if i.get('number', -1) != season:
                continue
            for j in i.get('episodes', []):
                if j.get('number', -1) == episode:
                    return j.get('plays', 1)

    @is_authorized
    def get_episodes_airedcount(self, unique_id, id_type, season=None):
        """ Gets the number of aired episodes for a tvshow """
        tv_sync = self.get_sync('watched', 'show', id_type).get(unique_id, {}).get('show', {})
        aired_episodes = tv_sync.get('aired_episodes')
        if season is None or not aired_episodes:  # Don't get seasons if we don't have tvshow data
            return aired_episodes
        return self.get_season_episodes_airedcount(unique_id, id_type, season, trakt_id=tv_sync.get('ids', {}).get('trakt'))

    @is_authorized
    @use_activity_cache('episodes', 'watched_at', cache_days=CACHE_SHORT)
    def get_season_episodes_airedcount(self, unique_id, id_type, season, trakt_id=None):
        season = try_int(season, fallback=-2)
        if not trakt_id:
            trakt_id = self.get_id(unique_id, id_type, trakt_type='show', output_type='trakt')
        for i in self.get_request_sc('shows', trakt_id, 'seasons', extended='full'):
            if i.get('number', -1) == season:
                return i.get('aired_episodes')

    def get_calendar(self, trakt_type, user=True, start_date=None, days=None):
        user = 'my' if user else 'all'
        return self.get_response_json('calendars', user, trakt_type, start_date, days, extended='full')

    @use_simple_cache(cache_days=0.25)
    def get_calendar_episodes(self, startdate=0, days=1, user=True):
        # Broaden date range in case utc conversion bumps into different day
        mod_date = try_int(startdate) - 1
        mod_days = try_int(days) + 2
        date = get_datetime_today() + get_timedelta(days=mod_date)
        return self.get_calendar('shows', user, start_date=date.strftime('%Y-%m-%d'), days=mod_days)

    def _get_calendar_episode_item(self, i):
        air_date = convert_timestamp(i.get('first_aired'), utc_convert=True)
        item = get_empty_item()
        item['label'] = i.get('episode', {}).get('title')
        item['infolabels'] = {
            'mediatype': 'episode',
            'premiered': air_date.strftime('%Y-%m-%d'),
            'year': air_date.strftime('%Y'),
            'title': item['label'],
            'episode': i.get('episode', {}).get('number'),
            'season': i.get('episode', {}).get('season'),
            'tvshowtitle': i.get('show', {}).get('title'),
            'duration': try_int(i.get('episode', {}).get('runtime', 0)) * 60,
            'plot': i.get('episode', {}).get('overview'),
            'mpaa': i.get('show', {}).get('certification')}
        item['infoproperties'] = {
            'air_date': get_region_date(air_date, 'datelong'),
            'air_time': get_region_date(air_date, 'time'),
            'air_day': air_date.strftime('%A'),
            'air_day_short': air_date.strftime('%a'),
            'air_date_short': air_date.strftime('%d %b')}
        days_to_air = (air_date.date() - get_datetime_today().date()).days
        dtaproperty = 'days_from_aired' if days_to_air < 0 else 'days_until_aired'
        item['infoproperties'][dtaproperty] = str(abs(days_to_air))
        item['unique_ids'] = {u'tvshow.{}'.format(k): v for k, v in i.get('show', {}).get('ids', {}).items()}
        item['params'] = {
            'info': 'details',
            'tmdb_type': 'tv',
            'tmdb_id': i.get('show', {}).get('ids', {}).get('tmdb'),
            'episode': i.get('episode', {}).get('number'),
            'season': i.get('episode', {}).get('season')}
        return item

    def _get_calendar_episode_item_bool(self, i, kodi_db, user, startdate, days):
        if kodi_db and not user and not kodi_db.get_info(
                info='dbid',
                tmdb_id=i.get('show', {}).get('ids', {}).get('tmdb'),
                tvdb_id=i.get('show', {}).get('ids', {}).get('tvdb'),
                imdb_id=i.get('show', {}).get('ids', {}).get('imdb')):
            return False
        # Do some timezone conversion so we check that we're in the date range for our timezone
        if not date_in_range(i.get('first_aired'), utc_convert=True, start_date=startdate, days=days):
            return False
        return True

    def _get_stacked_item(self, next_item, last_item):
        # If the next item is the same show then we stack the details onto the last item and add it next iteration
        ip = last_item['infoproperties']

        # First time setup
        if not ip.get('stacked_count'):
            ip['stacked_count'] = 1
            ti = last_item['infolabels']['title']
            se = '{season}x{episode:0>2}'.format(season=try_int(
                last_item['infolabels']['season']), episode=try_int(last_item['infolabels']['episode']))
            ep = '{episode}. {label}'.format(episode=se, label=ti)
            ip['stacked_labels'] = ep
            ip['stacked_titles'] = ti
            ip['stacked_episodes'] = se
            ip['stacked_first'] = '{season}x{episode:0>2}'.format(
                season=try_int(last_item['infolabels'].get('season')),
                episode=try_int(last_item['infolabels'].get('episode')))
            ip['stacked_first_episode'] = last_item['infolabels']['episode']
            ip['stacked_first_season'] = last_item['infolabels']['season']
            ip['no_label_formatting'] = True
            last_item['params'].pop('episode', None)
            last_item['params']['info'] = 'episodes'
            last_item['is_folder'] = True

        # Stacked Setup
        ti = next_item['infolabels']['title']
        se = '{season}x{episode:0>2}'.format(season=try_int(
            next_item['infolabels']['season']), episode=try_int(next_item['infolabels']['episode']))
        ep = '{episode}. {label}'.format(episode=se, label=ti)
        ip['stacked_count'] = ip.get('stacked_count', 1) + 1
        ip['stacked_labels'] = '{}, {}'.format(ip['stacked_labels'], ep)
        ip['stacked_titles'] = '{}, {}'.format(ip['stacked_titles'], ti)
        ip['stacked_episodes'] = '{}, {}'.format(ip['stacked_episodes'], se)
        ip['stacked_last'] = se
        ip['stacked_last_episode'] = next_item['infolabels']['episode']
        ip['stacked_last_season'] = next_item['infolabels']['season']
        last_item['label'] = '{first_ep}-{final_ep}. {ep_count}'.format(
            ep_count='{} {}'.format(ip['stacked_count'], xbmc.getLocalizedString(20360)),
            first_ep=ip['stacked_first'],
            final_ep=ip['stacked_last'])
        return last_item

    def _stack_calendar_episodes(self, episode_list, flipped=False):
        items = []
        last_item = None
        for i in reversed(episode_list) if flipped else episode_list:
            if not last_item:
                last_item = i
                continue

            # If the next item is a different show or day then we stop stacking and add the item
            if (
                    last_item['infolabels']['tvshowtitle'] != i['infolabels']['tvshowtitle']
                    or last_item['infolabels']['premiered'] != i['infolabels']['premiered']
            ):
                items.append(last_item)
                last_item = i
                continue

            last_item = self._get_stacked_item(i, last_item)

        else:  # The last item in the list won't be added in the for loop so do an extra action at the end to add it
            if last_item:
                items.append(last_item)
        return items[::-1] if flipped else items

    def _stack_calendar_tvshows(self, tvshow_list, flipped=False):
        items, titles = [], []
        for i in reversed(tvshow_list) if flipped else tvshow_list:
            t = i['infolabels']['title']
            if t not in titles:
                items.append(i)
                titles.append(t)
                continue
            x = titles.index(t)
            i = items[x]
            i['infoproperties']['stacked_count'] = i['infoproperties'].get('stacked_count', 0) + 1
        return items[::-1] if flipped else items

    @use_simple_cache(cache_days=0.25)
    def _get_calendar_episodes_list(self, startdate=0, days=1, user=True, kodi_db=None, stack=True):
        # Get response
        response = self.get_calendar_episodes(startdate=startdate, days=days, user=user)
        if not response:
            return
        # Reverse items for date ranges in past
        traktitems = reversed(response) if startdate < -1 else response
        items = [self._get_calendar_episode_item(i) for i in traktitems if self._get_calendar_episode_item_bool(i, kodi_db, user, startdate, days)]
        return self._stack_calendar_episodes(items, flipped=startdate < -1) if stack else items

    def get_calendar_episodes_list(self, startdate=0, days=1, user=True, kodi_db=None, page=1, limit=None):
        limit = limit or self.item_limit
        response_items = self._get_calendar_episodes_list(startdate, days, user, kodi_db, stack=ADDON.getSettingBool('calendar_flatten'))
        response = PaginatedItems(response_items, page=page, limit=limit)
        if response and response.items:
            return response.items + response.next_page
