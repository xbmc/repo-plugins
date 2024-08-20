from urllib.parse import quote_plus
from jurialmunkey.parser import try_int
from tmdbhelper.lib.addon.consts import CACHE_SHORT, CACHE_MEDIUM


def get_genres(self):
    genres = []
    from contextlib import suppress
    with suppress(KeyError, TypeError):
        genres += self.get_request_lc('genre', 'tv', 'list')['genres']
        genres += self.get_request_lc('genre', 'movie', 'list')['genres']
    if not genres:
        return {}
    return {i['name']: i['id'] for i in genres if i}


def get_tmdb_multisearch_validfy(query=None, validfy=True, scrub=True):
    if not validfy or not query:
        return query
    if scrub:  # Scrub added (Year) or other cruft in parentheses () added by Addons or TVDb
        query = query.split(' (', 1)[0]
    from tmdbhelper.lib.files.futils import validify_filename
    return validify_filename(query.lower(), alphanum=True)


def get_tmdb_multisearch_request(self, query=None, validfy=True, media_type=None, **kwargs):
    if not query:
        return
    request = self.get_request_sc('search', 'multi', language=self.req_language, query=query)
    request = request.get('results', [])
    if not request:
        return
    query = self.get_tmdb_multisearch_validfy(query, validfy=validfy)
    for i in request:
        if media_type and i.get('media_type') != media_type:
            continue
        if query == self.get_tmdb_multisearch_validfy(i.get('name', ''), validfy=validfy):
            return i
        if query == self.get_tmdb_multisearch_validfy(i.get('title', ''), validfy=validfy):
            return i
        if query == self.get_tmdb_multisearch_validfy(i.get('original_name', ''), validfy=validfy):
            return i
        if query == self.get_tmdb_multisearch_validfy(i.get('original_title', ''), validfy=validfy):
            return i


def get_tmdb_multisearch(self, query=None, validfy=True, media_type=None, **kwargs):
    kwargs['cache_days'] = CACHE_SHORT
    kwargs['cache_name'] = 'TMDb.get_tmdb_multisearch.v1'
    kwargs['cache_combine_name'] = True
    return self._cache.use_cache(
        self.get_tmdb_multisearch_request,
        query=query, validfy=validfy, media_type=media_type, **kwargs
    )


def get_tmdb_id(self, tmdb_type=None, imdb_id=None, tvdb_id=None, query=None, year=None, episode_year=None, raw_data=False, **kwargs):
    if not tmdb_type:
        return
    kwargs['cache_days'] = CACHE_MEDIUM
    kwargs['cache_name'] = 'TMDb.get_tmdb_id.v4'
    kwargs['cache_combine_name'] = True
    return self._cache.use_cache(
        self.get_tmdb_id_request,
        tmdb_type=tmdb_type, imdb_id=imdb_id, tvdb_id=tvdb_id, query=query, year=year,
        episode_year=episode_year, raw_data=raw_data, **kwargs
    )


def get_tmdb_id_request(self, tmdb_type, imdb_id, tvdb_id, query, year, episode_year, raw_data, **kwargs):
    func = self.get_request_lc
    if not tmdb_type:
        return
    request = None
    if tmdb_type == 'genre' and query:
        return self.genres.get(query, '')
    elif imdb_id:
        request = func('find', imdb_id, language=self.req_language, external_source='imdb_id')
        request = request.get(f'{tmdb_type}_results', [])
    elif tvdb_id:
        request = func('find', tvdb_id, language=self.req_language, external_source='tvdb_id')
        request = request.get(f'{tmdb_type}_results', [])
    elif query:
        if tmdb_type in ['movie', 'tv']:
            query = query.split(' (', 1)[0]  # Scrub added (Year) or other cruft in parentheses () added by Addons or TVDb
        if tmdb_type == 'tv':
            request = func('search', tmdb_type, language=self.req_language, query=quote_plus(query), first_air_date_year=year)
        else:
            request = func('search', tmdb_type, language=self.req_language, query=quote_plus(query), year=year)
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
    from xbmcgui import Dialog
    from tmdbhelper.lib.items.listitem import ListItem
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


def get_collection_tmdb_id(self, tmdb_id):
    details = self.get_details_request('movie', tmdb_id) if tmdb_id else None
    try:
        return details['belongs_to_collection']['id']
    except (KeyError, TypeError):
        return


def get_tmdb_id_list(self, items, tmdb_type=None, separator=None):
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
    from tmdbhelper.lib.addon.tmdate import format_date
    from tmdbhelper.lib.api.tmdb.mapping import get_episode_to_air
    from tmdbhelper.lib.addon.plugin import get_infolabel

    def _get_nextaired():
        response = self.get_response_json('tv', tmdb_id, language=self.req_language)
        if not response:
            return {}
        infoproperties = {}
        infoproperties.update(get_episode_to_air(response.get('next_episode_to_air'), 'next_aired'))
        infoproperties.update(get_episode_to_air(response.get('last_episode_to_air'), 'last_aired'))
        infoproperties['status'] = response.get('status')
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

    cache_name = f'TMDb.get_tv_nextaired.v2.{tmdb_id}'
    infoproperties = self._cache.use_cache(_get_nextaired, cache_name=cache_name, cache_days=CACHE_SHORT)
    return _get_formatted() if infoproperties else infoproperties


def get_details_request(self, tmdb_type, tmdb_id, season=None, episode=None, cache_refresh=False):
    path_affix = []
    if season is not None:
        path_affix += ['season', season]
    if season is not None and episode is not None:
        path_affix += ['episode', episode]
    return self.get_request_lc(
        tmdb_type, tmdb_id, *path_affix,
        append_to_response=self.append_to_response, cache_refresh=cache_refresh
    ) or {}


def get_details(self, tmdb_type, tmdb_id, season=None, episode=None, **kwargs):
    info_item = self.get_details_request(tmdb_type, tmdb_id)
    base_item = self.mapper.get_info(info_item, tmdb_type)
    if tmdb_type != 'tv' or season is None:
        return base_item
    # If we're getting season/episode details we need to add them to the base tv details
    child_type = 'episode' if episode else 'season'
    child_info = self.get_details_request(tmdb_type, tmdb_id, season, episode)
    return self.mapper.get_info(child_info, child_type, base_item, tmdb_id=tmdb_id)


def get_next_episode(self, tmdb_id, season, episode):
    snum, enum = try_int(season), try_int(episode)

    if snum < 1 or enum < 0:
        return

    all_episodes = self.get_flatseasons_list(tmdb_id)
    if not all_episodes:
        return

    for i in all_episodes:
        i_snum = try_int(i['infolabels'].get('season', -1))
        if i_snum > snum:
            return i
        if i_snum < snum:
            continue
        i_enum = try_int(i['infolabels'].get('episode', -1))
        if i_enum > enum:
            return i
