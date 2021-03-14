from resources.lib.api.request import RequestAPI
from resources.lib.addon.plugin import ADDON
from resources.lib.addon.setutils import del_empty_keys
from resources.lib.omdb.mapping import ItemMapper


class OMDb(RequestAPI):
    def __init__(self, api_key=ADDON.getSettingString('omdb_apikey')):
        super(OMDb, self).__init__(
            req_api_key=u'apikey={0}'.format(api_key),
            req_api_name='OMDb',
            req_api_url='http://www.omdbapi.com/')

    def get_request_item(self, imdb_id=None, title=None, year=None, tomatoes=True, fullplot=True, cache_only=False):
        kwparams = {}
        kwparams['i'] = imdb_id
        kwparams['t'] = title
        kwparams['y'] = year
        kwparams['plot'] = 'full' if fullplot else 'short'
        kwparams['tomatoes'] = 'True' if tomatoes else None
        kwparams = del_empty_keys(kwparams)
        request = self.get_request_lc(is_xml=True, cache_only=cache_only, r='xml', **kwparams)
        if request and request.get('root') and not request.get('root').get('response') == 'False':
            request = request.get('root').get('movie')[0]
        else:
            request = {}
        return request

    def get_ratings_awards(self, imdb_id=None, title=None, year=None, cache_only=False, base_item=None):
        request = self.get_request_item(imdb_id=imdb_id, title=title, year=year, cache_only=cache_only)
        return ItemMapper().get_info(request, base_item=base_item)
