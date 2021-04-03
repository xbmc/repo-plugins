import random


def random_from_list(items, remove_next_page=True):
    if not items or not isinstance(items, list) or len(items) < 2:
        return
    item = random.choice(items)
    if remove_next_page and isinstance(item, dict) and 'next_page' in item:
        return random_from_list(items, remove_next_page=True)
    return item


def dict_to_list(items, key):
    items = items or []
    return [i[key] for i in items if i.get(key)]


def _quick_copy(v):
    if isinstance(v, dict):
        return v.copy()
    return v


def quick_copy(d):
    return {k: _quick_copy(v) for k, v in d.items()}


def merge_two_dicts(x, y, reverse=False, deep=False):
    xx = y or {} if reverse else x or {}
    yy = x or {} if reverse else y or {}
    z = xx.copy()  # start with x's keys and values
    if not deep:   # modifies z with y's keys and values
        z.update(yy)
        return z
    for k, v in yy.items():
        if isinstance(v, dict):
            merge_two_dicts(z.setdefault(k, {}), v, reverse=reverse, deep=True)
        elif v:
            z[k] = v
    return z


def merge_two_items(base_item, item):
    item = item or {}
    base_item = base_item or {}
    item['stream_details'] = merge_two_dicts(base_item.get('stream_details', {}), item.get('stream_details', {}))
    item['params'] = merge_two_dicts(base_item.get('params', {}), item.get('params', {}))
    item['infolabels'] = merge_two_dicts(base_item.get('infolabels', {}), item.get('infolabels', {}))
    item['infoproperties'] = merge_two_dicts(base_item.get('infoproperties', {}), item.get('infoproperties', {}))
    item['art'] = merge_two_dicts(base_item.get('art', {}), item.get('art', {}))
    item['unique_ids'] = merge_two_dicts(base_item.get('unique_ids', {}), item.get('unique_ids', {}))
    item['cast'] = item.get('cast') or base_item.get('cast') or []
    return item


# @timer_report('del_empty_keys')
def del_empty_keys(d, values=[]):
    values += [None, '']
    return {k: v for k, v in d.items() if v not in values}


def find_dict_in_list(list_of_dicts, key, value):
    return [list_index for list_index, dic in enumerate(list_of_dicts) if dic.get(key) == value]


def iter_props(items, property_name, infoproperties=None, func=None, **kwargs):
    infoproperties = infoproperties or {}
    if not items or not isinstance(items, list):
        return infoproperties
    for x, i in enumerate(items, start=1):
        for k, v in kwargs.items():
            infoproperties[u'{}.{}.{}'.format(property_name, x, k)] = func(i.get(v)) if func else i.get(v)
        if x >= 10:
            break
    return infoproperties


def get_params(item, tmdb_type, tmdb_id=None, params=None, definition=None, base_tmdb_type=None):
    params = params or {}
    tmdb_id = tmdb_id or item.get('id')
    if params == -1:
        return {}
    definition = definition or {'info': 'details', 'tmdb_type': '{tmdb_type}', 'tmdb_id': '{tmdb_id}'}
    for k, v in definition.items():
        params[k] = v.format(tmdb_type=tmdb_type, tmdb_id=tmdb_id, base_tmdb_type=base_tmdb_type, **item)
    return del_empty_keys(params)  # TODO: Is this necessary??!


def split_items(items, separator='/'):
    separator = u' {} '.format(separator)
    if items and separator in items:
        items = items.split(separator)
    items = [items] if not isinstance(items, list) else items  # Make sure we return a list to prevent a string being iterated over characters
    return items
