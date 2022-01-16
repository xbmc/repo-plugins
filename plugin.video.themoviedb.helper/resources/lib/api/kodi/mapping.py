from resources.lib.api.mapping import _ItemMapper, get_empty_item


class ItemMapper(_ItemMapper):
    def __init__(self, key=None):
        self.key = key
        self.blacklist = []
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
        self.advanced_map = {
            'premiered': [{
                'keys': [('infolabels', 'premiered')]}, {
                'keys': [('infolabels', 'year')],
                'func': lambda v: v[0:4]
            }],
            'playcount': [{
                'keys': [('infolabels', 'playcount')],
                'type': int}, {
                # ---
                'keys': [('infolabels', 'overlay')],
                'func': lambda v: 5 if self.key in ['movie', 'episode'] and v > 0 else 4,
                'type': int
            }],
            'ratings': [{
                'subkeys': ['metacritic', 'rating'],
                'keys': [('infoproperties', 'metacritic_rating')],
                'type': float,
                'func': lambda v: f'{v:.1f}'}, {
                # ---
                'subkeys': ['imdb', 'rating'],
                'keys': [('infoproperties', 'imdb_rating')],
                'type': float,
                'func': lambda v: f'{v:.1f}'}, {
                # ---
                'subkeys': ['themoviedb', 'rating'],
                'keys': [('infoproperties', 'tmdb_rating')],
                'type': float,
                'func': lambda v: f'{v:.1f}'}, {
                # ---
                'subkeys': ['imdb', 'votes'],
                'keys': [('infoproperties', 'imdb_votes')],
                'type': float,
                'func': lambda v: f'{v:0,.0f}'}, {
                # ---
                'subkeys': ['themoviedb', 'votes'],
                'keys': [('infoproperties', 'tmdb_votes')],
                'type': float,
                'func': lambda v: f'{v:0,.0f}'
            }],
        }
        self.standard_map = {
            'dbid': ('infolabels', 'dbid'),
            'genre': ('infolabels', 'genre'),
            'country': ('infolabels', 'country'),
            'episode': ('infolabels', 'episode'),
            'season': ('infolabels', 'season'),
            'sortepisode': ('infolabels', 'sortepisode'),
            'sortseason': ('infolabels', 'sortseason'),
            'showlink': ('infolabels', 'showlink'),
            'top250': ('infolabels', 'top250'),
            'setid': ('infolabels', 'setid'),
            'tracknumber': ('infolabels', 'tracknumber'),
            'rating': ('infolabels', 'rating'),
            'userrating': ('infolabels', 'userrating'),
            'overlay': ('infolabels', 'overlay'),
            'director': ('infolabels', 'director'),
            'mpaa': ('infolabels', 'mpaa'),
            'plot': ('infolabels', 'plot'),
            'plotoutline': ('infolabels', 'plotoutline'),
            'title': ('infolabels', 'title'),
            'originaltitle': ('infolabels', 'originaltitle'),
            'sorttitle': ('infolabels', 'sorttitle'),
            'duration': ('infolabels', 'duration'),
            'studio': ('infolabels', 'studio'),
            'tagline': ('infolabels', 'tagline'),
            'writer': ('infolabels', 'writer'),
            'tvshowtitle': ('infolabels', 'tvshowtitle'),
            'status': ('infolabels', 'status'),
            'set': ('infolabels', 'set'),
            'setoverview': ('infolabels', 'setoverview'),
            'tag': ('infolabels', 'tag'),
            'imdbnumber': ('infolabels', 'imdbnumber'),
            'code': ('infolabels', 'code'),
            'aired': ('infolabels', 'aired'),
            'credits': ('infolabels', 'credits'),
            'lastplayed': ('infolabels', 'lastplayed'),
            'album': ('infolabels', 'album'),
            'artist': ('infolabels', 'artist'),
            'votes': ('infolabels', 'votes'),
            'path': ('infolabels', 'file'),
            'trailer': ('infolabels', 'trailer'),
            'dateadded': ('infolabels', 'dateadded'),
            'watchedepisodes': ('infoproperties', 'watchedepisodes')
        }

    def get_info(self, info_item, tmdb_type=None, base_item=None, **kwargs):
        item = get_empty_item()
        item = self.map_item(item, info_item)
        item = self.add_base(item, base_item, tmdb_type)
        item['label'] = info_item.get('label') or ''
        item['cast'] = info_item.get('cast') or []
        item['art'] = info_item.get('art') or {}
        item['stream_details'] = info_item.get('streamdetails') or {}
        item['unique_ids'] = info_item.get('uniqueid') or {}
        return item
