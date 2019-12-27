from json import loads, dumps
import resources.lib.utils as utils
from resources.lib.requestapi import RequestAPI
from resources.lib.listitem import ListItem
import time
import xbmc
import random
import xbmcgui
import datetime


class traktAPI(RequestAPI):
    def __init__(self, force=False, cache_short=None, cache_long=None, tmdb=None, login=False):
        super(traktAPI, self).__init__(
            cache_short=cache_short, cache_long=cache_long,
            req_api_url='https://api.trakt.tv/', req_api_name='Trakt')
        self.authorization = ''
        self.sync = {}
        self.last_activities = None
        self.prev_activities = None
        self.refreshcheck = 0
        self.attempedlogin = False
        self.dialog_noapikey_header = '{0} {1} {2}'.format(self.addon.getLocalizedString(32007), self.req_api_name, self.addon.getLocalizedString(32011))
        self.dialog_noapikey_text = self.addon.getLocalizedString(32012)
        self.client_id = 'e6fde6173adf3c6af8fd1b0694b9b84d7c519cefc24482310e1de06c6abe5467'
        self.client_secret = '15119384341d9a61c751d8d515acbc0dd801001d4ebe85d3eef9885df80ee4d9'
        self.headers = {'trakt-api-version': '2', 'trakt-api-key': self.client_id, 'Content-Type': 'application/json'}
        self.tmdb = tmdb
        self.library = 'video'
        self.utc_offset = -time.timezone // 3600
        self.utc_offset += 1 if time.localtime().tm_isdst > 0 else 0

        if force:
            self.login()
            return

        self.authorize(login)

    def authorize(self, login=False):
        if self.authorization:
            return self.authorization
        token = self.addon.getSetting('trakt_token')
        token = loads(token) if token else None
        if token and type(token) is dict and token.get('access_token'):
            self.authorization = token
            self.headers['Authorization'] = 'Bearer {0}'.format(self.authorization.get('access_token'))
        elif login:
            if not self.attempedlogin and xbmcgui.Dialog().yesno(self.dialog_noapikey_header, self.dialog_noapikey_text, '', '', 'Cancel', 'OK'):
                self.login()
            self.attempedlogin = True
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
            'Trakt Authentication',
            'Go to [B]https://trakt.tv/activate[/B]',
            'Enter the code: [B]' + self.code.get('user_code') + '[/B]')
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
        utils.kodi_log('Trakt Authentication Aborted!', 1)
        self.auth_dialog.close()

    def on_expired(self):
        """Triggered when the device authentication code has expired"""
        utils.kodi_log('Trakt Authentication Expired!', 1)
        self.auth_dialog.close()

    def on_authenticated(self, auth_dialog=True):
        """Triggered when device authentication has been completed"""
        utils.kodi_log('Trakt Authenticated Successfully!', 1)
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

    def get_itemlist(self, *args, **kwargs):
        items = []

        if not self.tmdb or (kwargs.pop('req_auth', False) and not self.authorize()):
            return items

        key_list = kwargs.pop('key_list', ['dummy'])
        rnd_list = kwargs.pop('rnd_list', 0)
        response = self.get_response(*args, **kwargs)

        if not response:
            return items

        itemlist = response.json()

        this_page = int(kwargs.get('page', 1))
        last_page = int(response.headers.get('X-Pagination-Page-Count', 0))
        next_page = this_page + 1 if this_page < last_page and not rnd_list else False

        if rnd_list:
            rnd_list = random.sample(range(len(itemlist) - 1), rnd_list)
            itemlist = [itemlist[i] for i in rnd_list]

        n = 0
        limit = kwargs.get('limit', 0)
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
            items.append(ListItem(library=self.library, label='Next Page', nextpage=next_page))

        return items

    def get_limitedlist(self, itemlist, tmdbtype, limit, islistitem):
        items = []
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
            if islistitem:
                item = ListItem(library=self.library, **self.tmdb.get_detailed_item(tmdbtype, item[1]))
            if item not in items:
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
        infoproperties['trakt_rating'] = '{:0.1f}'.format(response.get('rating', ''))
        infoproperties['trakt_votes'] = '{0}'.format(response.get('votes', ''))
        return infoproperties

    def get_mostwatched(self, userslug, tmdbtype, limit=None, islistitem=True):
        history = self.get_response_json('users', userslug, 'watched', utils.type_convert(tmdbtype, 'trakt') + 's')
        history = sorted(history, key=lambda i: i['plays'], reverse=True)
        return self.get_limitedlist(history, tmdbtype, limit, islistitem)

    def get_recentlywatched(self, userslug, tmdbtype, limit=None, islistitem=True):
        start_at = datetime.date.today() - datetime.timedelta(6 * 365 / 12)
        history = self.get_response_json('users', userslug, 'history', utils.type_convert(tmdbtype, 'trakt') + 's', page=1, limit=200, start_at=start_at.strftime("%Y-%m-%d"))
        return self.get_limitedlist(history, tmdbtype, limit, islistitem)

    def get_inprogress(self, userslug, limit=None):
        """
        Looks at user's most recently watched 200 episodes in last 6 months
        Adds each unique show to list in order then checks if show has an upnext episode
        Returns list of tmdb_ids representing shows with upnext episodes in recently watched order
        """
        items = []
        if not self.tmdb or not self.authorize():
            return items

        n = 0
        for i in self.get_recentlywatched(userslug, 'tv', islistitem=False):
            if limit and n >= limit:
                break
            progress = self.get_upnext(i[0], True)
            if progress and progress.get('next_episode'):
                items.append(ListItem(library=self.library, **self.tmdb.get_detailed_item('tv', i[1])))
                n += 1
        return items

    def get_calendar(self, tmdbtype, user=True, start_date=None, days=None):
        user = 'my' if user else 'all'
        return self.get_response_json('calendars', user, tmdbtype, start_date, days)

    def get_calendar_episodes(self, startdate=0, days=1, limit=25):
        items = []

        if not self.tmdb or not self.authorize():
            return items

        date = datetime.datetime.today() + datetime.timedelta(days=startdate)
        response = traktAPI().get_calendar('shows', True, start_date=date.strftime('%Y-%m-%d'), days=days)

        for i in response[-limit:]:
            episode = i.get('episode', {}).get('number')
            season = i.get('episode', {}).get('season')
            tmdb_id = i.get('show', {}).get('ids', {}).get('tmdb')
            item = ListItem(library=self.library, **self.tmdb.get_detailed_item(
                itemtype='tv', tmdb_id=tmdb_id, season=season, episode=episode))
            item.tmdb_id, item.season, item.episode = tmdb_id, season, episode
            item.infolabels['title'] = item.label = i.get('episode', {}).get('title')
            air_date = utils.convert_timestamp(i.get('first_aired', '')) + datetime.timedelta(hours=self.utc_offset)
            item.infolabels['premiered'] = air_date.strftime('%Y-%m-%d')
            item.infolabels['year'] = air_date.strftime('%Y')
            item.infoproperties['air_time'] = air_date.strftime('%I:%M %p')
            items.append(item)
        return items

    def get_upnext(self, show_id, response_only=False):
        items = []
        if not self.authorize():
            return items
        request = 'shows/{0}/progress/watched'.format(show_id)
        response = self.get_response_json(request)
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

    def get_unwatched_count(self, tmdb_id=None, imdb_id=None, season=None, request=None, check_sync=True):
        if not tmdb_id and not imdb_id and not request:
            return -1

        request = request or self.get_unwatched_progress(tmdb_id=tmdb_id, imdb_id=imdb_id, check_sync=check_sync)
        request = utils.get_dict_in_list(request.get('seasons', []), 'number', utils.try_parse_int(season)) if season else request

        if not request or not request.get('aired'):
            return -1

        return utils.try_parse_int(request.get('aired')) - utils.try_parse_int(request.get('completed', 0))

    def get_usernameslug(self, login=False):
        if not self.authorize(login):
            return
        item = self.get_response_json('users/settings')
        return item.get('user', {}).get('ids', {}).get('slug')

    def get_details(self, item_type, id_num, season=None, episode=None):
        if not season or not episode:
            return self.get_response_json(item_type + 's', id_num)
        return self.get_response_json(item_type + 's', id_num, 'seasons', season, 'episodes', episode)

    def get_traktslug(self, item_type, id_type, id_num):
        item = self.get_response_json('search', id_type, id_num, '?' + item_type)
        return item[0].get(item_type, {}).get('ids', {}).get('slug')

    def sync_activities(self, itemtype, listtype):
        """ Checks if itemtype.listtype has been updated since last check """
        if not self.authorize():
            return
        cache_name = '{0}.trakt.last_activities'.format(self.cache_name)
        if not self.prev_activities:
            self.prev_activities = self.get_cache(cache_name)
        if not self.last_activities:
            self.last_activities = self.set_cache(self.get_response_json('sync/last_activities'), cache_name=cache_name, cache_days=self.cache_long)
        if not self.prev_activities or not self.last_activities:
            return
        if self.prev_activities.get(itemtype, {}).get(listtype) == self.last_activities.get(itemtype, {}).get(listtype):
            return self.last_activities.get(itemtype, {}).get(listtype)

    def sync_collection(self, itemtype, idtype=None, mode=None, items=None):
        return self.get_sync('collection', 'collected_at', itemtype, idtype, mode, items)

    def sync_watchlist(self, itemtype, idtype=None, mode=None, items=None):
        return self.get_sync('watchlist', 'watchlisted_at', itemtype, idtype, mode, items)

    def sync_history(self, itemtype, idtype=None, mode=None, items=None):
        return self.get_sync('history', 'watched_at', itemtype, idtype, mode, items)

    def get_watched(self, itemtype, idtype=None):
        return self.get_sync('watched', 'watched_at', itemtype, idtype, None, None)

    def get_sync(self, name, activity, itemtype, idtype=None, mode=None, items=None):
        if not self.authorize():
            return
        if mode == 'add' or mode == 'remove':
            name = name + '/remove' if mode == 'remove' else name
            return self.get_api_request('{0}/sync/{1}'.format(self.req_api_url, name), headers=self.headers, postdata=dumps(items))
        if not self.sync.get(name):
            cache_refresh = False if self.sync_activities(itemtype + 's', activity) else True
            self.sync[name] = self.get_request_lc('sync/', name, itemtype + 's', cache_refresh=cache_refresh)
        if not self.sync.get(name):
            return
        if idtype:
            return {i.get(itemtype, {}).get('ids', {}).get(idtype) for i in self.sync.get(name) if i.get(itemtype, {}).get('ids', {}).get(idtype)}
        return self.sync.get(name)
