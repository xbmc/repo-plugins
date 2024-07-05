"""Addon entry point."""

import sys

import lib.routes  # noqa: F401
import xbmc
from lib.router import init_router
from lib.utils.kodi import log

if __name__ == "__main__":
    log(sys.version, xbmc.LOGDEBUG)
    init_router()
