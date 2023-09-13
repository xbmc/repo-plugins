# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------


"""
A very simple key-value store.
Stores data in volatile memory for the lifetime of the addon or the specified period.
"""


import time
import logging
from copy import deepcopy

from codequick.support import logger_id


logger = logging.getLogger(logger_id + '.cache')
# noinspection SpellCheckingInspection
DFLT_EXPIRE_TIME = 600


__cache = {}


def get_item(key):
    """Return the cached data if present in the cache and not expired.
    Return None otherwise.

    """
    item = __cache.get(key)
    if item and item['expires'] > time.monotonic():
        logger.debug("Data cache: hit")
        return deepcopy(item['data'])
    else:
        logger.debug("Data cache: miss")
        return None


def set_item(key, data, expire_time=DFLT_EXPIRE_TIME):
    """Cache `data` in memory for the lifetime of the addon, to a maximum of `expire_time` in seconds.

    """
    item = dict(expires=time.monotonic() + expire_time,
                data=deepcopy(data))
    logger.debug("cached '%s'", key)
    __cache[key] = item


def clean():
    """Remove expired items from the cache."""
    now = time.monotonic()
    for key, item in list(__cache.items()):
        if item['expires'] < now:
            logger.debug('Clean removed: %s', key)
            del __cache[key]


def purge():
    """Empty the cache."""
    __cache.clear()


def size():
    return len(__cache)