from resources.lib.addon.plugin import get_language, get_setting
from resources.lib.addon.parser import try_int, del_empty_keys
from resources.lib.addon.consts import CACHE_EXTENDED, ITER_PROPS_MAX
from resources.lib.api.request import RequestAPI

EN_FALLBACK = get_setting('fanarttv_enfallback')
API_URL = 'https://webservice.fanart.tv/v3'
NO_LANGUAGE = ['keyart', 'fanart']
ARTWORK_TYPES = {
    'movies': {
        'poster': ['movieposter'],
        'fanart': ['moviebackground'],
        'landscape': ['moviethumb'],
        'banner': ['moviebanner'],
        'clearart': ['hdmovieclearart', 'movieclearart'],
        'clearlogo': ['hdmovielogo', 'movielogo'],
        'discart': ['moviedisc'],
        'keyart': ['movieposter']},
    'tv': {
        'poster': ['tvposter'],
        'fanart': ['showbackground'],
        'landscape': ['tvthumb'],
        'banner': ['tvbanner'],
        'clearart': ['hdclearart', 'clearart'],
        'clearlogo': ['hdtvlogo', 'clearlogo'],
        'characterart': ['characterart']},
    'season': {
        'poster': ['seasonposter', 'tvposter'],
        'fanart': ['showbackground'],
        'landscape': ['seasonthumb', 'tvthumb'],
        'banner': ['seasonbanner', 'tvbanner']},
    'season_only': {
        'poster': ['seasonposter'],
        'landscape': ['seasonthumb'],
        'banner': ['seasonbanner']}
}


def add_extra_art(source, output=None):
    output = output or {}
    if not source:
        return output
    output.update({f'fanart{x}': i['url'] for x, i in enumerate(source, 1) if i.get('url') and x <= ITER_PROPS_MAX})
    return output


class FanartTV(RequestAPI):
    def __init__(
            self,
            api_key='fcca59bee130b70db37ee43e63f8d6c1',
            client_key=get_setting('fanarttv_clientkey', 'str'),
            language=get_language(),
            cache_only=False,
            cache_refresh=False,
            delay_write=False):
        super(FanartTV, self).__init__(
            req_api_name='FanartTV',
            req_api_url=API_URL,
            req_api_key=f'api_key={api_key}',
            delay_write=delay_write)
        self.req_api_key = f'api_key={api_key}' if api_key else self.req_api_key
        self.req_api_key = f'{self.req_api_key}&client_key={client_key}' if client_key else self.req_api_key
        self.language = language[:2] if language else 'en'
        self.cache_only = cache_only
        self.cache_refresh = cache_refresh
        self.quick_request = {'movies': {}, 'tv': {}}
        self.req_strip.append((f'&client_key={client_key}', ''))

    def get_all_artwork(self, ftv_id, ftv_type, season=None, artlist_type=None, season_type=None):
        """
        ftv_type can be 'movies' 'tv'
        ftv_id is tmdb_id|imdb_id for movies and tvdb_id for tv
        """
        def get_artwork_type(key, get_lang=True):
            if not key:
                return
            languages = [get_lang if isinstance(get_lang, str) and get_lang != 'all' else self.language] if get_lang else ['00', None, '']
            data = (j for i in artwork_types.get(key, []) for j in request.get(i, []) if get_lang == 'all' or j.get('lang') in languages)
            if season is not None:
                allowlist = [try_int(season), 'all']
                data = (i for i in data if try_int(i.get('season'), fallback='all') in allowlist)
            return data

        def get_best_artwork(key, get_lang=True):
            response = get_artwork_type(key, get_lang)
            try:
                return next(response).get('url', '')
            except StopIteration:
                if isinstance(get_lang, str):
                    return
                if not get_lang and (key in NO_LANGUAGE or not EN_FALLBACK):
                    return
            return get_best_artwork(key, False if get_lang else 'en')  # Try again with no language OR all languages

        def get_artwork(key, get_list=False, get_lang=True):
            func = get_artwork_type if get_list else get_best_artwork
            return func(key, get_lang)

        # __main__
        if not ftv_type or not ftv_id:
            return {}
        request = self.quick_request[ftv_type].get(ftv_id)
        if not request:
            request = self.quick_request[ftv_type][ftv_id] = self.get_request(
                ftv_type, ftv_id,
                cache_force=7,  # Force dummy request caching to prevent rerequesting 404s
                cache_fallback={'dummy': None},
                cache_days=CACHE_EXTENDED,
                cache_only=self.cache_only,
                cache_refresh=self.cache_refresh)
        if not request or 'dummy' in request:
            return {}
        artwork_types = ARTWORK_TYPES.get(ftv_type if season is None else season_type or 'season', {})
        if artlist_type:
            return get_artwork(artlist_type, get_list=True, get_lang='all') or []
        artwork_data = del_empty_keys({i: get_artwork(i, get_lang=i not in NO_LANGUAGE) for i in artwork_types})
        return add_extra_art(get_artwork('fanart', get_list=True, get_lang=False), artwork_data)
