# -*- coding: utf-8 -*-
"""
The local SQlite database module

Copyright 2017-2019, Leo Moll
SPDX-License-Identifier: MIT
"""

# pylint: disable=too-many-lines,line-too-long

import os
import json
import time

import resources.lib.appContext as appContext

from contextlib import closing
from codecs import open

import resources.lib.mvutils as mvutils

import resources.lib.appContext as appContext


class StoreCache(object):
    """
    The local SQlite database class

    """

    def __init__(self):
        self.logger = appContext.MVLOGGER.get_new_logger('StoreCache')
        self.notifier = appContext.MVNOTIFIER
        self.settings = appContext.MVSETTINGS
        # internals

    def load_cache(self, reqtype, condition):
        start = time.time()
        if not self.settings.getCaching():
            self.logger.debug('loading cache is disabled')
            return None
        #
        filename = os.path.join(self.settings.getDatapath() , reqtype + '.cache')
        if not mvutils.file_exists(filename):
            self.logger.debug('no cache file request "{}" and condition "{}"', reqtype, condition)
            return None
        #
        dbLastUpdate = self.settings.getLastUpdate()
        try:
            with closing(open(filename, encoding='utf-8')) as json_file:
                data = json.load(json_file)
                if isinstance(data, dict):
                    if data.get('type', '') != reqtype:
                        self.logger.debug('no matching cache for type {} vs {}', data.get('type', ''), reqtype)
                        return None
                    if data.get('condition', '') != condition:
                        self.logger.debug('no matching cache for condition {} vs {}', data.get('condition', ''), condition)
                        return None
                    if int(dbLastUpdate) != data.get('time', 0):
                        self.logger.debug('outdated cache')
                        return None
                    data = data.get('data', [])
                    if isinstance(data, list):
                        self.logger.debug('return cache after {} sec for request "{}" and condition "{}"', (time.time() - start), reqtype, condition)
                        return data
        # pylint: disable=broad-except
        except Exception as err:
            self.logger.error('Failed to load cache file {}: {}', filename, err)
            mvutils.file_remove(filename)
            raise
        self.logger.debug('no cache found')
        return None

    def save_cache(self, reqtype, condition, data):
        if not self.settings.getCaching():
            self.logger.debug('saving cache is disabled')
            return None
        if data is None:
            self.logger.debug('cache data is NONE')
            return None
        if len(data) == 0:
            self.logger.debug('no data to cache')
            return None
        if not isinstance(data, list):
            self.logger.debug('not a proper instance for caching')
            return None
        start = time.time()
        filename = os.path.join(self.settings.getDatapath() , reqtype + '.cache')
        dbLastUpdate = self.settings.getLastUpdate()
        cache = {
            "type": reqtype,
            "time": int(dbLastUpdate),
            "condition": condition,
            "data": data
        }
        try:
            with closing(open(filename, 'w', encoding='utf-8')) as json_file:
                json.dump(cache, json_file)
        except Exception as err:
            self.logger.error('Failed to write cache file {}: {}', filename, err)
            raise
        self.logger.debug('cache saved after {} sec for request "{}" and condition "{}"', (time.time() - start), reqtype, condition)
