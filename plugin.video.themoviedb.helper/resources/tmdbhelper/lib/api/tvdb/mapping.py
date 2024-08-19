from tmdbhelper.lib.api.mapping import _ItemMapper, get_empty_item
from tmdbhelper.lib.addon.plugin import ADDONPATH


TVDB_ICON = f'{ADDONPATH}/resources/icons/tvdb/tvdb.png'


class ItemMapper(_ItemMapper):
    def __init__(self):
        """ Mapping dictionary
        keys:       list of tuples containing parent and child key to add value. [('parent', 'child')]
                    parent keys: art, unique_ids, infolabels, infoproperties, params
                    use UPDATE_BASEKEY for child key to update parent with a dict
        func:       function to call to manipulate values (omit to skip and pass value directly)
        (kw)args:   list/dict of args/kwargs to pass to func.
                    func is also always passed v as first argument
        type:       int, float, str - convert v to type using try_type(v, type)
        extend:     set True to add to existing list - leave blank to overwrite exiting list
        subkeys:    list of sub keys to get for v - i.e. v.get(subkeys[0], {}).get(subkeys[1]) etc.
                    note that getting subkeys sticks for entire loop so do other ops on base first if needed

        use standard_map for direct one-to-one mapping of v onto single property tuple
        """
        self.blacklist = ['N/A', '0.0', '0']
        self.advanced_map = {
            'firstAired': [{
                'keys': [('infolabels', 'premiered')]}, {
                'keys': [('infolabels', 'year')],
                'func': lambda v: v[0:4]
            }],
        }
        self.standard_map = {
            'id': ('unique_ids', 'tvdb'),
            'slug': ('unique_ids', 'tvdb_slug'),
            'name': ('infolabels', 'originaltitle'),
            # 'image': ('art', 'poster'),
            'year': ('infolabels', 'year'),
            'mediatype': ('infolabels', 'mediatype'),
        }

    def get_type(self, info_item):
        if info_item.get('series'):
            info = info_item['series']
            info['mediatype'] = 'tvshow'
            return info
        if info_item.get('movie'):
            info = info_item['movie']
            info['mediatype'] = 'movie'
            return info

    def finalise(self, item):
        if not item['art'].get('icon') and not item['art'].get('poster'):
            item['art']['icon'] = TVDB_ICON
        item['label'] = item['infolabels'].get('originaltitle') or ''
        return item

    def get_info(self, info_item, tmdb_type=None, base_item=None, **kwargs):
        item = get_empty_item()
        item = self.map_item(item, info_item)
        item = self.add_base(item, base_item, tmdb_type)
        item = self.finalise(item)
        return item
