from tmdbhelper.lib.addon.consts import TMDB_PARAMS_EPISODES, TMDB_PARAMS_SEASONS, TMDB_ALL_ITEMS_LISTS


def clean_merged(item, tmdb_id, episode_group=False):
    item['infolabels'].pop('tvshowtitle', None)
    item['unique_ids']['tvshow.tmdb'] = item['infoproperties']['tvshow.tmdb_id'] = tmdb_id
    if episode_group:
        item['unique_ids']['tmdb'] = item['infoproperties']['tmdb_id'] = tmdb_id
    if item['infolabels'].get('season') == 0:
        item['infoproperties']['IsSpecial'] = 'true'
    return item


def get_flatseasons_list(self, tmdb_id):
    request = self.get_request_sc(f'tv/{tmdb_id}')
    if not request or not request.get('seasons'):
        return []
    return (
        j for i in request['seasons'] for j in self.get_episode_list(tmdb_id, i['season_number'])
        if i.get('season_number'))


def get_episode_group_episodes_list(self, tmdb_id, group_id, position):
    from jurialmunkey.parser import try_int
    request = self.get_request_sc(f'tv/episode_group/{group_id}')
    if not request or not request.get('groups'):
        return []
    eps_group = request.get('groups', [])[try_int(position)] or {}
    return [
        clean_merged(
            self.mapper.get_info(i, 'episode', None, definition=TMDB_PARAMS_EPISODES, tmdb_id=tmdb_id),
            tmdb_id=tmdb_id)
        for i in eps_group.get('episodes', [])
    ]


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
        item = clean_merged(item, tmdb_id=tmdb_id, episode_group=True)
        items_append(item)
    return items


def get_episode_groups_list(self, tmdb_id):
    request = self.get_request_sc(f'tv/{tmdb_id}/episode_groups')
    if not request or not request.get('results'):
        return []
    items = [
        clean_merged(
            self.mapper.get_info(i, 'tv', None, tmdb_id=tmdb_id, definition={
                'info': 'episode_group_seasons', 'tmdb_type': 'tv', 'tmdb_id': str(tmdb_id), 'group_id': '{id}'}),
            tmdb_id=tmdb_id, episode_group=True)
        for i in request.get('results', [])]
    return items


def get_videos_list(self, tmdb_id, tmdb_type, season=None, episode=None):

    def _get_videos_list(list_season=None, list_episode=None):
        path = f'{tmdb_type}/{tmdb_id}'
        if list_season is not None:
            path = f'{path}/season/{list_season}'
        if episode is not None:
            path = f'{path}/episode/{list_episode}'
        request = self.get_request_sc(f'{path}/videos') or {}
        return request.get('results') or []

    results = _get_videos_list(season, episode)
    if episode is not None:  # Also get season videos
        results = results + _get_videos_list(season)
    if season is not None:  # Also get base show videos
        results = results + _get_videos_list()
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
            item['infoproperties']['IsSpecial'] = 'true'
            items_end.append(item)

    from tmdbhelper.lib.addon.plugin import ADDONPATH, get_localized

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
            egroup_item['infoproperties']['IsSpecial'] = 'true'
            items_end.append(egroup_item)

    # Up Next
    if ((special_folders >> 1) & 1) == 0:  # on bit in 1 pos hides up next
        from jurialmunkey.window import get_property
        if get_property('TraktIsAuth') == 'True':
            upnext_item = self.mapper.get_info({
                'title': get_localized(32043)}, 'season', base_item, tmdb_id=tmdb_id, definition={
                    'info': 'trakt_upnext', 'tmdb_type': 'tv', 'tmdb_id': str(tmdb_id)})
            upnext_item['art']['thumb'] = upnext_item['art']['poster'] = f'{ADDONPATH}/resources/icons/trakt/up-next.png'
            upnext_item['infolabels']['season'] = -1
            upnext_item['infolabels']['episode'] = 0
            upnext_item['infoproperties']['specialseason'] = get_localized(32043)
            upnext_item['infoproperties']['IsSpecial'] = 'true'
            items_end.append(upnext_item)

    return items + items_end


def get_episode_list(self, tmdb_id, season, get_detailed=False):
    """
    Use get_detailed flag if going to be getting details via itembuilder anyway
    TODO: Check if cached detailed version exists and automate this part
    """
    request = self.get_details_request('tv', tmdb_id, season) if get_detailed else self.get_request_sc(f'tv/{tmdb_id}/season/{season}')
    if not request:
        return []
    items = (
        clean_merged(
            item=self.mapper.get_info(i, 'episode', None, definition=TMDB_PARAMS_EPISODES, tmdb_id=tmdb_id),
            tmdb_id=tmdb_id)
        for i in request.get('episodes', []))
    return items


def get_cast_list(
        self, tmdb_id, tmdb_type, season=None, episode=None, keys=None, aggregate=False,
        paginated=True, limit=None, page=None, **kwargs
):
    """ Get cast list
    endpoint switch to aggregate_credits for full tv series cast
    """
    keys = keys or ['cast', 'guest_stars']
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

    if not paginated:
        return items

    return self.get_paginated_items(items, limit, page)


