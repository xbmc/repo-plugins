#
#      Copyright (C) 2014 Tommy Winther, msj33, TermeHansen
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import os
import sys

import xbmc
import xbmcaddon
import xbmcgui

if sys.version_info.major == 2:
    # python 2
    from xbmc import translatePath
else:
    from xbmcvfs import translatePath

ADDON = xbmcaddon.Addon('plugin.video.drnu')

CACHE_PATH = translatePath(ADDON.getAddonInfo("Profile"))
if not os.path.exists(CACHE_PATH):
    os.makedirs(CACHE_PATH)

FAVORITES_PATH = os.path.join(CACHE_PATH, 'favorites.pickle')

if os.path.exists(FAVORITES_PATH):
    os.unlink(FAVORITES_PATH)

xbmcgui.Dialog().ok(ADDON.getLocalizedString(30008), ADDON.getLocalizedString(30202))
