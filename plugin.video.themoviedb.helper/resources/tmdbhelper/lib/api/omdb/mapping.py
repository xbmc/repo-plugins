from tmdbhelper.lib.api.mapping import _ItemMapper, get_empty_item
from jurialmunkey.parser import get_between_strings


class ItemMapper(_ItemMapper):
    def __init__(self):
        self.blacklist = ['N/A', '0.0', '0']
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
            'awards': [{
                'keys': [('infoproperties', 'awards')]}, {
                # ---
                'keys': [('infoproperties', 'oscar_wins')],
                'func': lambda v: get_between_strings(v or '', 'Won ', ' Oscar')}, {
                # ---
                'keys': [('infoproperties', 'emmy_wins')],
                'func': lambda v: get_between_strings(v or '', 'Won ', ' Primetime Emmy')}, {
                # ---
                'keys': [('infoproperties', 'award_wins')],
                'func': lambda v: get_between_strings(v or '', '.* ', ' win') or get_between_strings(v or '', '', ' win')}, {
                # ---
                'keys': [('infoproperties', 'oscar_nominations')],
                'func': lambda v: get_between_strings(v or '', 'Nominated for ', ' Oscar')}, {
                # ---
                'keys': [('infoproperties', 'emmy_nominations')],
                'func': lambda v: get_between_strings(v or '', 'Nominated for ', ' Primetime Emmy')}, {
                # ---
                'keys': [('infoproperties', 'award_nominations')],
                'func': lambda v: get_between_strings(v or '', 'wins? & ', ' nomination') or get_between_strings(v or '', '', ' nomination')
            }],
            'tomatoReviews': [{
                'keys': [('infoproperties', 'rottentomatoes_reviewstotal')],
                'type': float,
                'func': lambda v: f'{v:0,.0f}'
            }],
            'tomatoFresh': [{
                'keys': [('infoproperties', 'rottentomatoes_reviewsfresh')],
                'type': float,
                'func': lambda v: f'{v:0,.0f}'
            }],
            'tomatoRotten': [{
                'keys': [('infoproperties', 'rottentomatoes_reviewsrotten')],
                'type': float,
                'func': lambda v: f'{v:0,.0f}'
            }],
            'tomatoUserReviews': [{
                'keys': [('infoproperties', 'rottentomatoes_userreviews')],
                'type': float,
                'func': lambda v: f'{v:0,.0f}'
            }]
        }
        self.standard_map = {
            'metascore': ('infoproperties', 'metacritic_rating'),
            'imdbRating': ('infoproperties', 'imdb_rating'),
            'imdbVotes': ('infoproperties', 'imdb_votes'),
            'tomatoMeter': ('infoproperties', 'rottentomatoes_rating'),
            'tomatoImage': ('infoproperties', 'rottentomatoes_image'),
            'tomatoConsensus': ('infoproperties', 'rottentomatoes_consensus'),
            'tomatoUserMeter': ('infoproperties', 'rottentomatoes_usermeter')
        }

    def get_info(self, info_item, tmdb_type=None, base_item=None, **kwargs):
        item = get_empty_item()
        item = self.map_item(item, info_item)
        item = self.add_base(item, base_item, tmdb_type)
        return item
