from resources.lib.container.pages import PaginatedItems
from resources.lib.trakt.items import TraktItems
from resources.lib.trakt.decorators import is_authorized, use_activity_cache, use_lastupdated_cache
from resources.lib.addon.parser import try_int
from resources.lib.addon.timedate import convert_timestamp, date_in_range, get_region_date, get_datetime_today, get_timedelta
from resources.lib.api.mapping import get_empty_item
from resources.lib.addon.cache import CACHE_SHORT, CACHE_LONG, use_simple_cache


class _TraktProgress():
    @is_authorized
    def get_inprogress_shows_list(self, page=1, limit=20, params=None, next_page=True, sort_by=None, sort_how=None):
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
        return [i for i in response if self._is_inprogress_show(i, hidden_shows)]

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
    def get_upnext_list(self, unique_id, id_type=None, page=1):
        """ Gets the next episodes for a show that user should watch next """
        if id_type != 'slug':
            unique_id = self.get_id(unique_id, id_type, 'show', output_type='slug')
        if unique_id:
            showitem = self.get_details('show', unique_id)
            response = self.get_upnext_episodes(unique_id, showitem)
            response = TraktItems(response, trakt_type='episode').configure_items(params_def={
                'info': 'details', 'tmdb_type': '{tmdb_type}', 'tmdb_id': '{tmdb_id}',
                'season': '{season}', 'episode': '{number}'})
            response = PaginatedItems(response['items'], page=page, limit=10)
            return response.items + response.next_page

    @is_authorized
    def get_upnext_episodes_list(self, page=1, sort_by_premiered=False):
        """ Gets a list of episodes for in-progress shows that user should watch next """
        response = self._get_upnext_episodes_list(sort_by_premiered=sort_by_premiered)
        response = TraktItems(response, trakt_type='episode').configure_items(params_def={
            'info': 'details', 'tmdb_type': '{tmdb_type}', 'tmdb_id': '{tmdb_id}',
            'season': '{season}', 'episode': '{number}'})
        response = PaginatedItems(response['items'], page=page, limit=10)
        return response.items + response.next_page

    @is_authorized
    def _get_upnext_episodes_list(self, sort_by_premiered=False):
        shows = self._get_inprogress_shows() or []
        items = [j for j in (self.get_upnext_episodes(
            i.get('show', {}).get('ids', {}).get('slug'), i.get('show', {}), get_single_episode=True)
            for i in shows) if j]
        if sort_by_premiered:
            items = [
                {'show': i.get('show'), 'episode': self.get_details(
                    'show', i.get('show', {}).get('ids', {}).get('slug'),
                    season=i.get('episode', {}).get('season'),
                    episode=i.get('episode', {}).get('number')) or i.get('episode')}
                for i in items]
            items = TraktItems(items, trakt_type='episode').sort_items('released', 'desc')
        return items

    @is_authorized
    @use_activity_cache('episodes', 'watched_at', cache_days=CACHE_SHORT)
    def get_show_progress(self, slug):
        if not slug:
            return
        return use_lastupdated_cache(
            self._cache, self.get_response_json, 'shows', slug, 'progress/watched',
            sync_info=self.get_sync('watched', 'show', 'slug').get(slug),
            cache_name=u'TraktAPI.get_show_progress.response.{}'.format(slug))

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
    # @use_activity_cache('movies', 'watched_at', cache_days=CACHE_LONG)
    def get_movie_playcount(self, unique_id, id_type):
        return self.get_sync('watched', 'movie', id_type).get(unique_id, {}).get('plays')

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
    @use_activity_cache('episodes', 'watched_at', cache_days=CACHE_SHORT)
    def get_episodes_airedcount(self, unique_id, id_type, season=None):
        """ Gets the number of aired episodes for a tvshow """
        if season is not None:
            return self.get_season_episodes_airedcount(unique_id, id_type, season)
        return self.get_sync('watched', 'show', id_type).get(unique_id, {}).get('show', {}).get('aired_episodes')

    @is_authorized
    @use_activity_cache('episodes', 'watched_at', cache_days=CACHE_SHORT)
    def get_season_episodes_airedcount(self, unique_id, id_type, season):
        season = try_int(season, fallback=-2)
        slug = self.get_id(unique_id, id_type, trakt_type='show', output_type='slug')
        for i in self.get_request_sc('shows', slug, 'seasons', extended='full'):
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

    @use_simple_cache(cache_days=0.25)
    def _get_calendar_episodes_list(self, startdate=0, days=1, user=True, kodi_db=None):
        # Get response
        response = self.get_calendar_episodes(startdate=startdate, days=days, user=user)
        if not response:
            return
        # Reverse items for date ranges in past
        traktitems = reversed(response) if startdate < -1 else response
        return [self._get_calendar_episode_item(i) for i in traktitems if self._get_calendar_episode_item_bool(
            i, kodi_db, user, startdate, days)]

    def get_calendar_episodes_list(self, startdate=0, days=1, user=True, kodi_db=None, page=1, limit=20):
        response_items = self._get_calendar_episodes_list(startdate, days, user, kodi_db)
        response = PaginatedItems(response_items, page=page, limit=limit)
        if response and response.items:
            return response.items + response.next_page
