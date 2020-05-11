import datetime
import simplecache
import xbmcaddon
import xbmcgui
import xbmc
import requests
import resources.lib.utils as utils
import xml.etree.ElementTree as ET
_cache = simplecache.SimpleCache()


class RequestAPI(object):
    def __init__(self, cache_short=None, cache_long=None, req_api_url=None, req_api_key=None, req_api_name=None, req_wait_time=None):
        self.req_api_url = req_api_url or ''
        self.req_api_key = req_api_key or ''
        self.req_api_name = req_api_name or ''
        self.req_wait_time = req_wait_time or 0
        self.req_connect_err_prop = 'TMDbHelper.ConnectionError.{}'.format(self.req_api_name)
        self.req_connect_err = utils.try_parse_float(xbmcgui.Window(10000).getProperty(self.req_connect_err_prop)) or 0
        self.cache_long = 14 if not cache_long or cache_long < 14 else cache_long
        self.cache_short = 1 if not cache_short or cache_short < 1 else cache_short
        self.cache_name = 'plugin.video.themoviedb.helper'
        self.addon_name = 'plugin.video.themoviedb.helper'
        self.addon = xbmcaddon.Addon(self.addon_name)
        self.dialog_noapikey_header = u'{0} - {1}'.format(self.addon.getLocalizedString(32007), self.req_api_name)
        self.dialog_noapikey_text = self.addon.getLocalizedString(32009)
        self.dialog_noapikey_check = None

    def invalid_apikey(self):
        if self.dialog_noapikey_check == self.req_api_key:
            return  # We've already asked once so don't ask again for this container
        self.dialog_noapikey_check = self.req_api_key
        xbmcgui.Dialog().ok(self.dialog_noapikey_header, self.dialog_noapikey_text)
        xbmc.executebuiltin('Addon.OpenSettings({0})'.format(self.addon_name))

    def get_cache(self, cache_name):
        return _cache.get(cache_name)

    def set_cache(self, my_object, cache_name, cache_days=14):
        if my_object and cache_name and cache_days:
            _cache.set(cache_name, my_object, expiration=datetime.timedelta(days=cache_days))
        return my_object

    def use_cache(self, func, *args, **kwargs):
        """
        Simplecache takes func with args and kwargs
        Returns the cached item if it exists otherwise does the function
        """
        cache_days = kwargs.pop('cache_days', 14)
        cache_name = kwargs.pop('cache_name', self.cache_name)
        cache_only = kwargs.pop('cache_only', False)
        cache_refresh = kwargs.pop('cache_refresh', False)
        for arg in args:
            if arg:
                cache_name = u'{0}/{1}'.format(cache_name, arg)
        for key, value in kwargs.items():
            if value:
                cache_name = u'{0}&{1}={2}'.format(cache_name, key, value)
        my_cache = self.get_cache(cache_name) if not cache_refresh else None
        if my_cache:
            return my_cache
        elif not cache_only:
            my_object = func(*args, **kwargs)
            return self.set_cache(my_object, cache_name, cache_days)

    def translate_xml(self, request):
        if request:
            request = ET.fromstring(request.content)
            request = utils.dictify(request)
        return request

    def get_api_request(self, request=None, is_json=True, postdata=None, headers=None, dictify=True):
        """
        Make the request to the API by passing a url request string
        """
        if utils.get_timestamp(self.req_connect_err):
            return {} if dictify else None  # Connection error in last minute for this api so don't keep trying
        if self.req_wait_time:
            utils.rate_limiter(addon_name=self.cache_name, wait_time=self.req_wait_time, api_name=self.req_api_name)
        try:
            response = requests.post(request, data=postdata, headers=headers) if postdata else requests.get(request, headers=headers)  # Request our data
        except Exception as err:
            self.req_connect_err = utils.set_timestamp()
            xbmcgui.Window(10000).setProperty(self.req_connect_err_prop, str(self.req_connect_err))
            utils.kodi_log(u'ConnectionError: {}\nSuppressing retries for 1 minute'.format(err), 1)
            return {} if dictify else None
        if not response.status_code == requests.codes.ok and utils.try_parse_int(response.status_code) >= 400:  # Error Checking
            if response.status_code == 401:
                utils.kodi_log(u'HTTP Error Code: {0}\nRequest: {1}\nPostdata: {2}\nHeaders: {3}\nResponse: {4}'.format(response.status_code, request, postdata, headers, response), 1)
                self.invalid_apikey()
            elif response.status_code == 500:
                self.req_connect_err = utils.set_timestamp()
                xbmcgui.Window(10000).setProperty(self.req_connect_err_prop, str(self.req_connect_err))
                utils.kodi_log(u'HTTP Error Code: {0}\nRequest: {1}\nSuppressing retries for 1 minute'.format(response.status_code, request), 1)
            elif utils.try_parse_int(response.status_code) > 400:  # Don't write 400 error to log
                utils.kodi_log(u'HTTP Error Code: {0}\nRequest: {1}'.format(response.status_code, request), 1)
            return {} if dictify else None
        if dictify and is_json:
            response = response.json()  # Make the response nice
        elif dictify:
            response = self.translate_xml(response)
        return response

    def get_request_url(self, *args, **kwargs):
        """
        Creates a url request string:
        https://api.themoviedb.org/3/arg1/arg2?api_key=foo&kwparamkey=kwparamvalue
        """
        request = self.req_api_url
        for arg in args:
            if arg:  # Don't add empty args
                request = u'{0}/{1}'.format(request, arg)
        sep = '?' if '?' not in request else '&'
        request = u'{0}{1}{2}'.format(request, sep, self.req_api_key)
        for key, value in kwargs.items():
            if value:  # Don't add empty kwargs
                sep = '?' if '?' not in request else ''
                request = u'{0}{1}&{2}={3}'.format(request, sep, key, value)
        return request

    def get_request_sc(self, *args, **kwargs):
        """ Get API request using the short cache """
        kwargs['cache_days'] = self.cache_short
        return self.get_request(*args, **kwargs)

    def get_request_lc(self, *args, **kwargs):
        """ Get API request using the long cache """
        kwargs['cache_days'] = self.cache_long
        return self.get_request(*args, **kwargs)

    def get_request(self, *args, **kwargs):
        """ Get API request from cache (or online if no cached version) """
        cache_days = kwargs.pop('cache_days', self.cache_long)
        cache_name = kwargs.pop('cache_name', self.cache_name)
        cache_only = kwargs.pop('cache_only', False)
        cache_refresh = kwargs.pop('cache_refresh', False)
        is_json = kwargs.pop('is_json', True)
        request_url = self.get_request_url(*args, **kwargs)
        # utils.kodi_log(request_url, 1)
        return self.use_cache(
            self.get_api_request, request_url, is_json=is_json, cache_refresh=cache_refresh,
            cache_days=cache_days, cache_name=cache_name, cache_only=cache_only)
