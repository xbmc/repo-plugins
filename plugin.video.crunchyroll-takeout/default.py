# -*- coding: utf-8 -*-
"""
    Crunchyroll
    Copyright (C) 2012 - 2014 Matthew Beacher
    This program is free software; you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by the
    Free Software Foundation; either version 2 of the License.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation,
Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
"""

import sys
import xbmc
import xbmcaddon


_plugId = 'plugin.video.crunchyroll-takeout'

# Plugin constants
__plugin__    = "Crunchyroll"
__version__   = "2.2.1"
__XBMCBUILD__ = xbmc.getInfoLabel("System.BuildVersion")
__settings__  = xbmcaddon.Addon(id=_plugId)
__language__  = __settings__.getLocalizedString

xbmc.log("[PLUGIN] '%s: version %s' initialized!" % (__plugin__, __version__))

if __name__ == "__main__":
    from resources.lib import crunchy_main

    crunchy_main.main()

sys.modules.clear()
