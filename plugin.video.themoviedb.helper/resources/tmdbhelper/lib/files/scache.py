#!/usr/bin/python
# -*- coding: utf-8 -*-
import jurialmunkey.scache
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.addon.plugin import get_setting
from tmdbhelper.lib.files.futils import FileUtils


class SimpleCache(jurialmunkey.scache.SimpleCache):
    _memcache = get_setting('use_mem_cache')
    _basefolder = get_setting('cache_location', 'str') or ''
    _fileutils = FileUtils()  # Import to use plugin addon_data folder not the module one

    @staticmethod
    def kodi_log(msg, level=0):
        kodi_log(msg, level)


class SimpleCacheMem(SimpleCache):
    _memcache = True
