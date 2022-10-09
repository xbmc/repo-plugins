from xbmcgui import Dialog
from resources.lib.addon.plugin import ADDONPATH, get_mpaa_prefix, get_language, convert_type, get_setting, get_localized, get_infolabel
from resources.lib.addon.consts import TMDB_ALL_ITEMS_LISTS, TMDB_PARAMS_SEASONS, TMDB_PARAMS_EPISODES, TMDB_GENRE_IDS, CACHE_SHORT, CACHE_MEDIUM
from resources.lib.addon.parser import try_int, is_excluded
from resources.lib.addon.window import get_property
from resources.lib.addon.tmdate import format_date
from resources.lib.files.futils import use_json_filecache, validify_filename
from resources.lib.items.pages import PaginatedItems
from resources.lib.api.request import RequestAPI
from resources.lib.api.tmdb.mapping import ItemMapper, get_episode_to_air
from urllib.parse import quote_plus

""" Lazyimports
from resources.lib.items.listitem import ListItem
from resources.lib.files.downloader import Downloader
from resources.lib.addon.tmdate import get_datetime_now, get_timedelta
"""

ARTWORK_QUALITY = get_setting('artwork_quality', 'int')
ARTLANG_FALLBACK = True if get_setting('fanarttv_enfallback') and not get_setting('fanarttv_secondpref') else False

API_URL = 'https://api.themoviedb.org/3'
APPEND_TO_RESPONSE = 'credits,images,release_dates,content_ratings,external_ids,movie_credits,tv_credits,keywords,reviews,videos,watch/providers'


