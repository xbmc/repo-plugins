from tmdbhelper.lib.api.request import RequestAPI
from tmdbhelper.lib.addon.consts import CACHE_SHORT, CACHE_MEDIUM
from tmdbhelper.lib.api.api_keys.tvdb import API_KEY, USER_TOKEN


API_URL = 'https://api4.thetvdb.com/v4'


def is_authorized(func):
    def wrapper(self, *args, **kwargs):
        if not self._token:
            return
        return func(self, *args, **kwargs)
    return wrapper


class TVDb(RequestAPI):

    api_key = API_KEY
    user_token = USER_TOKEN

    def __init__(
            self,
            api_key=None,
            user_token=None):
        super(TVDb, self).__init__(
            req_api_name='TVDb',
            req_api_url=API_URL)
        self.set_token()
        TVDb.api_key = api_key or self.api_key
        TVDb.user_token = user_token or self.user_token

    @property
    def mapper(self):
        try:
            return self._mapper
        except AttributeError:
            from tmdbhelper.lib.api.tvdb.mapping import ItemMapper
            self._mapper = ItemMapper()
            return self._mapper

    def set_token(self):
        self._token = self.get_token()
        self.headers = {'Authorization': f'Bearer {self._token}'}

    @is_authorized
    def get_request_sc(self, *args, **kwargs):
        """ Get API request using the short cache """
        kwargs['cache_days'] = CACHE_SHORT
        data = self.get_request(*args, **kwargs)
        try:
            data = data['data']
        except (KeyError, AttributeError, TypeError):
            return
        return data

    @is_authorized
    def get_request_lc(self, *args, **kwargs):
        """ Get API request using the long cache """
        kwargs['cache_days'] = CACHE_MEDIUM
        data = self.get_request(*args, **kwargs)
        try:
            data = data['data']
        except (KeyError, AttributeError, TypeError):
            return
        return data

    @is_authorized
    def get_response_json(self, *args, **kwargs):
        return self.get_api_request_json(self.get_request_url(*args, **kwargs), headers=self.headers)

    def get_token(self):
        _token = self.user_token.value
        if not _token:
            _token = self.login()
        return _token

    def login(self):
        path = self.get_request_url('login')
        data = self.get_api_request_json(path, postdata={'apikey': self.api_key}, method='json')
        if not data or not data.get('status') == 'success':
            return
        try:
            _token = data['data']['token']
        except (KeyError, TypeError):
            return
        self.user_token.value = _token
        return _token
