# -*- coding: utf-8 -*-
"""
    Class: CacheControl

    Implementation of file based caching for python objects.
    Utilises pickle to store object data as file within the KODI virtual file system.

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import hashlib
import os
import shutil
import time

# don't use kodi_six xbmcvfs
import xbmcvfs  # pylint: disable=import-error
from kodi_six import xbmc  # pylint: disable=import-error
from six import PY3
from six import text_type
# noinspection PyPep8Naming
from six.moves import cPickle as pickle

from .constants import CONFIG
from .logger import Logger

try:
    xbmc.translatePath = xbmcvfs.translatePath
except AttributeError:
    pass

LOG = Logger('cachecontrol')


class CacheControl:
    # ADDON_DATA_FOLDER is hardcoded and is used for path protection
    # Cache will only enable/delete if the path is in the add-on's addon_data folder
    ADDON_DATA_FOLDER = 'special://profile/addon_data/plugin.video.composite_for_plex/'

    def __init__(self, cache_location, enabled=True):
        if not CONFIG['cache_path'].startswith(self.ADDON_DATA_FOLDER):
            LOG.debug('CACHE: Cache is disabled, the cache path is'
                      ' not in the addon_data folder')
            enabled = False

        self.cache_location = xbmc.translatePath(os.path.join(CONFIG['cache_path'], cache_location))
        self.enabled = enabled

        if self.enabled:

            delimiter = '/' if self.cache_location.find('/') > -1 else '\\'
            if self.cache_location[-1] != delimiter:
                self.cache_location += delimiter

            if not xbmcvfs.exists(self.cache_location):
                LOG.debug('CACHE [%s]: Location does not exist.  Creating' %
                          self.cache_location)
                if not xbmcvfs.mkdirs(self.cache_location):
                    LOG.debug('CACHE [%s]: Location cannot be created' %
                              self.cache_location)
                    self.cache_location = None
                    return
            LOG.debug('Running with cache location: %s' % self.cache_location)

        else:
            self.cache_location = None
            LOG.debug('Cache is disabled')

    def read_cache(self, cache_name):
        if self.cache_location is None:
            return False, None

        LOG.debug('CACHE [%s]: attempting to read' % cache_name)
        cache = xbmcvfs.File(self.cache_location + cache_name)
        try:
            if PY3:
                cache_data = cache.readBytes()
            else:
                cache_data = cache.read()
        except Exception as error:  # pylint: disable=broad-except
            LOG.debug('CACHE [%s]: read error [%s]' % (cache_name, error))
            cache_data = False
        finally:
            cache.close()

        if cache_data:
            if isinstance(cache_data, text_type):
                cache_data = cache_data.encode('utf-8')
            LOG.debug('CACHE [%s]: read' % cache_name)
            try:
                cache_object = pickle.loads(cache_data)
            except (ValueError, TypeError):
                return False, None
            return True, cache_object

        LOG.debug('CACHE [%s]: empty' % cache_name)
        return False, None

    def write_cache(self, cache_name, obj):

        if self.cache_location is None:
            return True

        LOG.debug('CACHE [%s]: Writing file' % cache_name)
        cache = xbmcvfs.File(self.cache_location + cache_name, 'w')
        try:
            if PY3:
                cache.write(bytearray(pickle.dumps(obj)))
            else:
                cache.write(pickle.dumps(obj))
        except Exception as error:  # pylint: disable=broad-except
            LOG.debug('CACHE [%s]: Writing error [%s]' %
                      (self.cache_location + cache_name, error))
        finally:
            cache.close()
        return True

    def is_valid(self, cache_name, ttl=3600):
        if self.cache_location is None:
            return None

        if xbmcvfs.exists(self.cache_location + cache_name):
            LOG.debug('CACHE [%s]: exists, ttl: |%s|' % (cache_name, str(ttl)))
            now = int(round(time.time(), 0))
            modified = int(xbmcvfs.Stat(self.cache_location + cache_name).st_mtime())
            LOG.debug('CACHE [%s]: mod[%s] now[%s] diff[%s]' %
                      (cache_name, modified, now, now - modified))

            if (modified < 0) or (now - modified) > ttl:
                return False

            return True

        LOG.debug('CACHE [%s]: does not exist' % cache_name)
        return None

    def check_cache(self, cache_name, ttl=3600):
        if self.cache_location is None:
            return False, None

        cache_valid = self.is_valid(cache_name, ttl)

        if cache_valid is False:
            LOG.debug('CACHE [%s]: too old, delete' % cache_name)
            if xbmcvfs.delete(self.cache_location + cache_name):
                LOG.debug('CACHE [%s]: deleted' % cache_name)
            else:
                LOG.debug('CACHE [%s]: not deleted' % cache_name)

        elif cache_valid:
            LOG.debug('CACHE [%s]: current' % cache_name)
            return self.read_cache(cache_name)

        return False, None

    def delete_cache(self, force=False):
        if not CONFIG['cache_path'].startswith(self.ADDON_DATA_FOLDER):
            LOG.debug('CACHE: Cache not deleted, the cache path is'
                      ' not in the addon_data folder')
            return

        start_time = time.time()

        persistent_cache_suffix = '.pcache'

        if force:
            folder_deleted = self.delete_cache_folder()
            if folder_deleted:
                LOG.debug('Deleted cache in |%.3fs|' % (time.time() - start_time))
                return

        dirs, file_list = xbmcvfs.listdir(self.cache_location)

        LOG.debug('List of file: [%s]' % file_list)
        LOG.debug('List of dirs: [%s]' % dirs)

        cache_files = []
        append = cache_files.append
        path_join = os.path.join
        has_persistent = False

        for cache_file in file_list:
            if cache_file.endswith(persistent_cache_suffix):
                has_persistent = True

            if not force and cache_file.endswith(persistent_cache_suffix):
                continue

            append(path_join(self.cache_location, cache_file))

        folder_deleted = False
        if not has_persistent:
            folder_deleted = self.delete_cache_folder()

        delete = xbmcvfs.delete
        if not folder_deleted:
            for cache_file in cache_files:
                if delete(cache_file):
                    LOG.debug('SUCCESSFUL: removed %s' % cache_file)
                else:
                    LOG.debug('UNSUCCESSFUL: did not remove %s' % cache_file)

        LOG.debug('Deleted cache in |%.3fs|' % (time.time() - start_time))

    def delete_cache_folder(self):
        if xbmcvfs.exists(self.cache_location):
            shutil.rmtree(self.cache_location)

        if not xbmcvfs.exists(self.cache_location):
            LOG.debug('SUCCESSFUL: removed %s' % self.cache_location)
            xbmcvfs.mkdirs(self.cache_location)
            return True

        LOG.debug('UNSUCCESSFUL: did not remove %s' % self.cache_location)
        return False

    @staticmethod
    def sha512_cache_name(name, unique_id, data):
        if PY3:
            if not isinstance(name, bytes):
                name = name.encode('utf-8')
            if not isinstance(unique_id, bytes):
                unique_id = unique_id.encode('utf-8')
            if not isinstance(data, bytes):
                data = data.encode('utf-8')

        name_hash = hashlib.sha512()
        name_hash.update(name + unique_id + data)
        cache_name = name_hash.hexdigest()

        if isinstance(cache_name, bytes):
            cache_name = cache_name.decode('utf-8')

        return cache_name + '.cache'
