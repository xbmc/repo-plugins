from json import loads, dumps
import resources.lib.utils as utils
from resources.lib.requestapi import RequestAPI
from resources.lib.listitem import ListItem
import xbmc
import random
import xbmcgui
import datetime


class TraktAPI(RequestAPI):
    def __init__(self, force=False, cache_short=None, cache_long=None, tmdb=None, login=False):
        super(TraktAPI, self).__init__(
            cache_short=cache_short, cache_long=cache_long,
            req_api_url='https://api.trakt.tv/', req_api_name='Trakt')
        self.authorization = ''
        self.sync = {}
        self.last_activities = None
        self.prev_activities = None
        self.refreshcheck = 0
        self.attempedlogin = False
        self.dialog_noapikey_header = u'{0} {1} {2}'.format(self.addon.getLocalizedString(32007), self.req_api_name, self.addon.getLocalizedString(32011))
        self.dialog_noapikey_text = self.addon.getLocalizedString(32012)
        self.client_id = 'e6fde6173adf3c6af8fd1b0694b9b84d7c519cefc24482310e1de06c6abe5467'
        self.client_secret = '15119384341d9a61c751d8d515acbc0dd801001d4ebe85d3eef9885df80ee4d9'
        self.headers = {'trakt-api-version': '2', 'trakt-api-key': self.client_id, 'Content-Type': 'application/json'}
        self.tmdb = tmdb
        self.library = 'video'

        if force:
            self.login()
            return

        self.authorize(login)

    def authorize(self, login=False):
        if self.authorization:
            return self.authorization
        token = self.addon.getSettingString('trakt_token')
        token = loads(token) if token else None
        if token and type(token) is dict and token.get('access_token'):
            self.authorization = token
            self.headers['Authorization'] = 'Bearer {0}'.format(self.authorization.get('access_token'))
        elif login:
            if not self.attempedlogin and xbmcgui.Dialog().yesno(self.dialog_noapikey_header, self.dialog_noapikey_text, '', '', 'Cancel', 'OK'):
                self.login()
            self.attempedlogin = True
        if self.authorization:
            xbmcgui.Window(10000).setProperty('TMDbHelper.TraktIsAuth', 'True')
        return self.authorization

    def login(self):
        self.code = self.get_api_request('https://api.trakt.tv/oauth/device/code', postdata={'client_id': self.client_id})
        if not self.code.get('user_code') or not self.code.get('device_code'):
            return  # TODO: DIALOG: Authentication Error
        self.progress = 0
        self.interval = self.code.get('interval', 5)
        self.expirein = self.code.get('expires_in', 0)
        self.auth_dialog = xbmcgui.DialogProgress()
        self.auth_dialog.create(
            self.addon.getLocalizedString(32097),
            self.addon.getLocalizedString(32096),
            self.addon.getLocalizedString(32095) + ': [B]' + self.code.get('user_code') + '[/B]')
        self.poller()

    def refresh_token(self):
        if not self.authorization or not self.authorization.get('refresh_token'):
            self.login()
            return
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
        if self.authorization:
            self.on_authenticated()
            return
        xbmc.Monitor().waitForAbort(self.interval)
        if xbmc.Monitor().abortRequested():
            return
        self.poller()

    def on_aborted(self):
        """Triggered when device authentication was aborted"""
        utils.kodi_log(u'Trakt Authentication Aborted!', 1)
        self.auth_dialog.close()

    def on_expired(self):
        """Triggered when the device authentication code has expired"""
        utils.kodi_log(u'Trakt Authentication Expired!', 1)
        self.auth_dialog.close()

    def on_authenticated(self, auth_dialog=True):
        """Triggered when device authentication has been completed"""
        utils.kodi_log(u'Trakt Authenticated Successfully!', 1)
        self.addon.setSettingString('trakt_token', dumps(self.authorization))
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

    def invalid_apikey(self):
        if self.refreshcheck == 0:
            self.refresh_token()
        self.refreshcheck += 1

    def get_response(self, *args, **kwargs):
        response = self.get_api_request(self.get_request_url(*args, **kwargs), headers=self.headers, dictify=False)
        if self.refreshcheck == 1:
            self.get_response(*args, **kwargs)
        return response

    def get_response_json(self, *args, **kwargs):
        response = self.get_response(*args, **kwargs)
        return response.json() if response else {}

    def get_request(self, *args, **kwargs):
        return self.use_cache(self.get_response_json, *args, **kwargs)

    def get_itemlist_sorted(self, *args, **kwargs):
        response = self.get_response(*args, extended='full')
        items = response.json()
        reverse = True if response.headers.get('X-Sort-How') == 'desc' else False
        if response.headers.get('X-Sort-By') == 'rank':
            return sorted(items, key=lambda i: i.get('rank'), reverse=reverse)
        elif response.headers.get('X-Sort-By') == 'added':
            return sorted(items, key=lambda i: i['listed_at'], reverse=reverse)
        elif response.headers.get('X-Sort-By') == 'title':
            return sorted(items, key=lambda i: i.get(i.get('type'), {}).get('title'), reverse=reverse)
        elif response.headers.get('X-Sort-By') == 'released':
            return sorted(items, key=lambda i: i.get(i.get('type'), {}).get('first_aired') if i.get('type') == 'show' else i.get(i.get('type'), {}).get('released'), reverse=reverse)
        elif response.headers.get('X-Sort-By') == 'runtime':
            return sorted(items, key=lambda i: i.get(i.get('type'), {}).get('runtime'), reverse=reverse)
        elif response.headers.get('X-Sort-By') == 'popularity':
            return sorted(items, key=lambda i: i.get(i.get('type'), {}).get('comment_count'), reverse=reverse)
        elif response.headers.get('X-Sort-By') == 'percentage':
            return sorted(items, key=lambda i: i.get(i.get('type'), {}).get('rating'), reverse=reverse)
        elif response.headers.get('X-Sort-By') == 'votes':
            return sorted(items, key=lambda i: i.get(i.get('type'), {}).get('votes'), reverse=reverse)
        elif response.headers.get('X-Sort-By') == 'random':
            random.shuffle(items)
            return items
        return sorted(items, key=lambda i: i['listed_at'], reverse=True)

    def get_itemlist_ranked(self, *args, **kwargs):
        response = self.get_response(*args)
        items = response.json()
        return sorted(items, key=lambda i: i['rank'], reverse=False)

    def get_imdb_top250(self):
        return self.use_cache(self.get_itemlist_ranked, 'users', 'nielsz', 'lists', 'active-imdb-top-250', 'items')

    def get_itemlist_sortedcached(self, *args, **kwargs):
        page = kwargs.pop('page', 1)
        limit = kwargs.pop('limit', 10)
        cache_refresh = True if page == 1 else False
        kwparams = {'cache_name': self.cache_name + '.trakt.sortedlist.v3', 'cache_days': 0.125, 'cache_refresh': cache_refresh}
        items = self.use_cache(self.get_itemlist_sorted, *args, **kwparams)
        index_z = page * limit
        index_a = index_z - limit
        index_z = len(items) if len(items) < index_z else index_z
        return {'items': items[index_a:index_z], 'pagecount': -(-len(items) // limit)}

    def get_itemlist(self, *args, **kwargs):
        items = []

        if not self.tmdb or (kwargs.pop('req_auth', False) and not self.authorize()):
            return items

        key_list = kwargs.pop('key_list', ['dummy'])
        rnd_list = kwargs.pop('rnd_list', 0)
        usr_list = kwargs.pop('usr_list', False)

        this_page = int(kwargs.get('page', 1))
        limit = kwargs.get('limit', 0)

        if usr_list:  # Check if userlist and apply special sorting
            kwparams = {'page': this_page, 'limit': limit}
            response = self.get_itemlist_sortedcached(*args, **kwparams)
            itemlist = response.get('items')
            if not itemlist:
                return items
            last_page = response.get('pagecount')
        else:
            response = self.get_response(*args, **kwargs)
            if not response:
                return items
            itemlist = response.json()
            last_page = int(response.headers.get('X-Pagination-Page-Count', 0))

        next_page = this_page + 1 if this_page < last_page and not rnd_list else False

        if rnd_list:
            rnd_list = random.sample(range(len(itemlist) - 1), rnd_list)
            itemlist = [itemlist[i] for i in rnd_list]

        n = 0
        for i in itemlist:
            if limit and not n < limit:
                break

            for key in key_list:
                if limit and not n < limit:
                    break

                myitem = i.get(key) or i

                if not myitem:
                    continue

                tmdbtype = 'tv' if key == 'show' else 'movie'

                item = None
                if myitem.get('ids', {}).get('imdb'):
                    item = self.tmdb.get_externalid_item(tmdbtype, myitem.get('ids', {}).get('imdb'), 'imdb_id')
                elif myitem.get('ids', {}).get('tvdb'):
                    item = self.tmdb.get_externalid_item(tmdbtype, myitem.get('ids', {}).get('tvdb'), 'tvdb_id')

                if not item:
                    continue

                item['mixed_type'] = tmdbtype
                items.append(ListItem(library=self.library, **item))
                n += 1

        if next_page:
            items.append(ListItem(library=self.library, label=xbmc.getLocalizedString(33078), nextpage=next_page))

        return items

    def get_limitedlist(self, itemlist, tmdbtype, limit, islistitem):
        items, added_items = [], []
        if not self.tmdb or not self.authorize():
            return items

        n = 0
        itemtype = utils.type_convert(tmdbtype, 'trakt')
        for i in itemlist:
            if limit and n >= limit:
                break
            item = (
                i.get(itemtype, {}).get('ids', {}).get('slug'),
                i.get(itemtype, {}).get('ids', {}).get('tmdb'),
                i.get(itemtype, {}).get('title'))

            if item in added_items:
                continue

            added_items.append(item)
            if islistitem:
                item = ListItem(library=self.library, **self.tmdb.get_detailed_item(tmdbtype, item[1]))
            items.append(item)
            n += 1

        return items

    def get_ratings(self, tmdbtype=None, imdb_id=None, trakt_id=None, trakt_slug=None, season=None, episode=None):
        slug = trakt_slug or trakt_id or imdb_id
        infoproperties = {}
        if not slug or not tmdbtype:
            return infoproperties
        url = 'episodes/{0}/ratings'.format(episode) if episode else 'ratings'
        url = 'seasons/{0}/{1}'.format(season, url) if season else 'ratings'
        response = self.get_request_lc(utils.type_convert(tmdbtype, 'trakt') + 's', slug, url)
        infoproperties['trakt_rating'] = '{:0.1f}'.format(response.get('rating')) if response.get('rating') else ''
        infoproperties['trakt_votes'] = '{:0,.0f}'.format(response.get('votes')) if response.get('votes') else ''
        return infoproperties

    def get_mostwatched(self, userslug, tmdbtype, limit=None, islistitem=True, onlyshows=False):
        extended = 'noseasons' if onlyshows else None
        history = self.get_response_json('users', userslug, 'watched', utils.type_convert(tmdbtype, 'trakt') + 's', extended=extended)
        history = sorted(history, key=lambda i: i['plays'], reverse=True)
        return self.get_limitedlist(history, tmdbtype, limit, islistitem)

    def get_inprogress_movies(self, limit=None, islistitem=True):
        history = self.get_response_json('sync', 'playback', 'movies', extended='noseasons')
        history = sorted(history, key=lambda i: i['paused_at'], reverse=True)
        return self.get_limitedlist(history, 'movie', limit, islistitem)

    def get_recentlywatched_shows(self, userslug, limit=None, islistitem=True):
        history = self.get_response_json('users', userslug, 'watched', 'shows', extended='noseasons')
        history = sorted(history, key=lambda i: i['last_watched_at'], reverse=True)
        return self.get_limitedlist(history, 'tv', limit, islistitem)

    def get_recentlywatched(self, userslug, tmdbtype, limit=None, islistitem=True, months=6):
        start_at = datetime.date.today() - datetime.timedelta(months * 365 / 12)
        history = self.get_response_json('users', userslug, 'history', utils.type_convert(tmdbtype, 'trakt') + 's', page=1, limit=200, start_at=start_at.strftime("%Y-%m-%d"))
        return self.get_limitedlist(history, tmdbtype, limit, islistitem)

    def get_inprogress(self, userslug, limit=None, episodes=False):
        """
        UPDATED: Now looks at all shows sorted by recently watched
        OLD VERSION: Looked at user's most recently watched 200 episodes in last 3 years
        Adds each unique show to list in order then checks if show has an upnext episode
        Returns list of tmdb_ids representing shows with upnext episodes in recently watched order
        """
        items = []
        if not self.tmdb or not self.authorize():
            return items

        n = 0
        # utils.kodi_log(u'Getting In-Progress For Trakt User {0}'.format(userslug), 2)
        last_updated = self.get_response_json('sync/last_activities')
        last_updated = last_updated.get('episodes', {}).get('watched_at') if last_updated else None
        for i in self.get_recentlywatched_shows(userslug, islistitem=False):
            if limit and n >= limit:
                break
            # utils.kodi_log(u'In-Progress -- Searching Next Episode For:\n{0}'.format(i), 1)
            progress = self.get_upnext(i[0], True, last_updated=last_updated)
            if progress and progress.get('next_episode'):
                if (episodes and
                        progress.get('next_episode', {}).get('season') == 1 and
                        progress.get('next_episode', {}).get('number') == 1):
                    continue
                # utils.kodi_log(u'In-Progress -- Found Next Episode:\n{0}'.format(progress.get('next_episode')), 2)
                season = progress.get('next_episode', {}).get('season') if episodes else None
                episode = progress.get('next_episode', {}).get('number') if episodes else None
                item = self.tmdb.get_detailed_item('tv', i[1], season=season, episode=episode)
                item['tmdb_id'] = i[1]
                # utils.kodi_log(u'In-Progress -- Got Next Episode Details:\n{0}'.format(item), 2)
                items.append(ListItem(library=self.library, **item))
                n += 1
        return sorted(items, key=lambda i: i.infolabels.get('premiered'), reverse=True) if episodes and self.addon.getSettingString('trakt_nextepisodesort') == 'airdate' else items

    def get_airingshows(self, start_date=0, days=1):
        start_date = datetime.date.today() + datetime.timedelta(days=start_date)
        return self.get_response_json('calendars', 'all', 'shows', start_date.strftime('%Y-%m-%d'), days, extended='full')

    def get_calendar(self, tmdbtype, user=True, start_date=None, days=None):
        user = 'my' if user else 'all'
        return self.get_response_json('calendars', user, tmdbtype, start_date, days, extended='full')

    def get_calendar_properties(self, item, i):
        # Create our airing properties
        air_date = utils.convert_timestamp(i.get('first_aired'), utc_convert=True)
        item.infolabels['premiered'] = air_date.strftime('%Y-%m-%d')
        item.infolabels['year'] = air_date.strftime('%Y')
        item.infoproperties['air_date'] = utils.get_region_date(air_date, 'datelong')
        item.infoproperties['air_time'] = utils.get_region_date(air_date, 'time')
        item.infoproperties['air_day'] = air_date.strftime('%A')
        item.infoproperties['air_day_short'] = air_date.strftime('%a')
        item.infoproperties['air_date_short'] = air_date.strftime('%d %b')

        # Do some fallback properties in-case TMDb doesn't have info
        item.infolabels['title'] = item.label = i.get('episode', {}).get('title')
        item.infolabels['episode'] = item.infolabels.get('episode') or i.get('episode', {}).get('number')
        item.infolabels['season'] = item.infolabels.get('season') or i.get('episode', {}).get('season')
        item.infolabels['tvshowtitle'] = i.get('show', {}).get('title')
        item.infolabels['duration'] = item.infolabels.get('duration') or utils.try_parse_int(i.get('episode', {}).get('runtime', 0)) * 60
        item.infolabels['plot'] = item.infolabels.get('plot') or i.get('episode', {}).get('overview')
        item.infolabels['mpaa'] = item.infolabels.get('mpaa') or i.get('show', {}).get('certification')

        return item

    def get_calendar_episodes(self, startdate=0, days=1, limit=25):
        items = []

        if not self.tmdb or not self.authorize():
            return items

        date = datetime.date.today() + datetime.timedelta(days=startdate)
        response = self.get_calendar('shows', True, start_date=date.strftime('%Y-%m-%d'), days=days)

        if not response:
            return items

        for i in response[-limit:]:
            episode = i.get('episode', {}).get('number')
            season = i.get('episode', {}).get('season')
            tmdb_id = i.get('show', {}).get('ids', {}).get('tmdb')
            item = ListItem(library=self.library, **self.tmdb.get_detailed_item(
                itemtype='tv', tmdb_id=tmdb_id, season=season, episode=episode))
            item.tmdb_id, item.season, item.episode = tmdb_id, season, episode
            item = self.get_calendar_properties(item, i)
            items.append(item)
        return items

    def get_upnext_cache_refresh(self, show_id, last_updated):
        if not last_updated:  # No last Trakt update date so refresh cache
            # utils.kodi_log(u'Up Next {} Episodes:\nNo last Trakt update date. Refreshing cache...'.format(show_id), 1)
            return True  # Refresh cache

        cache_name = '{0}.trakt.show.{1}.last_updated'.format(self.cache_name, show_id)
        prev_updated = self.get_cache(cache_name)
        if not prev_updated:  # No previous update date so refresh cache
            # utils.kodi_log(u'Up Next {} Episodes:\nNo previous update date. Refreshing cache...'.format(show_id), 1)
            return self.set_cache(last_updated, cache_name)  # Set the cache date and refresh cache

        if utils.convert_timestamp(prev_updated) < utils.convert_timestamp(last_updated):  # Changes on Trakt since previous update date so refresh cache
            # utils.kodi_log(u'Up Next {} Episodes:\nChanges on Trakt since previous update date. Refreshing cache...'.format(show_id), 1)
            return self.set_cache(last_updated, cache_name)  # Set the cache date and refresh cache
        # utils.kodi_log(u'Up Next {} Episodes:\nRetrieving cached details...'.format(show_id), 1)

    def get_upnext(self, show_id, response_only=False, last_updated=None):
        items = []
        if not self.authorize():
            return items

        cache_refresh = self.get_upnext_cache_refresh(show_id, last_updated)

        request = 'shows/{0}/progress/watched'.format(show_id)
        response = self.get_request(request, cache_refresh=cache_refresh, cache_days=1)
        reset_at = utils.convert_timestamp(response.get('reset_at')) if response.get('reset_at') else None
        seasons = response.get('seasons', [])
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
                        # utils.kodi_log(u'Up Next {} Episodes:\nFound next episode - S{}E{}'.format(show_id, s_num, e_num), 1)
                        return response
                    items.append(item)
        if not response_only:
            return items if items else [(1, 1)]

    def get_upnext_episodes(self, tmdb_id=None, imdb_id=None, limit=10):
        if not self.tmdb or not self.authorize() or not tmdb_id:
            return []

        if not imdb_id:
            imdb_id = self.tmdb.get_item_externalid(itemtype='tv', tmdb_id=tmdb_id, external_id='imdb_id')

        return [ListItem(library=self.library, **self.tmdb.get_detailed_item(
            itemtype='tv', tmdb_id=tmdb_id, season=i[0], episode=i[1])) for i in self.get_upnext(imdb_id)[:limit]]

    def get_unwatched_progress(self, tmdb_id=None, imdb_id=None, check_sync=True):
        if not self.tmdb or not self.authorize() or not tmdb_id:
            return
        if not imdb_id:
            imdb_id = self.tmdb.get_item_externalid(itemtype='tv', tmdb_id=utils.try_parse_int(tmdb_id), external_id='imdb_id')
        if not imdb_id:
            return
        cache_refresh = False if not check_sync or self.sync_activities('shows', 'watched_at') else True
        return self.get_request_lc('shows', imdb_id, 'progress', 'watched', cache_refresh=cache_refresh)

    def get_unwatched_count(self, tmdb_id=None, imdb_id=None, season=None, request=None, check_sync=True, only_inprogress=True):
        if not tmdb_id and not imdb_id and not request:
            return -1

        request = request or self.get_unwatched_progress(tmdb_id=tmdb_id, imdb_id=imdb_id, check_sync=check_sync)

        if not request:
            return -1

        request = utils.get_dict_in_list(request.get('seasons', []), 'number', utils.try_parse_int(season)) if season else request

        if not request or not request.get('aired'):
            return -1

        if not utils.try_parse_int(request.get('completed', 0)):
            return -1

        return utils.try_parse_int(request.get('aired')) - utils.try_parse_int(request.get('completed', 0))

    def get_usernameslug(self, login=False):
        if not self.authorize(login):
            return
        item = self.get_response_json('users/settings')
        user_slug = item.get('user', {}).get('ids', {}).get('slug')
        if user_slug:
            xbmcgui.Window(10000).setProperty('TMDbHelper.TraktUserSlug', user_slug)  # Set a Window Property to Compare
            return user_slug

    def get_details(self, item_type, id_num, season=None, episode=None):
        if not season or not episode:
            return self.get_response_json(item_type + 's', id_num, extended='full')
        return self.get_response_json(item_type + 's', id_num, 'seasons', season, 'episodes', episode, extended='full')

    def get_traktslug(self, item_type, id_type, id_num):
        items = self.get_response_json('search', id_type, id_num, type=item_type)
        for i in items:
            if str(i.get(item_type, {}).get('ids', {}).get(id_type)) == str(id_num):
                return i.get(item_type, {}).get('ids', {}).get('slug')

    def get_collection(self, tmdbtype, page=1, limit=20):
        items = []
        if not self.tmdb or not self.authorize():
            return items
        collection = self.sync_collection(utils.type_convert(tmdbtype, 'trakt'))
        collection = sorted(collection, key=lambda i: i[utils.type_convert(tmdbtype, 'trakt')]['title'], reverse=False)
        start_at = limit * (page - 1)
        end_at = start_at + limit
        for i in collection[start_at:end_at]:
            i = i.get(utils.type_convert(tmdbtype, 'trakt'))
            i_tmdb = i.get('ids', {}).get('tmdb', '')
            item = ListItem(library=self.library, **self.tmdb.get_detailed_item(tmdbtype, i_tmdb))
            if item and item.label != 'N/A':
                items.append(item)
        if items and collection[end_at:]:  # If there's more items add the next page item
            items.append(ListItem(library=self.library, label=xbmc.getLocalizedString(33078), nextpage=page + 1))
        return items

    def get_item_idlookup(self, item_type, tmdb_id=None, tvdb_id=None, imdb_id=None):
        if not tmdb_id and not tvdb_id and not imdb_id:
            return
        item = None
        if tmdb_id:
            item = self.get_request('search', 'tmdb', tmdb_id, type=item_type)
        if not item and tvdb_id:
            item = self.get_request('search', 'tvdb', tvdb_id, type=item_type)
        if not item and imdb_id:
            item = self.get_request('search', 'imdb', imdb_id, type=item_type)
        if not item:
            return
        for i in item:
            if i.get('type') == item_type:
                return i.get(item_type)

    def create_userlist(self, user_slug=None, list_name=None, login=True):
        if not self.authorize(login):  # Method needs authorisation
            utils.kodi_log('TRAKT CREATE USERLIST - User not authorized')
            return
        user_slug = user_slug or self.get_usernameslug()
        if not user_slug:
            utils.kodi_log('TRAKT CREATE USERLIST - Unable to retrieve user_slug')
            return
        list_name = list_name or xbmcgui.Dialog().input('Enter List Name')
        if not list_name:
            utils.kodi_log('TRAKT CREATE USERLIST - No list name entered')
            return
        user_list = self.get_api_request('{}/users/{}/lists'.format(self.req_api_url, user_slug), headers=self.headers, postdata=dumps({"name": list_name}))
        if user_list:
            return user_list.get('ids', {}).get('slug')

    def sync_userlist(self, item_type, tmdb_id=None, tvdb_id=None, imdb_id=None, login=True, remove_item=False, user_list=None):
        utils.kodi_log('Adding {} {} {} {} to User List'.format(item_type, tmdb_id, tvdb_id, imdb_id))
        if not self.authorize(login):  # Method needs authorisation
            return

        user_slug = self.get_usernameslug()  # Get the user's slug
        if not user_slug:
            utils.kodi_log('TRAKT SYNC LIST - Failed to retrieve user_slug')
            return

        item = self.get_item_idlookup(item_type, tmdb_id=tmdb_id, tvdb_id=tvdb_id, imdb_id=imdb_id)  # Lookup item
        if not item:
            utils.kodi_log('TRAKT SYNC LIST - Failed to retrieve item details')
            return

        if not user_list:
            user_lists = self.get_response_json('users', user_slug, 'lists')  # Get the user's lists
            user_list_labels = [i.get('name') for i in user_lists]  # Build select dialog to choose list
            user_list_labels.append(self.addon.getLocalizedString(32141)) if not remove_item else None  # Add create new list item
            addremove = xbmc.getLocalizedString(1210) if remove_item else xbmc.getLocalizedString(15019)
            user_choice = xbmcgui.Dialog().select("{} {}".format(addremove, item.get('title')), user_list_labels)  # Choose the list
            if user_choice == -1:  # User cancelled
                utils.kodi_log('TRAKT SYNC LIST - User Cancelled')
                return
            if user_list_labels[user_choice] == self.addon.getLocalizedString(32141):
                user_list = self.create_userlist(user_slug)
            else:
                user_list = user_lists[user_choice].get('ids', {}).get('slug')
            if not user_list:
                utils.kodi_log('TRAKT SYNC LIST - Failed to retrieve list_slug')
                return

        items = {item_type + 's': [item]}  # Create postdata for adding item
        url = '{}/users/{}/lists/{}/items'.format(self.req_api_url, user_slug, user_list)
        url += '/remove' if remove_item else ''
        msg_head = self.addon.getLocalizedString(32139) if remove_item else self.addon.getLocalizedString(32140)
        if self.get_api_request(url, headers=self.headers, postdata=dumps(items)):
            msg_body = self.addon.getLocalizedString(32135) if remove_item else self.addon.getLocalizedString(32136)
            msg_body = msg_body.format(item_type, item.get('title'), user_list)
            utils.kodi_log('TRAKT SYNC LIST - ' + msg_body)
            xbmcgui.Dialog().ok(msg_head, msg_body)  # Notify user that item added/removed successfully
            return item
        msg_body = self.addon.getLocalizedString(32137) if remove_item else self.addon.getLocalizedString(32138)
        msg_body = msg_body.format(item_type, item.get('title'), user_list)
        utils.kodi_log('TRAKT SYNC LIST - ' + msg_body)
        xbmcgui.Dialog().ok(msg_head, msg_body)  # Notify user that we failed to add/remove item

    def sync_activities(self, itemtype, listtype):
        """ Checks if itemtype.listtype has been updated since last check """
        if not self.authorize():
            return
        cache_name = '{0}.trakt.last_activities_v2'.format(self.cache_name)
        self.prev_activities = self.get_cache(cache_name)
        self.last_activities = self.get_response_json('sync/last_activities')
        if not self.last_activities:
            return  # No last activities so refresh item cache
        if not self.prev_activities:
            self.set_cache(self.last_activities, cache_name=cache_name, cache_days=self.cache_long)
            return  # No prev activities so refresh item cache and save last activities as prev activities
        if not self.prev_activities.get(itemtype, {}).get(listtype) or not self.last_activities.get(itemtype, {}).get(listtype):
            return  # No activity recorded for that listtype/itemtype combo so refresh item cache
        if self.prev_activities.get(itemtype, {}).get(listtype) != self.last_activities.get(itemtype, {}).get(listtype):
            self.prev_activities[itemtype][listtype] = self.last_activities.get(itemtype, {}).get(listtype)
            self.set_cache(self.prev_activities, cache_name=cache_name, cache_days=self.cache_long)
            return  # Dates didnt match so refresh item cache and update prev activities with new date
        return self.last_activities.get(itemtype, {}).get(listtype)  # No updates since last time so dont refresh item cache

    def sync_collection(self, itemtype, idtype=None, mode=None, items=None, cache_refresh=False):
        return self.get_sync('collection', 'collected_at', itemtype, idtype, mode, items, cache_refresh)

    def sync_watchlist(self, itemtype, idtype=None, mode=None, items=None, cache_refresh=False):
        return self.get_sync('watchlist', 'watchlisted_at', itemtype, idtype, mode, items, cache_refresh)

    def sync_history(self, itemtype, idtype=None, mode=None, items=None, cache_refresh=False):
        return self.get_sync('history', 'watched_at', itemtype, idtype, mode, items, cache_refresh)

    def get_watched(self, itemtype, idtype=None):
        return self.get_sync('watched', 'watched_at', itemtype, idtype)

    def get_sync(self, name, activity, itemtype, idtype=None, mode=None, items=None, cache_refresh=False):
        if not self.authorize():
            return {}
        if mode == 'add' or mode == 'remove':
            name = name + '/remove' if mode == 'remove' else name
            return self.get_api_request('{0}/sync/{1}'.format(self.req_api_url, name), headers=self.headers, postdata=dumps(items))
        if not self.sync.get(name):
            if not cache_refresh:
                cache_refresh = False if self.sync_activities(itemtype + 's', activity) else True
            self.sync[name] = self.get_request_lc('sync', name, itemtype + 's', cache_refresh=cache_refresh)
        if not self.sync.get(name):
            return {}
        if idtype:
            return {i.get(itemtype, {}).get('ids', {}).get(idtype) for i in self.sync.get(name) if i.get(itemtype, {}).get('ids', {}).get(idtype)}
        return self.sync.get(name)
