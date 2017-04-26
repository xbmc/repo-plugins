# -*- encoding: utf-8 -*-

from six.moves.urllib.parse import urljoin

from twitch import CLIENT_ID, OAUTH_TOKEN
from twitch.exceptions import ResourceUnavailableException
from twitch.logging import log
from twitch.scraper import download, get_json
from twitch import methods

_kraken_baseurl = 'https://api.twitch.tv/kraken/'
_hidden_baseurl = 'https://api.twitch.tv/api/'
_usher_baseurl = 'https://usher.ttvnw.net/'
_clips_baseurl = 'https://clips.twitch.tv/'
_uploads_baseurl = 'https://uploads.twitch.tv/'

_v5_headers = {'ACCEPT': 'application/vnd.twitchtv.v5+json'}


class _Query(object):
    def __init__(self, url, headers={}, data={}, method=methods.GET):
        self._headers = headers
        self._data = data
        self._url = url
        self._method = method

        self._params = dict()
        self._urlkws = dict()

    @property
    def url(self):
        formatted_url = self._url.format(**self._urlkws)  # throws KeyError
        return formatted_url

    @property
    def headers(self):
        return self._headers

    @property
    def data(self):
        return self._data

    @property
    def params(self):
        return self._params

    @property
    def method(self):
        return self._method

    @property
    def urlkws(self):
        return self._urlkws

    def add_path(self, path):
        self._url = urljoin(self._url, path)
        return self

    def add_data(self, key, value, default=None):
        assert_new(self._data, key)
        if value != default:
            self._data[key] = value
        return self

    def add_bin(self, data):
        self._data = data
        return self

    def add_param(self, key, value, default=None):
        assert_new(self._params, key)
        if value != default:
            self._params[key] = value
        return self

    def add_urlkw(self, kw, replacement):
        assert_new(self._urlkws, kw)
        self._urlkws[kw] = replacement
        return self

    def set_headers(self, headers):
        self._headers = headers
        return self

    def __str__(self):
        return '{method} Query to {url}, params {params}, data {data},  headers {headers}' \
            .format(url=self.url, params=self.params, headers=self.headers, data=self.data, method=self.method)

    def execute(self, f):
        try:
            return f(self.url, self.params, self.headers, self.data, self.method)
        except:
            raise ResourceUnavailableException(str(self))


class DownloadQuery(_Query):
    def execute(self):
        # TODO implement download completely here
        return super(DownloadQuery, self).execute(download)


class JsonQuery(_Query):
    def execute(self):
        # TODO implement get_json completely here
        return super(JsonQuery, self).execute(get_json)


class ApiQuery(JsonQuery):
    def __init__(self, path, headers={}, data={}, method=methods.GET):
        headers.setdefault('Client-ID', CLIENT_ID)
        if OAUTH_TOKEN:
            headers.setdefault('Authorization', 'OAuth {access_token}'.format(access_token=OAUTH_TOKEN))
        super(ApiQuery, self).__init__(_kraken_baseurl, headers, data, method)
        self.add_path(path)


class HiddenApiQuery(JsonQuery):
    def __init__(self, path, headers={}, data={}, method=methods.GET):
        headers.setdefault('Client-ID', CLIENT_ID)
        if OAUTH_TOKEN:
            headers.setdefault('Authorization', 'OAuth {access_token}'.format(access_token=OAUTH_TOKEN))
        super(HiddenApiQuery, self).__init__(_hidden_baseurl, headers, data, method)
        self.add_path(path)


class UsherQuery(DownloadQuery):
    def __init__(self, path, headers={}, data={}, method=methods.GET):
        headers.setdefault('Client-ID', CLIENT_ID)
        if OAUTH_TOKEN:
            headers.setdefault('Authorization', 'OAuth {access_token}'.format(access_token=OAUTH_TOKEN))
        super(UsherQuery, self).__init__(_usher_baseurl, headers, data, method)
        self.add_path(path)


class ClipsQuery(DownloadQuery):
    def __init__(self, path, headers={}, data={}, method=methods.GET):
        super(ClipsQuery, self).__init__(_clips_baseurl, headers, data, method)
        self.add_path(path)


class UploadsQuery(DownloadQuery):
    def __init__(self, path, headers={}, data={}, method=methods.PUT):
        super(UploadsQuery, self).__init__(_uploads_baseurl, headers, data, method)
        self.add_path(path)


class V5Query(ApiQuery):
    def __init__(self, path, method=methods.GET):
        super(V5Query, self).__init__(path, _v5_headers, method=method)


def assert_new(d, k):
    if k in d:
        v = d.get(k)
        raise ValueError("Key '{0}' already set to '{1}'".format(k, v))


# TODO maybe rename
def query(f):
    def wrapper(*args, **kwargs):
        qry = f(*args, **kwargs)
        if not isinstance(qry, _Query):
            raise ValueError('{0} did not return a Query, was: {1}'.format(f.__name__, repr(qry)))
        log.debug('%s QUERY: url: %s, params: %s, data: %s, '
                  'headers: %r, target_func: %r',
                  qry.method, qry.url, qry.params, qry.data, qry.headers, f.__name__)
        return qry.execute()

    return wrapper
