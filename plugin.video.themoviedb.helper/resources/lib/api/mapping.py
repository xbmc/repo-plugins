from resources.lib.addon.parser import try_type

UPDATE_BASEKEY = 1


def get_empty_item():
    return {
        'art': {},
        'cast': [],
        'infolabels': {},
        'infoproperties': {},
        'unique_ids': {},
        'params': {},
        'context_menu': []}


def set_show(item, base_item=None, is_season=False):
    if not base_item:
        return item
    item['art'].update(
        {f'tvshow.{k}': v for k, v in base_item.get('art', {}).items()})
    item['unique_ids'].update(
        {f'tvshow.{k}': v for k, v in base_item.get('unique_ids', {}).items()})
    item['infoproperties'].update(
        {f'{"season." if is_season else "tvshow."}{k}': v for k, v in base_item.get('infolabels', {}).items() if type(v) not in [dict, list, tuple]})
    item['infolabels']['tvshowtitle'] = base_item['infolabels'].get('tvshowtitle') or base_item['infolabels'].get('title')
    item['unique_ids']['tmdb'] = item['unique_ids'].get('tvshow.tmdb')
    return item


class _ItemMapper(object):
    def add_base(self, item, base_item=None, tmdb_type=None, key_blacklist=[], is_season=False):
        if not base_item:
            return item
        for d in ['infolabels', 'infoproperties', 'art']:
            for k, v in base_item.get(d, {}).items():
                if not v or item[d].get(k) is not None:
                    continue
                if k in key_blacklist:
                    continue
                item[d][k] = v
        if tmdb_type in ['season', 'episode', 'tv']:
            return set_show(item, base_item, is_season=is_season)
        return item

    def map_item(self, item, i):
        sm = self.standard_map or {}
        am = self.advanced_map or {}

        # Iterate over item retrieved from api list
        for k, pv in i.items():
            # Skip empty objects
            if not pv and pv != 0:
                continue
            # Skip blacklist values
            if pv in self.blacklist:
                continue
            # Simple mapping is quicker so do that first if we can
            if k in sm:
                item[sm[k][0]][sm[k][1]] = pv
                continue
            # Check key is in advanced map before trying to map it
            if k not in am:
                continue
            # Iterate over list of dictionaries
            for d in am[k]:
                # Make a quick copy of object
                if isinstance(pv, dict):
                    v = pv.copy()
                elif isinstance(pv, list):
                    v = pv[:]
                else:
                    v = pv
                # Get subkeys
                if 'subkeys' in d:
                    for ck in d['subkeys']:
                        v = v.get(ck) or {}
                    if not v:
                        continue
                # Run through type conversion
                if 'type' in d:
                    v = try_type(v, d['type'])
                # Run through func
                if 'func' in d:
                    v = d['func'](v, *d.get('args', []), **d.get('kwargs', {}))
                # Check not empty
                if not v and v != 0:
                    continue
                # Map value onto item dict parent/child keys
                for p, c in d['keys']:
                    if c == UPDATE_BASEKEY:
                        item[p].update(v)
                    elif c is None:
                        item[p] = v
                    elif 'extend' in d and isinstance(item[p].get(c), list) and isinstance(v, list):
                        item[p][c] += v
                    else:
                        item[p][c] = v
        return item
