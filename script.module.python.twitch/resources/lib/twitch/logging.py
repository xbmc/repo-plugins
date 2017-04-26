# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

log = logging.getLogger('twitch')
log.addHandler(NullHandler())


def deprecation_warning(logger, old, new):
    logger.warning("DEPRECATED call to '%s\' detected, "
                   "please use '%s' instead",
                   old, new)
