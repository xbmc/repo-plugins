from jurialmunkey.parser import del_empty_keys, merge_two_dicts
from tmdbhelper.lib.api.request import RequestAPI
from tmdbhelper.lib.api.omdb.mapping import ItemMapper
from tmdbhelper.lib.api.api_keys.omdb import API_KEY


def translate_xml(request):
    """ Workaround wrapper for broken ElementTree in Python 3.11.1 """

    if not request:
        return

    from xml.dom.minidom import parseString
    from xml.parsers.expat import ExpatError

    try:
        r = parseString(request.text)
        d = {k: v for k, v in r.firstChild.firstChild.attributes.items() if k and v}
    except AttributeError:
        return
    except ExpatError:
        return

    return {'root': {'movie': [d]}}


class OMDb(RequestAPI):

    api_key = API_KEY

    def __init__(self, api_key=None):
        api_key = api_key or self.api_key

        super(OMDb, self).__init__(
            req_api_key=f'apikey={api_key}',
            req_api_name='OMDb',
            req_api_url='https://www.omdbapi.com/')
        self.translate_xml = translate_xml  # Temp monkey patch bandaid for broken ElementTree. Remove after upstream fix.
        self._error_notification = False  # Override user settings and always suppress OMDb error notifications since it times-out a lot.
        OMDb.api_key = api_key

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

    def get_item_ratings(self, item, cache_only=False):
        """ Get ratings for an item using IMDb lookup """
        if not item:
            return

        def _get_item_value(item, key_pairs: list = None, starts_with: str = None):
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

        imdb_id = _get_item_value(item, key_pairs=[('infolabels', 'imdbnumber'), ('unique_ids', 'imdb')], starts_with='tt')
        if not imdb_id:
            return item
        ratings = self.get_ratings_awards(imdb_id=imdb_id, cache_only=cache_only)
        imdb_tv_id = _get_item_value(item, key_pairs=[('unique_ids', 'tvshow.tvshow.imdb'), ('unique_ids', 'tvshow.imdb')], starts_with='tt')
        if imdb_tv_id and imdb_tv_id != imdb_id:
            # Also merge base tv show details
            tv_ratings = self.get_ratings_awards(imdb_id=imdb_tv_id, cache_only=cache_only)
            ratings['infoproperties'] = merge_two_dicts(tv_ratings.get('infoproperties', {}), ratings.get('infoproperties', {}))
        item['infoproperties'] = merge_two_dicts(item.get('infoproperties', {}), ratings.get('infoproperties', {}))
        return item
