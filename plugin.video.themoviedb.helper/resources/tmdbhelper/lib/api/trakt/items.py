import re
import random
from tmdbhelper.lib.addon.plugin import PLUGINPATH, convert_type, convert_trakt_type, get_setting
from jurialmunkey.parser import try_int, try_str, del_empty_keys, get_params, partition_list
from tmdbhelper.lib.addon.tmdate import date_in_range
from tmdbhelper.lib.items.filters import is_excluded


REGEX_DEFARTICLE = r'(?i)^The '

EPISODE_PARAMS = {
    'info': 'details', 'tmdb_type': 'tv', 'tmdb_id': '{tmdb_id}',
    'season': '{season}', 'episode': '{number}'}

SEASON_PARAMS = {
    'info': 'episodes', 'tmdb_type': 'tv', 'tmdb_id': '{tmdb_id}',
    'season': '{number}'}


def _sort_itemlist(items, sort_by=None, sort_how=None, trakt_type=None):
    _dummydict, _dummystr, _dummyint = {}, '', 0
    _dummystr_release = '9999-01-01T00:00:00.000Z'

    def _item_lambda_parent(i, sort_key):
        return i.get(trakt_type or i.get('type'), _dummydict).get(sort_key)

    def _sort_lambda_simple(items, sort_key: str, sort_fallback=None, sort_reverse=False):
        return sorted(items, key=lambda i: i.get(sort_key) or sort_fallback, reverse=sort_reverse)

    def _sort_lambda_parent(items, sort_key: str, sort_fallback=None, sort_reverse=False):
        return sorted(items, key=lambda i: _item_lambda_parent(i, sort_key) or sort_fallback, reverse=sort_reverse)

    def _sort_lambda_ignore(items, sort_key: str, sort_fallback=None, sort_reverse=False):
        if not get_setting('trakt_sortignorearticle'):
            return _sort_lambda_parent(items, sort_key, sort_fallback, sort_reverse)
        return sorted(items, key=lambda i: re.sub(REGEX_DEFARTICLE, '', _item_lambda_parent(i, sort_key) or sort_fallback), reverse=sort_reverse)

    def _sort_lambda_max_of(items, sort_keys: list, sort_fallback=None, sort_reverse=False):
        return sorted(items, key=lambda i: max(*[i.get(k) or sort_fallback for k in sort_keys]), reverse=sort_reverse)

    def _sort_lambda_mixing(items, sort_keys: tuple, sort_fallback=None, sort_reverse=False, sort_types: list = None):
        return sorted(
            items,
            key=lambda i: (
                try_str(i.get(trakt_type or i.get('type'), _dummydict).get(sort_keys[0]) or sort_fallback))
            if (trakt_type or i.get('type')) in sort_types
            else (
                try_str(i.get(trakt_type or i.get('type'), _dummydict).get(sort_keys[1]) or sort_fallback)),
            reverse=sort_reverse)

    def _sort_lambda_airing(items, sort_start: int):
        ly, lx = partition_list(items, lambda i: date_in_range(
            i.get(trakt_type or i.get('type'), _dummydict).get('first_aired'),
            utc_convert=True, start_date=sort_start, days=abs(sort_start) + 1))
        return _sort_lambda_parent(list(lx), 'first_aired', _dummystr, True) + list(ly)

    def _sort_lambda_random(items):
        random.shuffle(items)
        return items

    reverse = True if sort_how == 'desc' else False
    routing = {
        'unsorted': lambda: items,
        'rank': lambda: _sort_lambda_simple(items, 'rank', _dummyint, reverse),
        'plays': lambda: _sort_lambda_simple(items, 'plays', _dummyint, reverse),
        'watched': lambda: _sort_lambda_simple(items, 'last_watched_at', _dummystr, reverse),
        'paused': lambda: _sort_lambda_simple(items, 'paused_at', _dummystr, reverse),
        'added': lambda: _sort_lambda_simple(items, 'listed_at', _dummystr, reverse),
        'collected': lambda: _sort_lambda_max_of(items, ['collected_at', 'last_collected_at'], _dummystr, reverse),
        'title': lambda: _sort_lambda_ignore(items, 'title', _dummystr, reverse),
        'year': lambda: _sort_lambda_parent(items, 'year', _dummyint if reverse else 9999, reverse),
        'released': lambda: _sort_lambda_mixing(items, ('first_aired', 'released',), _dummystr if reverse else _dummystr_release, reverse, sort_types=['show', 'episode']),
        'runtime': lambda: _sort_lambda_parent(items, 'runtime', _dummyint, reverse),
        'popularity': lambda: _sort_lambda_parent(items, 'comment_count', _dummyint, reverse),
        'percentage': lambda: _sort_lambda_parent(items, 'rating', _dummyint, reverse),
        'votes': lambda: _sort_lambda_parent(items, 'votes', _dummyint, reverse),
        'random': lambda: _sort_lambda_random(items, ),
        'activity': lambda: _sort_lambda_max_of(items, ['last_watched_at', 'paused_at', 'listed_at'], _dummystr, reverse),
        'airing': lambda: _sort_lambda_airing(items, try_int(sort_how, fallback=_dummyint))
    }

    try:
        return routing[sort_by]()
    except KeyError:
        return _sort_lambda_simple(items, 'listed_at', _dummystr, True)


def _get_item_title(item):
    if 'title' in item:
        return item['title']
    if 'name' in item:
        return item['name']


