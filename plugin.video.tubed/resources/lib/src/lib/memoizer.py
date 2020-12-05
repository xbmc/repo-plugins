# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import functools
import hashlib
import os
import pickle
import time

import xbmcvfs  # pylint: disable=import-error

from ..constants import ADDON_ID

ENABLED = True
PATH = xbmcvfs.translatePath('special://temp/%s/cache/' % ADDON_ID)


def make_path():
    if not xbmcvfs.exists(PATH):
        xbmcvfs.mkdirs(PATH)

    return xbmcvfs.exists(PATH)


def reset_cache():
    xbmcvfs.rmdir(PATH, force=True)
    return make_path()


def _get_filename(name, args, kwargs):
    return hashlib.md5(name.encode('utf-8')).hexdigest() + \
           hashlib.md5(str(args).encode('utf-8')).hexdigest() + \
           hashlib.md5(str(kwargs).encode('utf-8')).hexdigest()


def _load(name, args=None, kwargs=None, limit=60):
    if not ENABLED or limit <= 0:
        return False, None

    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    now = time.time()
    max_age = now - limit

    filename = os.path.join(PATH, _get_filename(name, args, kwargs))
    if xbmcvfs.exists(filename):
        mtime = xbmcvfs.Stat(filename).st_mtime()

        if mtime >= max_age:
            with open(filename, 'rb') as file_handle:
                payload = file_handle.read()

            return True, pickle.loads(payload)

    return False, None


def _save(name, args=None, kwargs=None, result=None):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    try:
        payload = pickle.dumps(result)

        filename = os.path.join(PATH, _get_filename(name, args, kwargs))
        with open(filename, 'wb') as file_handle:
            file_handle.write(payload)

        return True

    except:  # pylint: disable=bare-except
        return False


def cache_method(limit):
    def wrap(func):

        @functools.wraps(func)
        def memoizer(*args, **kwargs):
            if args:
                klass, rargs = args[0], args[1:]
                name = '%s.%s.%s' % (klass.__module__, klass.__class__.__name__, func.__name__)
            else:
                name = func.__name__
                rargs = args

            cached, payload = _load(name, rargs, kwargs, limit=limit)
            if cached:
                return payload

            payload = func(*args, **kwargs)
            if ENABLED and limit > 0:
                _save(name, rargs, kwargs, payload)

            return payload

        return memoizer

    return wrap


def cache_function(limit):
    def wrap(func):

        @functools.wraps(func)
        def memoizer(*args, **kwargs):
            name = func.__name__

            cached, payload = _load(name, args, kwargs, limit=limit)
            if cached:
                return payload

            payload = func(*args, **kwargs)
            if ENABLED and limit > 0:
                _save(name, args, kwargs, payload)

            return payload

        return memoizer

    return wrap


make_path()
