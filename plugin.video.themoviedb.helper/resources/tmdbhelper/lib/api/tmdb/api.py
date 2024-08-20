from tmdbhelper.lib.addon.plugin import get_mpaa_prefix, get_language, get_setting
from tmdbhelper.lib.addon.consts import CACHE_SHORT, CACHE_MEDIUM
from tmdbhelper.lib.api.request import RequestAPI
from tmdbhelper.lib.api.tmdb.mapping import ItemMapper
from tmdbhelper.lib.api.tmdb.content import TMDbMethods
from tmdbhelper.lib.api.api_keys.tmdb import API_KEY


ARTWORK_QUALITY = get_setting('artwork_quality', 'int')
ARTLANG_FALLBACK = True if get_setting('fanarttv_enfallback') and not get_setting('fanarttv_secondpref') else False
API_URL = 'https://api.themoviedb.org/3' if not get_setting('use_alternate_api_url') else 'https://api.tmdb.org/3'
APPEND_TO_RESPONSE = 'credits,images,release_dates,content_ratings,external_ids,movie_credits,tv_credits,keywords,reviews,videos,watch/providers'


class TMDb(RequestAPI, TMDbMethods):

    api_key = API_KEY

    def __init__(
            self,
            api_key=None,
            language=get_language(),
            mpaa_prefix=get_mpaa_prefix(),
            page_length=1):
        api_key = api_key or self.api_key

        super(TMDb, self).__init__(
            req_api_name='TMDb',
            req_api_url=API_URL,
            req_api_key=f'api_key={api_key}')
        self.language = language
        self.mpaa_prefix = mpaa_prefix
        self.append_to_response = APPEND_TO_RESPONSE
        self.page_length = max(get_setting('pagemulti_tmdb', 'int'), page_length)
        TMDb.api_key = api_key

    @property
    def req_strip(self):
        req_strip_add = [
            (self.append_to_response, ''),
            (self.req_language, f'{self.iso_language}{"_en" if ARTLANG_FALLBACK else ""}')
        ]
        try:
            return self._req_strip + req_strip_add
        except AttributeError:
            self._req_strip = [
                (self.req_api_url, self.req_api_name),
                (self.req_api_key, ''),
                ('is_xml=False', ''),
                ('is_xml=True', '')
            ]
            return self._req_strip + req_strip_add

    @req_strip.setter
    def req_strip(self, value):
        self._req_strip = value

    @property
    def req_language(self):
        return f'{self.iso_language}-{self.iso_country}&include_image_language={self.iso_language},null{",en" if ARTLANG_FALLBACK else ""}&include_video_language={self.iso_language},null,en'

    @property
    def iso_language(self):
        return self.language[:2]

    @property
    def iso_country(self):
        return self.language[-2:]

    @property
    def iso_region(self):
        return None if self.setting_ignore_regionreleasefilter else self.iso_country

    @property
    def setting_ignore_regionreleasefilter(self):
        try:
            return self._setting_ignore_regionreleasefilter
        except AttributeError:
            self._setting_ignore_regionreleasefilter = get_setting('ignore_regionreleasefilter')
            return self._setting_ignore_regionreleasefilter

    @property
    def genres(self):
        try:
            return self._genres
        except AttributeError:
            cache_name = f'TMDb.GenreLookup.v2.{self.language}'
            self._genres = self._cache.use_cache(self.get_genres, cache_name=cache_name)
            return self._genres

    @property
    def mapper(self):
        try:
            return self._mapper
        except AttributeError:
            self._mapper = ItemMapper(self.language, self.mpaa_prefix, self.genres)
            return self._mapper

    @staticmethod
    def get_url_separator(separator=None):
        if separator == 'AND':
            return '%2C'
        elif separator == 'OR':
            return '%7C'
        elif not separator:
            return '%2C'
        else:
            return False

    @staticmethod
    def get_paginated_items(items, limit=None, page=1, total_pages=None):
        from jurialmunkey.parser import try_int
        if total_pages and try_int(page) < try_int(total_pages):
            items.append({'next_page': try_int(page) + 1})
            return items
        if limit is not None:
            from tmdbhelper.lib.items.pages import PaginatedItems
            paginated_items = PaginatedItems(items, page=page, limit=limit)
            return paginated_items.items + paginated_items.next_page
        return items

    def get_response_json(self, *args, **kwargs):
        kwargs['region'] = self.iso_region
        kwargs['language'] = self.req_language
        return self.get_api_request_json(self.get_request_url(*args, **kwargs))

    def get_request_sc(self, *args, **kwargs):
        """ Get API request using the short cache """
        kwargs['cache_days'] = CACHE_SHORT
        kwargs['region'] = self.iso_region
        kwargs['language'] = self.req_language
        return self.get_request(*args, **kwargs)

    def get_request_lc(self, *args, **kwargs):
        """ Get API request using the long cache """
        kwargs['cache_days'] = CACHE_MEDIUM
        kwargs['region'] = self.iso_region
        kwargs['language'] = self.req_language
        return self.get_request(*args, **kwargs)
