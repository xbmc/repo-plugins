#!/usr/bin/python
# -*- coding: utf-8 -*-
from xbmcgui import Window
from tmdbhelper.lib.addon.plugin import format_name
from tmdbhelper.lib.addon.tmdate import set_timestamp
from tmdbhelper.lib.files.futils import json_loads as data_loads
from json import dumps as data_dumps


TIME_MINUTES = 60


class MemoryCache(object):
    def __init__(self, name):
        self._win = Window(10000)
        self._sc_name = f'TMDBHelper.MemCache.{name}'

    def get(self, endpoint):
        '''
            get object from cache and return the results
            endpoint: the (unique) name of the cache object as reference
        '''
        cur_time = set_timestamp(0, True)

        # Check expiration time
        expr_endpoint = f'{self._sc_name}_expr_{endpoint}'
        expr_propdata = self._win.getProperty(expr_endpoint)
        if not expr_propdata or int(expr_propdata) <= cur_time:
            return

        # Retrieve data
        data_endpoint = f'{self._sc_name}_data_{endpoint}'
        data_propdata = self._win.getProperty(data_endpoint)
        if not data_propdata:
            return

        return data_loads(data_propdata)

    def set(self, endpoint, data, cache_minutes=60):
        """ set data in cache """
        expires = set_timestamp(cache_minutes * TIME_MINUTES, True)
        data = data_dumps(data, separators=(',', ':'))
        expr_endpoint = f'{self._sc_name}_expr_{endpoint}'
        data_endpoint = f'{self._sc_name}_data_{endpoint}'
        self._win.setProperty(expr_endpoint, str(expires))
        self._win.setProperty(data_endpoint, data)

    def use(
            self, func, *args, cache_name=None, cache_minutes=60, cache_combine_name=True,
            cache_refresh=False, cache_store_none=False, **kwargs
    ):

        if not cache_name or cache_combine_name:
            cache_name = format_name(cache_name, *args, **kwargs)

        my_object = self.get(cache_name) if not cache_refresh else None
        empty_obj = f'{self._sc_name}_none_{cache_name}'

        if my_object == empty_obj:
            return

        if my_object:
            return my_object

        my_object = func(*args, **kwargs)

        if my_object:
            self.set(cache_name, my_object, cache_minutes)
            return my_object

        if cache_store_none:
            self.set(cache_name, empty_obj, cache_minutes)
