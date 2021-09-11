import xbmcgui
from resources.lib.addon.cache import CACHE_SHORT, CACHE_LONG
from resources.lib.tmdb.mapping import ItemMapper, get_episode_to_air
from resources.lib.api.request import RequestAPI
from resources.lib.addon.plugin import ADDON, get_mpaa_prefix, get_language, convert_type, ADDONPATH
from resources.lib.files.downloader import Downloader
from resources.lib.container.listitem import ListItem
from resources.lib.addon.constants import TMDB_ALL_ITEMS_LISTS, TMDB_PARAMS_SEASONS, TMDB_PARAMS_EPISODES
from resources.lib.addon.parser import try_int
from resources.lib.files.utils import use_pickle
from resources.lib.addon.constants import TMDB_GENRE_IDS
from resources.lib.addon.window import get_property
from resources.lib.addon.timedate import get_datetime_now, get_timedelta
from json import loads


API_URL = 'https://api.themoviedb.org/3'
APPEND_TO_RESPONSE = 'credits,release_dates,content_ratings,external_ids,movie_credits,tv_credits,keywords,reviews,videos,watch/providers'


class TMDb(RequestAPI):
    def __init__(
            self,
            api_key='a07324c669cac4d96789197134ce272b',
            language=get_language(),
            mpaa_prefix=get_mpaa_prefix()):
        super(TMDb, self).__init__(
            req_api_name='TMDb',
            req_api_url=API_URL,
            req_api_key=u'api_key={}'.format(api_key))
        self.language = language
        self.iso_language = language[:2]
        self.iso_country = language[-2:]
        self.req_language = u'{0}-{1}&include_image_language={0},null'.format(self.iso_language, self.iso_country)
        self.mpaa_prefix = mpaa_prefix
        self.append_to_response = APPEND_TO_RESPONSE
        self.req_strip += [(self.append_to_response, ''), (self.req_language, self.iso_language)]
        self.mapper = ItemMapper(self.language, self.mpaa_prefix)

    def get_url_separator(self, separator=None):
        if separator == 'AND':
            return '%2C'
        elif separator == 'OR':
            return '%7C'
        elif not separator:
            return '%2C'
        else:
            return False

    def get_tmdb_id(self, tmdb_type=None, imdb_id=None, tvdb_id=None, query=None, year=None, episode_year=None, raw_data=False, **kwargs):
        if not tmdb_type:
            return
        kwargs['cache_days'] = CACHE_SHORT
        kwargs['cache_name'] = 'TMDb.get_tmdb_id.v2'
        kwargs['cache_combine_name'] = True
        return self._cache.use_cache(
            self._get_tmdb_id, tmdb_type=tmdb_type, imdb_id=imdb_id, tvdb_id=tvdb_id, query=query, year=year,
            episode_year=episode_year, raw_data=raw_data, **kwargs)

    def _get_tmdb_id(self, tmdb_type, imdb_id, tvdb_id, query, year, episode_year, raw_data, **kwargs):
        func = self.get_request_sc
        if not tmdb_type:
            return
        request = None
        if tmdb_type == 'genre' and query:
            return TMDB_GENRE_IDS.get(query, '')
        elif imdb_id:
            request = func('find', imdb_id, language=self.req_language, external_source='imdb_id')
            request = request.get(u'{0}_results'.format(tmdb_type), [])
        elif tvdb_id:
            request = func('find', tvdb_id, language=self.req_language, external_source='tvdb_id')
            request = request.get(u'{0}_results'.format(tmdb_type), [])
        elif query:
            query = query.split(' (', 1)[0]  # Scrub added (Year) or other cruft in parentheses () added by Addons or TVDb
            if tmdb_type == 'tv':
                request = func('search', tmdb_type, language=self.req_language, query=query, first_air_date_year=year)
            else:
                request = func('search', tmdb_type, language=self.req_language, query=query, year=year)
            request = request.get('results', [])
        if not request:
            return
        if raw_data:
            return request
        if tmdb_type == 'tv' and episode_year and len(request) > 1:
            for i in sorted(request, key=lambda k: k.get('first_air_date', ''), reverse=True):
                if not i.get('first_air_date'):
                    continue
                if try_int(i.get('first_air_date', '9999')[:4]) <= try_int(episode_year):
                    if query in [i.get('name'), i.get('original_name')]:
                        return i.get('id')
        return request[0].get('id')

    def get_tmdb_id_from_query(self, tmdb_type, query, header=None, use_details=False, get_listitem=False, auto_single=False):
        if not query or not tmdb_type:
            return
        response = self.get_tmdb_id(tmdb_type, query=query, raw_data=True)
        items = [ListItem(**self.mapper.get_info(i, tmdb_type)).get_listitem() for i in response]
        if not items:
            return
        x = 0
        if not auto_single or len(items) != 1:
            x = xbmcgui.Dialog().select(header, items, useDetails=use_details)
        if x != -1:
            return items[x] if get_listitem else items[x].getUniqueID('tmdb')

    def get_translated_list(self, items, tmdb_type=None, separator=None):
        """
        If tmdb_type specified will look-up IDs using search function otherwise assumes item ID is passed
        """
        separator = self.get_url_separator(separator)
        temp_list = ''
        for item in items:
            item_id = self.get_tmdb_id(tmdb_type=tmdb_type, query=item) if tmdb_type else item
            if not item_id:
                continue
            if separator:  # If we've got a url separator then concatinate the list with it
                temp_list = u'{}{}{}'.format(temp_list, separator, item_id) if temp_list else item_id
            else:  # If no separator, assume that we just want to use the first found ID
                temp_list = str(item_id)
                break  # Stop once we have a item
        temp_list = temp_list if temp_list else 'null'
        return temp_list

    def get_tvshow_nextaired(self, tmdb_id):
        """ Get updated next aired data for tvshows using 24hr cache """
        return self._cache.use_cache(
            self._get_tvshow_nextaired, tmdb_id,
            cache_name=u'TMDb.get_tvshow_nextaired.{}'.format(tmdb_id),
            cache_days=CACHE_SHORT)

    def _get_tvshow_nextaired(self, tmdb_id):
        if not tmdb_id:
            return {}
        response = self.get_response_json('tv', tmdb_id, language=self.req_language)
        if not response:
            return {}
        infoproperties = {}
        if response.get('next_episode_to_air'):
            infoproperties.update(get_episode_to_air(response['next_episode_to_air'], 'next_aired'))
        if response.get('last_episode_to_air'):
            infoproperties.update(get_episode_to_air(response['last_episode_to_air'], 'last_aired'))
        return {'infoproperties': infoproperties}

    def _get_details_request(self, tmdb_type, tmdb_id, season=None, episode=None):
        path_affix = []
        if season is not None:
            path_affix += ['season', season]
        if season is not None and episode is not None:
            path_affix += ['episode', episode]
        return self.get_response_json(
            tmdb_type, tmdb_id, *path_affix, append_to_response=self.append_to_response) or {}

    def get_details(self, tmdb_type, tmdb_id, season=None, episode=None, **kwargs):
        kwargs['cache_days'] = CACHE_LONG
        kwargs['cache_name'] = 'TMDb.get_details.v7.{}'.format(self.language)
        kwargs['cache_combine_name'] = True
        return self._cache.use_cache(self._get_details, tmdb_type, tmdb_id, season, episode, **kwargs)

    def _get_details(self, tmdb_type, tmdb_id, season, episode, **kwargs):
        if not tmdb_id or not tmdb_type:
            return

        # Get base item
        info_item = self._get_details_request(tmdb_type, tmdb_id)
        base_item = self.mapper.get_info(info_item, tmdb_type)

        if tmdb_type != 'tv' or season is None:
            return base_item

        # If we're getting season/episode details we need to add them to the base tv details
        child_type = 'episode' if episode else 'season'
        child_info = self._get_details_request(tmdb_type, tmdb_id, season, episode)
        return self.mapper.get_info(child_info, child_type, base_item, tmdb_id=tmdb_id)

    def _get_upnext_season_item(self, base_item):
        base_item['params']['info'] = 'trakt_upnext'
        base_item['infolabels']['mediatype'] = 'season'
        base_item['label'] = base_item['infolabels']['title'] = ADDON.getLocalizedString(32043)
        return [base_item]

    def get_flatseasons_list(self, tmdb_id):
        request = self.get_request_sc(u'tv/{}'.format(tmdb_id))
        if not request or not request.get('seasons'):
            return []
        return [
            j for i in request['seasons'] for j in self.get_episode_list(tmdb_id, i['season_number'])
            if i.get('season_number')]

    def get_episode_group_episodes_list(self, tmdb_id, group_id, position):
        request = self.get_request_sc(u'tv/episode_group/{}'.format(group_id))
        if not request or not request.get('groups'):
            return []
        base_item = self.get_details('tv', tmdb_id)
        eps_group = request.get('groups', [])[try_int(position)] or {}
        return [
            self.mapper.get_info(i, 'episode', base_item, definition=TMDB_PARAMS_EPISODES, tmdb_id=tmdb_id)
            for i in eps_group.get('episodes', [])]

    def get_episode_group_seasons_list(self, tmdb_id, group_id):
        request = self.get_request_sc(u'tv/episode_group/{}'.format(group_id))
        if not request or not request.get('groups'):
            return []
        base_item = self.get_details('tv', tmdb_id)
        items = [
            self.mapper.get_info(i, 'season', base_item, tmdb_id=tmdb_id, definition={
                'info': 'episode_group_episodes', 'tmdb_type': 'tv', 'tmdb_id': tmdb_id, 'group_id': group_id, 'position': str(x)})
            for x, i in enumerate(request.get('groups', []))]
        return items

    def get_episode_groups_list(self, tmdb_id):
        request = self.get_request_sc(u'tv/{}/episode_groups'.format(tmdb_id))
        if not request or not request.get('results'):
            return []
        base_item = self.get_details('tv', tmdb_id)
        items = [
            self.mapper.get_info(i, 'tv', base_item, tmdb_id=tmdb_id, definition={
                'info': 'episode_group_seasons', 'tmdb_type': 'tv', 'tmdb_id': tmdb_id, 'group_id': '{id}'})
            for i in request.get('results', [])]
        return items

    def _get_videos(self, tmdb_id, tmdb_type, season=None, episode=None):
        path = u'{}/{}'.format(tmdb_type, tmdb_id)
        if season is not None:
            path = u'{}/season/{}'.format(path, season)
        if episode is not None:
            path = u'{}/episode/{}'.format(path, episode)
        request = self.get_request_sc(u'{}/videos'.format(path)) or {}
        return request.get('results') or []

    def get_videos(self, tmdb_id, tmdb_type, season=None, episode=None):
        results = self._get_videos(tmdb_id, tmdb_type, season, episode)
        if episode is not None:  # Also get season videos
            results = results + self._get_videos(tmdb_id, tmdb_type, season)
        if season is not None:  # Also get base show videos
            results = results + self._get_videos(tmdb_id, tmdb_type)
        if not results:
            return []

        # Grab base item details and pop any details that aren't relevant to the video
        base_item = self.get_details(tmdb_type, tmdb_id, season, episode)
        base_item['infolabels'].pop('duration', None)
        base_item['infolabels'].pop('season', None)
        base_item['infolabels'].pop('episode', None)

        # Only list YouTube videos because Kodi install might not have browser and needs to play via plugin
        # Not sure if TMDb provides videos from other sites anymore but check just in case
        items = []
        for i in results:
            if i.get('site') != 'YouTube' or not i.get('key'):
                continue
            item = self.mapper.get_info(i, 'video', base_item, tmdb_id=tmdb_id)
            item['art']['thumb'] = 'https://img.youtube.com/vi/{}/0.jpg'.format(i['key'])
            item['path'] = u'plugin://plugin.video.youtube/play/?video_id={}'.format(i['key'])
            item['is_folder'] = False
            items.append(item)
        return items

    def get_season_list(self, tmdb_id, special_folders=0):
        """
        special_folders: int binary to hide:
        001 (1) = Hide Specials, 010 (2) = Hide Up Next, 100 (4) = Hide Groups
        """
        request = self.get_request_sc(u'tv/{}'.format(tmdb_id))
        if not request:
            return []
        base_item = self.mapper.get_info(request, 'tv')
        items, items_end = [], []
        for i in request.get('seasons', []):
            item = self.mapper.get_info(i, 'season', base_item, definition=TMDB_PARAMS_SEASONS, tmdb_id=tmdb_id)
            # TODO: Fix play all
            # Might be issue with resolving to dummy file that resets playlist to 1
            # item['context_menu'] += [(
            #     xbmc.getLocalizedString(22083),
            #     'RunScript(plugin.video.themoviedb.helper,play_season={},tmdb_id={})'.format(
            #         item['infolabels']['season'], tmdb_id))]
            if i.get('season_number') != 0:
                items.append(item)
            elif ((special_folders >> 0) & 1) == 0:  # on bit in 0 pos hides specials
                items_end.append(item)

        # Episode Groups
        if ((special_folders >> 2) & 1) == 0:  # on bit in 2 pos hides episode groups
            egroups = self.get_request_sc(u'tv/{}/episode_groups'.format(tmdb_id))
            if egroups and egroups.get('results'):
                egroup_item = self.mapper.get_info({
                    'title': ADDON.getLocalizedString(32345)}, 'season', base_item, tmdb_id=tmdb_id, definition={
                        'info': 'episode_groups', 'tmdb_type': 'tv', 'tmdb_id': tmdb_id})
                egroup_item['art']['thumb'] = egroup_item['art']['poster'] = u'{}/resources/icons/trakt/groupings.png'.format(ADDONPATH)
                items_end.append(egroup_item)

        # Up Next
        if ((special_folders >> 1) & 1) == 0:  # on bit in 1 pos hides up next
            if get_property('TraktIsAuth') == 'True':
                upnext_item = self.mapper.get_info({
                    'title': ADDON.getLocalizedString(32043)}, 'season', base_item, tmdb_id=tmdb_id, definition={
                        'info': 'trakt_upnext', 'tmdb_type': 'tv', 'tmdb_id': tmdb_id})
                upnext_item['art']['thumb'] = upnext_item['art']['poster'] = u'{}/resources/icons/trakt/up-next.png'.format(ADDONPATH)
                items_end.append(upnext_item)
        return items + items_end

    def get_episode_list(self, tmdb_id, season):
        request = self.get_request_sc(u'tv/{}/season/{}'.format(tmdb_id, season))
        if not request:
            return []
        base_item = self.get_details('tv', tmdb_id)
        return [
            self.mapper.get_info(i, 'episode', base_item, definition=TMDB_PARAMS_EPISODES, tmdb_id=tmdb_id)
            for i in request.get('episodes', [])]

    def get_cast_list(self, tmdb_id, tmdb_type, season=None, episode=None, keys=['cast', 'guest_stars']):
        items = []
        if season is not None and episode is not None:
            affix = u'season/{}/episode/{}'.format(season, episode)
        elif season is not None:
            affix = u'season/{}'.format(season)
        else:
            affix = None
        response = self.get_request_lc(tmdb_type, tmdb_id, affix, 'credits')
        if not response:
            return []

        # Join guest stars list etc
        cast_list = []
        for key in keys:
            cast_list += response.get(key) or []

        # Add items
        item_ids = []
        for i in sorted(cast_list, key=lambda k: k.get('order', 1000)):
            if not i.get('id'):
                continue
            # Avoid re-adding people that have multiple roles listed
            if i['id'] not in item_ids:
                item_ids.append(i['id'])
                items.append(self.mapper.get_info(i, 'person'))
                continue
            # Instead merge their roles back into the original entry
            x = item_ids.index(i['id'])
            p = items[x].get('infoproperties', {})
            for k, v in self.mapper.get_info(i, 'person').get('infoproperties', {}).items():
                if not v:
                    continue
                if not p.get(k):
                    p[k] = v
                elif p[k] != v:
                    p[k] = u'{} / {}'.format(p[k], v)
        return items

    def _get_downloaded_list(self, export_list, sorting=None, reverse=False, datestamp=None):
        if not export_list or not datestamp:
            return
        download_url = u'https://files.tmdb.org/p/exports/{}_ids_{}.json.gz'.format(export_list, datestamp)
        raw_list = [loads(i) for i in Downloader(download_url=download_url).get_gzip_text().splitlines()]
        return sorted(raw_list, key=lambda k: k.get(sorting, ''), reverse=reverse) if sorting else raw_list

    def get_daily_list(self, export_list, sorting=None, reverse=False):
        if not export_list:
            return
        datestamp = get_datetime_now() - get_timedelta(days=2)
        datestamp = datestamp.strftime("%m_%d_%Y")
        # Pickle results rather than cache due to being such a large list
        return use_pickle(
            self._get_downloaded_list,
            export_list=export_list, sorting=sorting, reverse=reverse, datestamp=datestamp,
            cache_name=u'TMDb.Downloaded.List.v2.{}.{}.{}'.format(export_list, sorting, reverse, datestamp))

    def get_all_items_list(self, tmdb_type, page=None):
        if tmdb_type not in TMDB_ALL_ITEMS_LISTS:
            return
        daily_list = self.get_daily_list(
            export_list=TMDB_ALL_ITEMS_LISTS.get(tmdb_type, {}).get('type'),
            sorting=False, reverse=False)
        if not daily_list:
            return
        items = []
        param = TMDB_ALL_ITEMS_LISTS.get(tmdb_type, {}).get('params', {})
        limit = TMDB_ALL_ITEMS_LISTS.get(tmdb_type, {}).get('limit', 20)
        pos_z = try_int(page, fallback=1) * limit
        pos_a = pos_z - limit
        dbtype = convert_type(tmdb_type, 'dbtype')
        for i in daily_list[pos_a:pos_z]:
            if not i.get('id'):
                continue
            if tmdb_type in ['keyword', 'network', 'studio']:
                item = {
                    'label': i.get('name'),
                    'infolabels': {'mediatype': dbtype},
                    'infoproperties': {'dbtype': dbtype},
                    'unique_ids': {'tmdb': i.get('id')},
                    'params': {}}
            else:
                item = self.get_details(tmdb_type, i.get('id'))
            if not item:
                continue
            for k, v in param.items():
                item['params'][k] = v.format(tmdb_id=i.get('id'))
            items.append(item)
        if not items:
            return []
        if TMDB_ALL_ITEMS_LISTS.get(tmdb_type, {}).get('sort'):
            items = sorted(items, key=lambda k: k.get('label', ''))
        if len(daily_list) > pos_z:
            items.append({'next_page': try_int(page, fallback=1) + 1})
        return items

    def get_search_list(self, tmdb_type, **kwargs):
        """ standard kwargs: query= page= """
        kwargs['key'] = 'results'
        return self.get_basic_list(u'search/{}'.format(tmdb_type), tmdb_type, **kwargs)

    def get_basic_list(self, path, tmdb_type, key='results', params=None, base_tmdb_type=None, **kwargs):
        response = self.get_request_sc(path, **kwargs)
        results = response.get(key, []) if response else []
        items = [
            self.mapper.get_info(i, tmdb_type, definition=params, base_tmdb_type=base_tmdb_type)
            for i in results if i]
        if try_int(response.get('page', 0)) < try_int(response.get('total_pages', 0)):
            items.append({'next_page': try_int(response.get('page', 0)) + 1})
        return items

    def get_discover_list(self, tmdb_type, **kwargs):
        # TODO: Check what regions etc we need to have
        for k, v in kwargs.items():
            if k in ['with_id', 'with_separator', 'page', 'limit', 'nextpage', 'widget', 'fanarttv']:
                continue
            if k and v:
                break
        else:  # Only build discover list if we have params to pass
            return
        path = u'discover/{}'.format(tmdb_type)
        return self.get_basic_list(path, tmdb_type, **kwargs)

    def get_response_json(self, *args, **kwargs):
        kwargs['region'] = self.iso_country
        kwargs['language'] = self.req_language
        return self.get_api_request_json(self.get_request_url(*args, **kwargs))

    def get_request_sc(self, *args, **kwargs):
        """ Get API request using the short cache """
        kwargs['cache_days'] = CACHE_SHORT
        kwargs['region'] = self.iso_country
        kwargs['language'] = self.req_language
        return self.get_request(*args, **kwargs)

    def get_request_lc(self, *args, **kwargs):
        """ Get API request using the long cache """
        kwargs['cache_days'] = CACHE_LONG
        kwargs['region'] = self.iso_country
        kwargs['language'] = self.req_language
        return self.get_request(*args, **kwargs)
