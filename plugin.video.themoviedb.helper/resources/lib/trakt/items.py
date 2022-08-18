import random
from resources.lib.addon.plugin import PLUGINPATH, convert_type, convert_trakt_type
from resources.lib.addon.setutils import del_empty_keys, get_params


def _sort_itemlist(items, sort_by=None, sort_how=None, trakt_type=None):
    reverse = True if sort_how == 'desc' else False
    if sort_by == 'unsorted':
        return items
    elif sort_by == 'rank':
        return sorted(items, key=lambda i: i.get('rank', 0), reverse=reverse)
    elif sort_by == 'plays':
        return sorted(items, key=lambda i: i.get('plays', 0), reverse=reverse)
    elif sort_by == 'watched':
        return sorted(items, key=lambda i: i.get('last_watched_at', ''), reverse=reverse)
    elif sort_by == 'paused':
        return sorted(items, key=lambda i: i.get('paused_at', ''), reverse=reverse)
    elif sort_by == 'added':
        return sorted(items, key=lambda i: i.get('listed_at', ''), reverse=reverse)
    elif sort_by == 'title':
        return sorted(items, key=lambda i: i.get(trakt_type or i.get('type'), {}).get('title', ''), reverse=reverse)
    elif sort_by == 'year':
        return sorted(items, key=lambda i: i.get(trakt_type or i.get('type'), {}).get('year', 0), reverse=reverse)
    elif sort_by == 'released':
        return sorted(items, key=lambda i: i.get(trakt_type or i.get('type'), {}).get('first_aired', '')
                      if (trakt_type or i.get('type')) in ['show', 'episode']
                      else i.get(trakt_type or i.get('type'), {}).get('released', ''), reverse=reverse)
    elif sort_by == 'runtime':
        return sorted(items, key=lambda i: i.get(trakt_type or i.get('type'), {}).get('runtime', 0), reverse=reverse)
    elif sort_by == 'popularity':
        return sorted(items, key=lambda i: i.get(trakt_type or i.get('type'), {}).get('comment_count', 0), reverse=reverse)
    elif sort_by == 'percentage':
        return sorted(items, key=lambda i: i.get(trakt_type or i.get('type'), {}).get('rating', 0), reverse=reverse)
    elif sort_by == 'votes':
        return sorted(items, key=lambda i: i.get(trakt_type or i.get('type'), {}).get('votes', 0), reverse=reverse)
    elif sort_by == 'random':
        random.shuffle(items)
        return items
    return sorted(items, key=lambda i: i.get('listed_at', ''), reverse=True)


def _get_item_title(item):
    if 'title' in item:
        return item['title']
    if 'name' in item:
        return item['name']


def _get_item_infolabels(item, item_type=None, infolabels=None, show=None):
    infolabels = infolabels or {}
    infolabels['title'] = _get_item_title(item)
    infolabels['year'] = item.get('year')
    infolabels['mediatype'] = convert_type(convert_trakt_type(item_type), 'dbtype')
    if show:
        infolabels['tvshowtitle'] = show.get('title') or ''
    if item_type == 'episode':
        infolabels['episode'] = item.get('number')
        infolabels['season'] = item.get('season')
    if item_type == 'season':
        infolabels['season'] = item.get('number')
    return del_empty_keys(infolabels)


def _get_item_infoproperties(item, item_type=None, infoproperties=None, show=None):
    infoproperties = infoproperties or {}
    infoproperties['tmdb_type'] = convert_trakt_type(item_type)
    return del_empty_keys(infoproperties)


def _get_item_unique_ids(item, unique_ids=None, prefix=None, show=None):
    prefix = prefix or ''
    unique_ids = unique_ids or {}
    for k, v in item.get('ids', {}).items():
        unique_ids[u'{}{}'.format(prefix, k)] = v
    if show:
        unique_ids = _get_item_unique_ids(show, unique_ids, prefix='tvshow.')
        unique_ids['tmdb'] = show.get('ids', {}).get('tmdb')
    return del_empty_keys(unique_ids)


def _get_item_info(item, item_type=None, base_item=None, check_tmdb_id=True, params_def=None):
    base_item = base_item or {}
    item_info = item.get(item_type, {}) or item
    show_item = item.get('show') if item_type == 'episode' else None
    if not item_info:
        return base_item
    if check_tmdb_id and not item_info.get('ids', {}).get('tmdb'):
        if not show_item or not show_item.get('ids', {}).get('tmdb'):
            return base_item
    base_item['label'] = _get_item_title(item_info) or ''
    base_item['infolabels'] = _get_item_infolabels(item_info, item_type=item_type, infolabels=base_item.get('infolabels', {}), show=show_item)
    base_item['infoproperties'] = _get_item_infoproperties(item_info, item_type=item_type, infoproperties=base_item.get('infoproperties', {}), show=show_item)
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
        self.configured = {'items': [], 'headers': headers or {}}

    def sort_items(self, sort_by=None, sort_how=None):
        """ (Re)Sorts items and returns sorted items """
        self.sort_by = sort_by or self.sort_by
        self.sort_how = sort_how or self.sort_how
        self.items = _sort_itemlist(self.items, self.sort_by, self.sort_how, self.trakt_type)
        return self.items

    def configure_items(self, permitted_types=None, params_def=None):
        """ (Re)Configures items for passing to listitem class in container and returns configured items """
        for i in self.items:
            i_type = self.trakt_type or i.get('type', None)
            if permitted_types and i_type not in permitted_types:
                continue
            item = _get_item_info(i, item_type=i_type, params_def=params_def)
            if not item:
                continue
            # Also add item to a list only containing that item type
            # Useful if we need to only get one type of item from a mixed list (e.g. only "movies")
            self.configured.setdefault(u'{}s'.format(i_type), []).append(item)
            self.configured['items'].append(item)
        return self.configured

    def build_items(self, sort_by=None, sort_how=None, permitted_types=None, params_def=None):
        """ Sorts and Configures Items """
        self.sort_items(sort_by, sort_how)
        self.configure_items(permitted_types, params_def)
        return self.configured