def get_downloaded_list(export_list, sorting=None, reverse=False, datestamp=None):
    from tmdbhelper.lib.files.downloader import Downloader
    if not export_list or not datestamp:
        return
    from json import loads as json_loads
    download_url = f'https://files.tmdb.org/p/exports/{export_list}_ids_{datestamp}.json.gz'
    raw_list = [json_loads(i) for i in Downloader(download_url=download_url).get_gzip_text().splitlines()]
    return sorted(raw_list, key=lambda k: k.get(sorting, ''), reverse=reverse) if sorting else raw_list


def get_daily_list(export_list, sorting=None, reverse=False):
    if not export_list:
        return
    from tmdbhelper.lib.addon.tmdate import get_datetime_now, get_timedelta
    from tmdbhelper.lib.files.futils import use_json_filecache
    datestamp = get_datetime_now() - get_timedelta(days=2)
    datestamp = datestamp.strftime("%m_%d_%Y")
    # Pickle results rather than cache due to being such a large list
    return use_json_filecache(
        get_downloaded_list,
        export_list=export_list, sorting=sorting, reverse=reverse, datestamp=datestamp,
        cache_name=f'TMDb.Downloaded.List.v3.{export_list}.{sorting}.{reverse}')


def get_all_items_list(tmdb_type, page=None):
    try:
        schema = TMDB_ALL_ITEMS_LISTS[tmdb_type]
    except KeyError:
        return
    daily_list = get_daily_list(
        export_list=schema.get('type'),
        sorting=False, reverse=False)
    if not daily_list:
        return

    from jurialmunkey.parser import try_int
    from tmdbhelper.lib.addon.plugin import convert_type

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
    from urllib.parse import quote_plus
    kwargs['key'] = 'results'
    kwargs['query'] = quote_plus(query)
    return self.get_basic_list(f'search/{"multi" if tmdb_type == "both" else tmdb_type}', tmdb_type, **kwargs)


def get_basic_list(
        self, path, tmdb_type, key='results', params=None, base_tmdb_type=None, limit=None, filters={},
        sort_key=None, sort_key_order=None, stacked=None, paginated=True, length=None, icon_path=None, **kwargs
):

    from jurialmunkey.parser import try_int

    length = length or self.page_length

    def _get_page(page):
        kwargs['page'] = page
        return self.get_request_sc(path, **kwargs)

    def _get_random():
        import random

        page_end = int(kwargs.pop('random_page_limit', 10))
        response = _get_page(random.randint(1, page_end))

        if not response:
            return
        if response.get(key):
            return response
        if int(response.get('total_pages') or 1) < page_end:
            return _get_page(random.randint(1, int(response['total_pages'] or 1)))

    def _get_results(response):
        try:
            return response[key] or []
        except (KeyError, TypeError):
            return []

    def _get_response(page, length):
        if page == 'random':
            response = _get_random()
            results = _get_results(response)
            return response, results
        results = []
        page = try_int(page, fallback=1)
        for x in range(try_int(length, fallback=1)):
            response = _get_page(page + x)
            results += _get_results(response)
            if int(response.get('total_pages') or 1) <= int(response.get('page') or 1):
                break
        return response, results

    response, results = _get_response(kwargs.get('page'), length=length)
    results = sorted(results, key=lambda i: i.get(sort_key, 0), reverse=sort_key_order != 'asc') if sort_key else results

    add_infoproperties = [('total_pages', response.get('total_pages')), ('total_results', response.get('total_results'))]

    item_tmdb_type = None if tmdb_type == 'both' else tmdb_type

    items = [
        self.mapper.get_info(
            i, item_tmdb_type or i.get('media_type', ''),
            definition=params,
            base_tmdb_type=base_tmdb_type,
            iso_country=self.iso_country,
            add_infoproperties=add_infoproperties)
        for i in results if i]

    def _add_icon(i):
        import xbmcvfs
        tmdb_id = i.get('unique_ids', {}).get('tmdb')
        if not tmdb_id:
            return i
        filepath = xbmcvfs.validatePath(xbmcvfs.translatePath(f'{icon_path}/{tmdb_id}.png'))
        if not xbmcvfs.exists(filepath):
            return i
        i['art']['icon'] = filepath
        return i

    if icon_path:
        items = [_add_icon(i) for i in items]

    if filters:
        from tmdbhelper.lib.items.filters import is_excluded
        items = [i for i in items if not is_excluded(i, **filters)]

    if stacked and items:
        stacked_list = [items.pop(0)]
        for i in items:
            x = len(stacked_list) - 1
            p = stacked_list[x]
            if p['unique_ids'].get('tmdb') != i['unique_ids'].get('tmdb'):
                stacked_list.append(i)
                continue
            for b, k in stacked:
                iv = i[b].get(k)
                if iv is None:
                    continue
                pv = p[b].get(k)
                p[b][k] = iv if pv is None else f'{pv} / {iv}'
        items = stacked_list

    if not paginated:
        return items

    return self.get_paginated_items(items, limit, kwargs['page'], response.get('total_pages'))


def get_discover_list(self, tmdb_type, **kwargs):
    # TODO: Check what regions etc we need to have
    to_del = ['with_id', 'with_separator', 'cacheonly', 'nextpage', 'widget', 'fanarttv']
    for k, v in kwargs.items():
        if k in to_del:
            continue
        if k in ['page', 'limit']:
            continue
        if k and v:
            break
    else:  # Only build discover list if we have params to pass
        return
    for k in to_del:
        kwargs.pop(k, None)
    path = f'discover/{tmdb_type}'
    return self.get_basic_list(path, tmdb_type, **kwargs)
