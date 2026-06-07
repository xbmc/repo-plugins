from resources.lib.addon.plugin import get_setting
from resources.lib.addon.parser import del_empty_keys, merge_two_dicts
from resources.lib.api.request import RequestAPI
from resources.lib.api.omdb.mapping import ItemMapper


IMDB_KEYPAIRS = [('infolabels', 'imdbnumber'), ('unique_ids', 'imdb'), ('unique_ids', 'tvshow.imdb')]


class OMDb(RequestAPI):
    def __init__(self, api_key=None, delay_write=False):
        super(OMDb, self).__init__(
            req_api_key=f'apikey={api_key or get_setting("omdb_apikey", "str")}',
            req_api_name='OMDb',
            req_api_url='https://www.omdbapi.com/',
            delay_write=delay_write)

    def get_request_item(self, imdb_id=None, title=None, year=None, tomatoes=True, fullplot=True, cache_only=False):
        kwparams = {}
        kwparams['i'] = imdb_id
        kwparams['t'] = title
        kwparams['y'] = year
        kwparams['plot'] = 'full' if fullplot else 'short'
        kwparams['tomatoes'] = 'True' if tomatoes else None
        kwparams = del_empty_keys(kwparams)
        request = self.get_request_lc(is_xml=True, cache_only=cache_only, r='xml', **kwparams)
        try:
            request = request['root']['movie'][0]
        except (KeyError, TypeError, AttributeError):
            request = {}
        return request

    def get_ratings_awards(self, imdb_id=None, title=None, year=None, cache_only=False, base_item=None):
        request = self.get_request_item(imdb_id=imdb_id, title=title, year=year, cache_only=cache_only)
        return ItemMapper().get_info(request, base_item=base_item)

    def _get_item_value(self, item, key_pairs: list = None, starts_with: str = None):
        for i, j in key_pairs:
            try:
                value = item[i][j]
                if not value:
                    continue
                if starts_with and not value.startswith(starts_with):
                    continue
                return value
            except (KeyError, AttributeError):
                continue

    def get_item_ratings(self, item, cache_only=False):
        """ Get ratings for an item using IMDb lookup """
        if not item:
            return
        imdb_id = self._get_item_value(item, key_pairs=IMDB_KEYPAIRS, starts_with='tt')
        if not imdb_id:
            return item
        ratings = self.get_ratings_awards(imdb_id=imdb_id, cache_only=cache_only)
        item['infoproperties'] = merge_two_dicts(item.get('infoproperties', {}), ratings.get('infoproperties', {}))
        return item
