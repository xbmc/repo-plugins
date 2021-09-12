import xbmcgui
import xml.etree.ElementTree as ET
from resources.lib.addon.cache import BasicCache, CACHE_SHORT, CACHE_LONG
from resources.lib.addon.window import get_property
from resources.lib.addon.plugin import kodi_log, ADDON
from resources.lib.addon.parser import try_int
from resources.lib.addon.timedate import get_timestamp, set_timestamp
from copy import copy
from json import loads, dumps


requests = None  # Requests module is slow to import so lazy import via decorator instead


def lazyimport_requests(func):
    def wrapper(*args, **kwargs):
        global requests
        if requests is None:
            import requests
        return func(*args, **kwargs)
    return wrapper


def dictify(r, root=True):
    if root:
        return {r.tag: dictify(r, False)}
    d = copy(r.attrib)
    if r.text:
        d["_text"] = r.text
    for x in r.findall("./*"):
        if x.tag not in d:
            d[x.tag] = []
        d[x.tag].append(dictify(x, False))
    return d


def translate_xml(request):
    if request:
        request = ET.fromstring(request.content)
        request = dictify(request)
    return request


class RequestAPI(object):
    def __init__(self, req_api_url=None, req_api_key=None, req_api_name=None, timeout=None):
        self.req_api_url = req_api_url or ''
        self.req_api_key = req_api_key or ''
        self.req_api_name = req_api_name or ''
        self.req_timeout_err_prop = u'TimeOutError.{}'.format(self.req_api_name)
        self.req_timeout_err = get_property(self.req_timeout_err_prop, is_type=float) or 0
        self.req_connect_err_prop = u'ConnectionError.{}'.format(self.req_api_name)
        self.req_connect_err = get_property(self.req_connect_err_prop, is_type=float) or 0
        self.req_500_err_prop = u'500Error.{}'.format(self.req_api_name)
        self.req_500_err = get_property(self.req_500_err_prop)
        self.req_500_err = loads(self.req_500_err) if self.req_500_err else {}
        self.req_strip = [(self.req_api_url, self.req_api_name), (self.req_api_key, ''), ('is_xml=False', ''), ('is_xml=True', '')]
        self.headers = None
        self.timeout = timeout or 10
        self._cache = BasicCache(filename='{}.db'.format(req_api_name or 'requests'))

    def get_api_request_json(self, request=None, postdata=None, headers=None, is_xml=False):
        request = self.get_api_request(request=request, postdata=postdata, headers=headers)
        if is_xml:
            return translate_xml(request)
        if request:
            return request.json()
        return {}

    def connection_error(self, err, wait_time=30, msg_affix=''):
        self.req_connect_err = set_timestamp(wait_time)
        get_property(self.req_connect_err_prop, self.req_connect_err)
        kodi_log(u'ConnectionError: {} {}\nSuppressing retries for 30 seconds'.format(msg_affix, err), 1)
        xbmcgui.Dialog().notification(
            ADDON.getLocalizedString(32308).format(' '.join([self.req_api_name, msg_affix])),
            ADDON.getLocalizedString(32307).format('30'))

    def fivehundred_error(self, request, wait_time=60):
        self.req_500_err[request] = set_timestamp(wait_time)
        get_property(self.req_500_err_prop, dumps(self.req_500_err))
        kodi_log(u'ConnectionError: {}\nSuppressing retries for 60 seconds'.format(dumps(self.req_500_err)), 1)
        xbmcgui.Dialog().notification(
            ADDON.getLocalizedString(32308).format(self.req_api_name),
            ADDON.getLocalizedString(32307).format('60'))

    def timeout_error(self, err):
        """ Log timeout error
        If two timeouts occur in x3 the timeout limit then set connection error
        e.g. if timeout limit is 10s then two timeouts within 30s trigger connection error
        """
        kodi_log(u'ConnectionTimeOut: {}'.format(err), 1)
        if get_timestamp(self.req_timeout_err):
            self.connection_error(err, msg_affix='timeout')
        self.req_timeout_err = set_timestamp(self.timeout * 3)
        get_property(self.req_timeout_err_prop, self.req_timeout_err)

    @lazyimport_requests
    def get_simple_api_request(self, request=None, postdata=None, headers=None, method=None):
        try:
            if method == 'delete':
                return requests.delete(request, headers=headers, timeout=self.timeout)
            if method == 'put':
                return requests.put(request, data=postdata, headers=headers, timeout=self.timeout)
            if postdata or method == 'post':  # If pass postdata assume we want to post
                return requests.post(request, data=postdata, headers=headers, timeout=self.timeout)
            return requests.get(request, headers=headers, timeout=self.timeout)
        except requests.exceptions.ConnectionError as errc:
            self.connection_error(errc)
        except requests.exceptions.Timeout as errt:
            self.timeout_error(errt)
        except Exception as err:
            kodi_log(u'RequestError: {}'.format(err), 1)

    @lazyimport_requests
    def get_api_request(self, request=None, postdata=None, headers=None):
        """
        Make the request to the API by passing a url request string
        """
        # Connection error in last minute for this api so don't keep trying
        if get_timestamp(self.req_connect_err):
            return
        if get_timestamp(self.req_500_err.get(request)):
            return

        # Get response
        response = self.get_simple_api_request(request, postdata, headers)
        if response is None or not response.status_code:
            return

        # Some error checking
        if not response.status_code == requests.codes.ok and try_int(response.status_code) >= 400:  # Error Checking
            # 500 code is server error which usually indicates Trakt is down
            # In this case let's set a connection error and suppress retries for a minute
            if response.status_code == 500:
                self.fivehundred_error(request)
            # 429 is too many requests code so suppress retries for a minute
            elif response.status_code == 429:
                self.connection_error(429)
            # Don't write 400 Bad Request error to log
            # 401 == OAuth / API key required
            elif try_int(response.status_code) > 400:
                log_level = 2 if try_int(response.status_code) in [404] else 1
                kodi_log([
                    u'HTTP Error Code: {}'.format(response.status_code),
                    u'\nRequest: {}'.format(request.replace(self.req_api_key, '') if request else None),
                    u'\nPostdata: {}'.format(postdata) if postdata else '',
                    u'\nHeaders: {}'.format(headers) if headers else '',
                    u'\nResponse: {}'.format(response) if response else ''], log_level)
            return

        # Return our response
        return response

    def get_request_url(self, *args, **kwargs):
        """
        Creates a url request string:
        https://api.themoviedb.org/3/arg1/arg2?api_key=foo&kwparamkey=kwparamvalue
        """
        request = self.req_api_url
        for arg in args:
            if arg is not None:
                request = u'{}/{}'.format(request, arg)
        sep = '?' if '?' not in request else '&'
        request = u'{}{}{}'.format(request, sep, self.req_api_key) if self.req_api_key else request
        for key, value in sorted(kwargs.items()):
            if value is not None:  # Don't add nonetype kwargs
                sep = '?' if '?' not in request else ''
                request = u'{}{}&{}={}'.format(request, sep, key, value)
        return request

    def get_request_sc(self, *args, **kwargs):
        """ Get API request using the short cache """
        kwargs['cache_days'] = CACHE_SHORT
        return self.get_request(*args, **kwargs)

    def get_request_lc(self, *args, **kwargs):
        """ Get API request using the long cache """
        kwargs['cache_days'] = CACHE_LONG
        return self.get_request(*args, **kwargs)

    def get_request(self, *args, **kwargs):
        """ Get API request from cache (or online if no cached version) """
        cache_days = kwargs.pop('cache_days', 0)  # Number of days to cache retrieved object if not already in cache.
        cache_name = kwargs.pop('cache_name', '')  # Affix to standard cache name.
        cache_only = kwargs.pop('cache_only', False)  # Only retrieve object from cache.
        cache_force = kwargs.pop('cache_force', False)  # Force retrieved object to be saved in cache. Use int to specify cache_days for fallback object.
        cache_fallback = kwargs.pop('cache_fallback', False)  # Object to force cache if no object retrieved.
        cache_refresh = kwargs.pop('cache_refresh', False)  # Ignore cached timestamps and retrieve new object.
        cache_combine_name = kwargs.pop('cache_combine_name', False)  # Combine given cache_name with auto naming via args/kwargs
        cache_strip = self.req_strip + kwargs.pop('cache_strip', [])  # Strip out api key and url from cache name
        headers = kwargs.pop('headers', None) or self.headers  # Optional override to default headers.
        postdata = kwargs.pop('postdata', None)  # Postdata if need to POST to a RESTful API.
        is_xml = kwargs.pop('is_xml', False)  # Response needs translating from XML to dict
        request_url = self.get_request_url(*args, **kwargs)
        return self._cache.use_cache(
            self.get_api_request_json, request_url,
            headers=headers,
            postdata=postdata,
            is_xml=is_xml,
            cache_refresh=cache_refresh,
            cache_days=cache_days,
            cache_name=cache_name,
            cache_only=cache_only,
            cache_force=cache_force,
            cache_fallback=cache_fallback,
            cache_combine_name=cache_combine_name,
            cache_strip=cache_strip)
