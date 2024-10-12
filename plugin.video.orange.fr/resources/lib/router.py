"""Addon router initialization."""

import xbmc
from routing import Plugin as Router

from lib.utils.kodi import log

router = Router()


def init_router():
    """Init addon router."""
    log("Initializing addon router", xbmc.LOGDEBUG)
    router.run()
