"""
    tknorris shared module

    Copyright (C) 2016 tknorris
    Copyright (C) 2016-2018 Twitch-on-Kodi

    Modified by Twitch-on-Kodi/plugin.video.twitch Dec. 12, 2016

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

import functools
import time
import hashlib
import os
import pickle
import shutil

from . import kodi, log_utils

cache_path = kodi.translate_path('special://temp/%s/cache/' % kodi.get_id())
try:
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)
except Exception as e:
    log_utils.log('Failed to create cache: %s: %s' % (cache_path, e), log_utils.LOGWARNING)

cache_enabled = kodi.get_setting('use_cache') == 'true'


def make_cache_path():
    try:
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)
    except Exception as e:
        log_utils.log('Failed to create cache: %s: %s' % (cache_path, e), log_utils.LOGWARNING)


def reset_cache():
    try:
        shutil.rmtree(cache_path)
        make_cache_path()
        return True
    except Exception as e:
        log_utils.log('Failed to Reset Cache: %s' % (e), log_utils.LOGWARNING)
        return False


def _get_func(name, args=None, kwargs=None, cache_limit=1):
    if not cache_enabled or cache_limit <= 0: return False, None
    now = time.time()
    max_age = now - (cache_limit * 60 * 60)
    if args is None: args = []
    if kwargs is None: kwargs = {}
    full_path = os.path.join(cache_path, _get_filename(name, args, kwargs))
    if os.path.exists(full_path):
        mtime = os.path.getmtime(full_path)
        if mtime >= max_age:
            with open(full_path, 'rb') as f:
                pickled_result = f.read()
            # log_utils.log('Returning cached result: |%s|%s|%s| - modtime: %s max_age: %s age: %ss' % (name, args, kwargs, mtime, max_age, now - mtime), log_utils.LOGDEBUG)
            return True, pickle.loads(pickled_result)

    return False, None


def _save_func(name, args=None, kwargs=None, result=None):
    try:
        if args is None: args = []
        if kwargs is None: kwargs = {}
        pickled_result = pickle.dumps(result)
        full_path = os.path.join(cache_path, _get_filename(name, args, kwargs))
        with open(full_path, 'wb') as f:
            f.write(pickled_result)
    except Exception as e:
        log_utils.log('Failure during cache write: %s' % (e), log_utils.LOGWARNING)


def _get_filename(name, args, kwargs):
    arg_hash = hashlib.md5(name.encode('utf-8')).hexdigest() + hashlib.md5(str(args).encode('utf-8')).hexdigest() + hashlib.md5(str(kwargs).encode('utf-8')).hexdigest()
    return arg_hash


def cache_method(cache_limit):
    def wrap(func):
        @functools.wraps(func)
        def memoizer(*args, **kwargs):
            if args:
                klass, real_args = args[0], args[1:]
                full_name = '%s.%s.%s' % (klass.__module__, klass.__class__.__name__, func.__name__)
            else:
                full_name = func.__name__
                real_args = args
            in_cache, result = _get_func(full_name, real_args, kwargs, cache_limit=cache_limit)
            if in_cache:
                # log_utils.log('Using method cache for: |%s|%s|%s| -> |%d|' % (full_name, args, kwargs, len(pickle.dumps(result))), log_utils.LOGDEBUG)
                log_utils.log('Using method cache for: |%s| -> |%d|' % (full_name, len(pickle.dumps(result))), log_utils.LOGDEBUG)
                return result
            else:
                # log_utils.log('Calling cached method: |%s|%s|%s|' % (full_name, args, kwargs), log_utils.LOGDEBUG)
                log_utils.log('Calling cached method: |%s|' % (full_name), log_utils.LOGDEBUG)
                result = func(*args, **kwargs)
                if cache_enabled and cache_limit > 0:
                    _save_func(full_name, real_args, kwargs, result)
                return result

        return memoizer

    return wrap


# do not use this with instance methods the self parameter will cause args to never match
def cache_function(cache_limit):
    def wrap(func):
        @functools.wraps(func)
        def memoizer(*args, **kwargs):
            name = func.__name__
            in_cache, result = _get_func(name, args, kwargs, cache_limit=cache_limit)
            if in_cache:
                # log_utils.log('Using function cache for: |%s|%s|%s| -> |%d|' % (name, args, kwargs, len(pickle.dumps(result))), log_utils.LOGDEBUG)
                log_utils.log('Using function cache for: |%s| -> |%d|' % (name, len(pickle.dumps(result))), log_utils.LOGDEBUG)
                return result
            else:
                # log_utils.log('Calling cached function: |%s|%s|%s|' % (name, args, kwargs), log_utils.LOGDEBUG)
                log_utils.log('Calling cached function: |%s|' % (name), log_utils.LOGDEBUG)
                result = func(*args, **kwargs)
                if cache_enabled and cache_limit > 0:
                    _save_func(name, args, kwargs, result)
                return result

        return memoizer

    return wrap