class TMDb(RequestAPI):
    def __init__(
            self,
            api_key='a07324c669cac4d96789197134ce272b',
            language=get_language(),
            mpaa_prefix=get_mpaa_prefix(),
            delay_write=False):
        super(TMDb, self).__init__(
            req_api_name='TMDb',
            req_api_url=API_URL,
            req_api_key=f'api_key={api_key}',
            delay_write=delay_write)
        self.language = language
        self.iso_language = language[:2]
        self.iso_country = language[-2:]
        self.req_language = f'{self.iso_language}-{self.iso_country}&include_image_language={self.iso_language},null{",en" if ARTLANG_FALLBACK else ""}&include_video_language={self.iso_language},null,en'
        self.mpaa_prefix = mpaa_prefix
        self.append_to_response = APPEND_TO_RESPONSE
        self.req_strip += [(self.append_to_response, ''), (self.req_language, f'{self.iso_language}{"_en" if ARTLANG_FALLBACK else ""}')]
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

    def _get_tmdb_multisearch_validfy(self, query=None, validfy=True):
        if not validfy or not query:
            return query
        return validify_filename(query.lower(), alphanum=True)

    def _get_tmdb_multisearch(self, query=None, validfy=True, media_type=None, **kwargs):
        if not query:
            return
        request = self.get_request_sc('search', 'multi', language=self.req_language, query=query)
        request = request.get('results', [])
        if not request:
            return
        query = self._get_tmdb_multisearch_validfy(query, validfy=validfy)
        for i in request:
            if media_type and i.get('media_type') != media_type:
                continue
            if query == self._get_tmdb_multisearch_validfy(i.get('name', ''), validfy=validfy):
                return i
            if query == self._get_tmdb_multisearch_validfy(i.get('title', ''), validfy=validfy):
                return i
            if query == self._get_tmdb_multisearch_validfy(i.get('original_name', ''), validfy=validfy):
                return i
            if query == self._get_tmdb_multisearch_validfy(i.get('original_title', ''), validfy=validfy):
                return i

    def get_tmdb_multisearch(self, query=None, validfy=True, media_type=None, **kwargs):
        kwargs['cache_days'] = CACHE_SHORT
        kwargs['cache_name'] = 'TMDb.get_tmdb_multisearch.v1'
        kwargs['cache_combine_name'] = True
        return self._cache.use_cache(
            self._get_tmdb_multisearch, query=query, validfy=validfy, media_type=media_type, **kwargs)

    def get_tmdb_id(self, tmdb_type=None, imdb_id=None, tvdb_id=None, query=None, year=None, episode_year=None, raw_data=False, **kwargs):
        if not tmdb_type:
            return
        kwargs['cache_days'] = CACHE_SHORT
        kwargs['cache_name'] = 'TMDb.get_tmdb_id.v3'
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
            request = request.get(f'{tmdb_type}_results', [])
        elif tvdb_id:
            request = func('find', tvdb_id, language=self.req_language, external_source='tvdb_id')
            request = request.get(f'{tmdb_type}_results', [])
        elif query:
            if tmdb_type in ['movie', 'tv']:
                query = query.split(' (', 1)[0]  # Scrub added (Year) or other cruft in parentheses () added by Addons or TVDb
            query = quote_plus(query)
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
        from resources.lib.items.listitem import ListItem
        if not query or not tmdb_type:
            return
        response = self.get_tmdb_id(tmdb_type, query=query, raw_data=True)
        if not response:
            return
        items = [ListItem(**self.mapper.get_info(i, tmdb_type)).get_listitem() for i in response]
        if not items:
            return
        x = 0
        if not auto_single or len(items) != 1:
            x = Dialog().select(header, items, useDetails=use_details)
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
                temp_list = f'{temp_list}{separator}{item_id}' if temp_list else item_id
            else:  # If no separator, assume that we just want to use the first found ID
                temp_list = str(item_id)
                break  # Stop once we have a item
        temp_list = temp_list if temp_list else 'null'
        return temp_list

    def get_tvshow_nextaired(self, tmdb_id):
        """ Get updated next aired data for tvshows using 24hr cache """

        def _get_nextaired():
            response = self.get_response_json('tv', tmdb_id, language=self.req_language)
            if not response:
                return {}
            infoproperties = {}
            infoproperties.update(get_episode_to_air(response.get('next_episode_to_air'), 'next_aired'))
            infoproperties.update(get_episode_to_air(response.get('last_episode_to_air'), 'last_aired'))
            return infoproperties

        def _get_formatted():
            df = get_infolabel('Skin.String(TMDbHelper.Date.Format)') or '%d %b %Y'
            for i in ['next_aired', 'last_aired']:
                try:
                    air_date = infoproperties[f'{i}.original']
                except KeyError:
                    continue
                infoproperties[f'{i}.custom'] = format_date(air_date, df)
            return infoproperties

        if not tmdb_id:
            return {}

        cache_name = f'TMDb.get_tv_nextaired.{tmdb_id}'
        infoproperties = self._cache.use_cache(_get_nextaired, cache_name=cache_name, cache_days=CACHE_SHORT)
        return _get_formatted() if infoproperties else infoproperties

    def get_details_request(self, tmdb_type, tmdb_id, season=None, episode=None, cache_refresh=False):
        path_affix = []
        if season is not None:
            path_affix += ['season', season]
        if season is not None and episode is not None:
            path_affix += ['episode', episode]
        return self.get_request_lc(
            tmdb_type, tmdb_id, *path_affix, append_to_response=self.append_to_response, cache_refresh=cache_refresh) or {}

    def get_details(self, tmdb_type, tmdb_id, season=None, episode=None, **kwargs):
        info_item = self.get_details_request(tmdb_type, tmdb_id)
        base_item = self.mapper.get_info(info_item, tmdb_type)
        if tmdb_type != 'tv' or season is None:
            return base_item
        # If we're getting season/episode details we need to add them to the base tv details
        child_type = 'episode' if episode else 'season'
        child_info = self.get_details_request(tmdb_type, tmdb_id, season, episode)
        return self.mapper.get_info(child_info, child_type, base_item, tmdb_id=tmdb_id)

    def _get_upnext_season_item(self, base_item):
        base_item['params']['info'] = 'trakt_upnext'
        base_item['infolabels']['mediatype'] = 'season'
        base_item['label'] = base_item['infolabels']['title'] = get_localized(32043)
        return [base_item]

    def get_flatseasons_list(self, tmdb_id):
        request = self.get_request_sc(f'tv/{tmdb_id}')
        if not request or not request.get('seasons'):
            return []
        return [
            j for i in request['seasons'] for j in self.get_episode_list(tmdb_id, i['season_number'])
            if i.get('season_number')]

    def get_episode_group_episodes_list(self, tmdb_id, group_id, position):
        request = self.get_request_sc(f'tv/episode_group/{group_id}')
        if not request or not request.get('groups'):
            return []
        eps_group = request.get('groups', [])[try_int(position)] or {}
        return [
            self._clean_merged(
                self.mapper.get_info(i, 'episode', None, definition=TMDB_PARAMS_EPISODES, tmdb_id=tmdb_id),
                tmdb_id=tmdb_id)
            for i in eps_group.get('episodes', [])]

    def get_episode_group_seasons_list(self, tmdb_id, group_id):
        request = self.get_request_sc(f'tv/episode_group/{group_id}')
        if not request or not request.get('groups'):
            return []
        items = []
        items_append = items.append
        for x, i in enumerate(request.get('groups', [])):
            item = self.mapper.get_info(i, 'tv', None, tmdb_id=tmdb_id, definition={
                'info': 'episode_group_episodes', 'tmdb_type': 'tv', 'tmdb_id': str(tmdb_id),
                'group_id': group_id, 'position': str(x)})
            item['infolabels']['season'] = -1
            item['infolabels']['episode'] = len(i.get('episodes', []))
            item = self._clean_merged(item, tmdb_id=tmdb_id, episode_group=True)
            items_append(item)
        return items

    def get_episode_groups_list(self, tmdb_id):
        request = self.get_request_sc(f'tv/{tmdb_id}/episode_groups')
        if not request or not request.get('results'):
            return []
        items = [
            self._clean_merged(
                self.mapper.get_info(i, 'tv', None, tmdb_id=tmdb_id, definition={
                    'info': 'episode_group_seasons', 'tmdb_type': 'tv', 'tmdb_id': str(tmdb_id), 'group_id': '{id}'}),
                tmdb_id=tmdb_id, episode_group=True)
            for i in request.get('results', [])]
        return items

    def _get_videos(self, tmdb_id, tmdb_type, season=None, episode=None):
        path = f'{tmdb_type}/{tmdb_id}'
        if season is not None:
            path = f'{path}/season/{season}'
        if episode is not None:
            path = f'{path}/episode/{episode}'
        request = self.get_request_sc(f'{path}/videos') or {}
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
            item['art']['thumb'] = f'https://img.youtube.com/vi/{i["key"]}/0.jpg'
            item['path'] = f'plugin://plugin.video.youtube/play/?video_id={i["key"]}'
            item['is_folder'] = False
            items.append(item)
        return items

    def get_season_list(self, tmdb_id, special_folders=0, get_detailed=False):
        """
        special_folders: int binary to hide:
        001 (1) = Hide Specials, 010 (2) = Hide Up Next, 100 (4) = Hide Groups

        Use get_detailed flag if going to be getting details via itembuilder anyway
        TODO: Check if cached detailed version exists and automate this part
        """
        request = self.get_details_request('tv', tmdb_id) if get_detailed else self.get_request_sc(f'tv/{tmdb_id}')
        if not request:
            return []
        base_item = self.mapper.get_info(request, 'tv')
        items, items_end = [], []
        for i in request.get('seasons', []):
            item = self.mapper.get_info(i, 'season', base_item, definition=TMDB_PARAMS_SEASONS, tmdb_id=tmdb_id)
            if i.get('season_number') != 0:
                items.append(item)
            elif ((special_folders >> 0) & 1) == 0:  # on bit in 0 pos hides specials
                items_end.append(item)

        # Episode Groups
        if ((special_folders >> 2) & 1) == 0:  # on bit in 2 pos hides episode groups
            egroups = self.get_request_sc(f'tv/{tmdb_id}/episode_groups')
            if egroups and egroups.get('results'):
                egroup_item = self.mapper.get_info({
                    'title': get_localized(32345)}, 'season', base_item, tmdb_id=tmdb_id, definition={
                        'info': 'episode_groups', 'tmdb_type': 'tv', 'tmdb_id': str(tmdb_id)})
                egroup_item['art']['thumb'] = egroup_item['art']['poster'] = f'{ADDONPATH}/resources/icons/trakt/groupings.png'
                egroup_item['infolabels']['season'] = -1
                egroup_item['infolabels']['episode'] = 0
                egroup_item['infoproperties']['specialseason'] = get_localized(32345)
                items_end.append(egroup_item)

        # Up Next
        if ((special_folders >> 1) & 1) == 0:  # on bit in 1 pos hides up next
            if get_property('TraktIsAuth') == 'True':
                upnext_item = self.mapper.get_info({
                    'title': get_localized(32043)}, 'season', base_item, tmdb_id=tmdb_id, definition={
                        'info': 'trakt_upnext', 'tmdb_type': 'tv', 'tmdb_id': str(tmdb_id)})
                upnext_item['art']['thumb'] = upnext_item['art']['poster'] = f'{ADDONPATH}/resources/icons/trakt/up-next.png'
                upnext_item['infolabels']['season'] = -1
                upnext_item['infolabels']['episode'] = 0
                upnext_item['infoproperties']['specialseason'] = get_localized(32043)
                items_end.append(upnext_item)
        return items + items_end

    def _clean_merged(self, item, tmdb_id, episode_group=False):
        item['infolabels'].pop('tvshowtitle', None)
        item['unique_ids']['tvshow.tmdb'] = item['infoproperties']['tvshow.tmdb_id'] = tmdb_id
        if episode_group:
            item['unique_ids']['tmdb'] = item['infoproperties']['tmdb_id'] = tmdb_id
        return item

    def get_episode_list(self, tmdb_id, season, get_detailed=False):
        """
        Use get_detailed flag if going to be getting details via itembuilder anyway
        TODO: Check if cached detailed version exists and automate this part
        """
        request = self.get_details_request('tv', tmdb_id, season) if get_detailed else self.get_request_sc(f'tv/{tmdb_id}/season/{season}')
        if not request:
            return []
        items = [
            self._clean_merged(
                item=self.mapper.get_info(i, 'episode', None, definition=TMDB_PARAMS_EPISODES, tmdb_id=tmdb_id),
                tmdb_id=tmdb_id)
            for i in request.get('episodes', [])]
        return items

    def get_cast_list(self, tmdb_id, tmdb_type, season=None, episode=None, keys=['cast', 'guest_stars'], aggregate=False):
        """ Get cast list
        endpoint switch to aggregate_credits for full tv series cast
        """
        items = []
        if season is not None and episode is not None:
            affix = f'season/{season}/episode/{episode}'
        elif season is not None:
            affix = f'season/{season}'
        else:
            affix = None
        endpoint = 'aggregate_credits' if aggregate and tmdb_type == 'tv' and affix is None else 'credits'
        response = self.get_request_lc(tmdb_type, tmdb_id, affix, endpoint)
        if not response:
            return []

        # Join guest stars list etc
        cast_list = []
        for key in keys:
            cast_list += response.get(key) or []

        # Add items
        item_ids = []
        if endpoint == 'aggregate_credits':
            cast_list_sorted = sorted(cast_list, key=lambda k: k.get('roles', [{}])[0].get('episode_count', 0), reverse=True)
        else:
            cast_list_sorted = sorted(cast_list, key=lambda k: k.get('order', 1000))
        for i in cast_list_sorted:
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
                    p[k] = f'{p[k]} / {v}'
        for i in items:
            i['label2'] = i['infoproperties'].get('role')
        return items

    def _get_downloaded_list(self, export_list, sorting=None, reverse=False, datestamp=None):
        from resources.lib.files.downloader import Downloader
        if not export_list or not datestamp:
            return
        from json import loads as json_loads
        download_url = f'https://files.tmdb.org/p/exports/{export_list}_ids_{datestamp}.json.gz'
        raw_list = [json_loads(i) for i in Downloader(download_url=download_url).get_gzip_text().splitlines()]
        return sorted(raw_list, key=lambda k: k.get(sorting, ''), reverse=reverse) if sorting else raw_list

    def get_daily_list(self, export_list, sorting=None, reverse=False):
        if not export_list:
            return
        from resources.lib.addon.tmdate import get_datetime_now, get_timedelta
        datestamp = get_datetime_now() - get_timedelta(days=2)
        datestamp = datestamp.strftime("%m_%d_%Y")
        # Pickle results rather than cache due to being such a large list
        return use_json_filecache(
            self._get_downloaded_list,
            export_list=export_list, sorting=sorting, reverse=reverse, datestamp=datestamp,
            cache_name=f'TMDb.Downloaded.List.v3.{export_list}.{sorting}.{reverse}')

    def get_all_items_list(self, tmdb_type, page=None):
        try:
            schema = TMDB_ALL_ITEMS_LISTS[tmdb_type]
        except KeyError:
            return
        daily_list = self.get_daily_list(
            export_list=schema.get('type'),
            sorting=False, reverse=False)
        if not daily_list:
            return
        items = []
        param = schema.get('params', {})
        limit = schema.get('limit', 20)
        pos_z = try_int(page, fallback=1) * limit
        pos_a = pos_z - limit
        dbtype = convert_type(tmdb_type, 'dbtype')
        for i in daily_list[pos_a:pos_z]:
            if not i.get('id'):
                continue
            item = {
                'label': i.get('name'),
                'infolabels': {'mediatype': dbtype},
                'infoproperties': {'dbtype': dbtype},
                'unique_ids': {'tmdb': i.get('id')},
                'params': {}}
            if not item:
                continue
            for k, v in param.items():
                item['params'][k] = v.format(tmdb_id=i.get('id'), label=i.get('name'))
            items.append(item)
        if not items:
            return []
        if schema.get('sort'):
            items = sorted(items, key=lambda k: k.get('label', ''))
        if len(daily_list) > pos_z:
            items.append({'next_page': try_int(page, fallback=1) + 1})
        return items

    def get_search_list(self, tmdb_type, query=None, **kwargs):
        """ standard kwargs: query= page= """
        if not query:
            return
        kwargs['key'] = 'results'
        kwargs['query'] = quote_plus(query)
        return self.get_basic_list(f'search/{tmdb_type}', tmdb_type, **kwargs)

    def get_basic_list(self, path, tmdb_type, key='results', params=None, base_tmdb_type=None, limit=None, filters={}, **kwargs):
        response = self.get_request_sc(path, **kwargs)
        results = response.get(key, []) if response else []
        items = [
            self.mapper.get_info(i, tmdb_type, definition=params, base_tmdb_type=base_tmdb_type, iso_country=self.iso_country)
            for i in results if i]
        if filters:
            items = [i for i in items if not is_excluded(i, **filters)]
        if try_int(response.get('page', 0)) < try_int(response.get('total_pages', 0)):
            items.append({'next_page': try_int(response.get('page', 0)) + 1})
        elif limit is not None:
            paginated_items = PaginatedItems(items, page=kwargs.get('page', 1), limit=limit)
            return paginated_items.items + paginated_items.next_page
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
        path = f'discover/{tmdb_type}'
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
        kwargs['cache_days'] = CACHE_MEDIUM
        kwargs['region'] = self.iso_country
        kwargs['language'] = self.req_language
        return self.get_request(*args, **kwargs)