def _get_item_infolabels(item, item_type=None, infolabels=None, show=None):
    infolabels = infolabels or {}
    infolabels['title'] = _get_item_title(item)
    infolabels['year'] = item.get('year')
    infolabels['premiered'] = item.get('first_aired') or item.get('released') or ''
    infolabels['premiered'] = infolabels['premiered'][:10]
    infolabels['mediatype'] = convert_type(convert_trakt_type(item_type), 'dbtype')
    if show:
        infolabels['tvshowtitle'] = show.get('title') or ''
    if item_type == 'episode':
        infolabels['episode'] = item.get('number')
        infolabels['season'] = item.get('season')
    if item_type == 'season':
        infolabels['season'] = item.get('number')
    return del_empty_keys(infolabels)


def _get_item_infoproperties(item, item_type=None, infoproperties=None, show=None, main=None):
    infoproperties = infoproperties or {}
    infoproperties['tmdb_type'] = convert_trakt_type(item_type)

    def _set_main_infoproperties():
        if not main:
            return
        for k, v in main.items():
            if v is None or not isinstance(v, (str, int, float,)):
                continue
            infoproperties[f'trakt_{k}'] = f'{v}'

    def _set_episode_infoproperties():
        if item_type != 'episode':
            return
        infoproperties[f'episode_type'] = item.get('episode_type')

    _set_main_infoproperties()
    _set_episode_infoproperties()

    return del_empty_keys(infoproperties)


def _get_item_unique_ids(item, unique_ids=None, prefix=None, show=None):
    prefix = prefix or ''
    unique_ids = unique_ids or {}
    for k, v in item.get('ids', {}).items():
        unique_ids[f'{prefix}{k}'] = v
    if show:
        unique_ids = _get_item_unique_ids(show, unique_ids, prefix='tvshow.')
        unique_ids['tmdb'] = show.get('ids', {}).get('tmdb')
    return del_empty_keys(unique_ids)


def _get_item_info(item, item_type=None, base_item=None, check_tmdb_id=True, params_def=None):
    base_item = base_item or {}
    item_info = item.get(item_type, {}) or item
    show_item = None

    if item_type in ['season', 'episode']:
        show_item = item.get('show')
        if not params_def:
            if item_type == 'season':
                params_def = SEASON_PARAMS
            else:
                params_def = EPISODE_PARAMS

    if not item_info:
        return base_item

    if check_tmdb_id and not item_info.get('ids', {}).get('tmdb'):
        if not show_item or not show_item.get('ids', {}).get('tmdb'):
            return base_item

    base_item['label'] = _get_item_title(item_info) or ''
    base_item['infolabels'] = _get_item_infolabels(item_info, item_type=item_type, infolabels=base_item.get('infolabels', {}), show=show_item)
    base_item['infoproperties'] = _get_item_infoproperties(item_info, item_type=item_type, infoproperties=base_item.get('infoproperties', {}), show=show_item, main=item)
    base_item['unique_ids'] = _get_item_unique_ids(item_info, unique_ids=base_item.get('unique_ids', {}), show=show_item)
    base_item['params'] = get_params(
        item_info, convert_trakt_type(item_type),
        tmdb_id=base_item.get('unique_ids', {}).get('tmdb'),
        params=base_item.get('params', {}),
        definition=params_def)
    base_item['path'] = PLUGINPATH
    return base_item


class TraktItems():
    def __init__(self, items, trakt_type=None, headers=None):
        self.items = items or []
        self.trakt_type = trakt_type
        self.sort_by = 'unsorted'
        self.sort_how = None
        self.configured = {'items': [], 'headers': {k.lower(): v for k, v in headers.items()} if headers else {}}

    def sort_items(self, sort_by=None, sort_how=None):
        """ (Re)Sorts items and returns sorted items """
        self.sort_by = sort_by or self.sort_by
        self.sort_how = sort_how or self.sort_how
        self.items = _sort_itemlist(self.items, self.sort_by, self.sort_how, self.trakt_type)
        return self.items

    def configure_items(self, permitted_types=None, params_def=None, filters=None):
        """ (Re)Configures items for passing to listitem class in container and returns configured items """
        for i in self.items:
            i_type = self.trakt_type or i.get('type', None)
            if permitted_types and i_type not in permitted_types:
                continue
            item = _get_item_info(i, item_type=i_type, params_def=params_def)
            if not item:
                continue
            if filters and is_excluded(item, **filters):
                continue
            # Check we haven't already added that item
            unique_id = f"{item['unique_ids']['tmdb']}_{item.get('label')}_{item['infolabels'].get('season')}_{item['infolabels'].get('episode')}"
            if unique_id in self.configured.get(f'{i_type}_ids', []):
                continue
            # Add item ID to checklist to avoid duplicates
            self.configured.setdefault(f'{i_type}_ids', []).append(unique_id)
            # Also add item to a list only containing that item type
            # Useful if we need to only get one type of item from a mixed list (e.g. only "movies")
            self.configured.setdefault(f'{i_type}s', []).append(item)
            self.configured['items'].append(item)
        return self.configured

    def build_items(self, sort_by=None, sort_how=None, permitted_types=None, params_def=None, filters=None):
        """ Sorts and Configures Items """
        self.sort_items(sort_by, sort_how)
        self.configure_items(permitted_types, params_def, filters)
        return self.configured
