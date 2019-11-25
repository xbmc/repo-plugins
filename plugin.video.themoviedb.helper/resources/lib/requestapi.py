import datetime
import simplecache
import xbmcaddon
import xbmcgui
import xbmc
import requests
import resources.lib.utils as utils
import xml.etree.ElementTree as ET
_cache = simplecache.SimpleCache()
_xbmcdialog = xbmcgui.Dialog()
_addon = xbmcaddon.Addon()


class RequestAPI(object):
    def __init__(self):
        self.req_api_url = ''
        self.req_api_key = ''
        self.req_api_name = ''
        self.req_wait_time = 1
        self.cache_long = 14
        self.cache_short = 1
        self.addon_name = 'plugin.video.themoviedb.helper'

    def invalid_apikey(self, api_name='TMDb'):
        _xbmcdialog.ok('{0} {1} {2}'.format(_addon.getLocalizedString(32007), api_name, _addon.getLocalizedString(32008)),
                       _addon.getLocalizedString(32009))
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
        cache_name = kwargs.pop('cache_name', self.addon_name)
        cache_only = kwargs.pop('cache_only', False)
        for arg in args:
            if arg:
                cache_name = u'{0}/{1}'.format(cache_name, arg)
        for key, value in kwargs.items():
            if value:
                cache_name = u'{0}&{1}={2}'.format(cache_name, key, value)
        my_cache = self.get_cache(cache_name)
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
        if self.req_wait_time:
            utils.rate_limiter(addon_name=self.addon_name, wait_time=self.req_wait_time, api_name=self.req_api_name)
        utils.kodi_log(request, 0)
        request = requests.post(request, data=postdata) if postdata else requests.get(request, headers=headers)  # Request our data
        if not request.status_code == requests.codes.ok:  # Error Checking
            if request.status_code == 401:
                utils.kodi_log('HTTP Error Code: {0}'.format(request.status_code), 1)
                self.invalid_apikey()
            elif not request.status_code == 400:  # Don't write 400 error to log
                utils.kodi_log('HTTP Error Code: {0}'.format(request.status_code), 1)
            return {}
        if dictify and is_json:
            request = request.json()  # Make the request nice
        elif dictify:
            request = self.translate_xml(request)
        return request

    def get_request_url(self, *args, **kwargs):
        """
        Creates a url request string:
        https://api.themoviedb.org/3/arg1/arg2?api_key=foo&kwparamkey=kwparamvalue
        """
        request = self.req_api_url
        for arg in args:
            if arg:  # Don't add empty args
                request = u'{0}/{1}'.format(request, arg)
        request = u'{0}{1}'.format(request, self.req_api_key)
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
        cache_name = kwargs.pop('cache_name', self.addon_name)
        cache_only = kwargs.pop('cache_only', False)
        is_json = kwargs.pop('is_json', True)
        request_url = self.get_request_url(*args, **kwargs)
        return self.use_cache(self.get_api_request, request_url, is_json=is_json,
                              cache_days=cache_days, cache_name=cache_name, cache_only=cache_only)
