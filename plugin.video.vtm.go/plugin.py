# -*- coding: utf-8 -*-
""" Addon entry point """

from __future__ import absolute_import, division, unicode_literals

from xbmcaddon import Addon

from resources.lib import kodiwrapper, kodilogging

# Reinitialise ADDON every invocation to fix an issue that settings are not fresh.
kodiwrapper.ADDON = Addon()
kodilogging.ADDON = Addon()

if __name__ == '__main__':
    import sys
    from resources.lib import plugin  # pylint: disable=ungrouped-imports

    plugin.run(sys.argv)
