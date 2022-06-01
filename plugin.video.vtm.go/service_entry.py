# -*- coding: utf-8 -*-
"""Service entry point"""

from __future__ import absolute_import, division, unicode_literals

from xbmcaddon import Addon

from resources.lib import kodilogging, kodiutils

# Reinitialise ADDON every invocation to fix an issue that settings are not fresh.
kodiutils.ADDON = Addon()
kodilogging.ADDON = Addon()

if __name__ == '__main__':
    from resources.lib.service import run

    run()
