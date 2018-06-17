# -*- coding: utf-8 -*-
# Wakanim - Watch videos from the german anime platform Wakanim.tv on Kodi.
# Copyright (C) 2017 MrKrabat
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import xbmc
import xbmcaddon


_plugId = "plugin.video.wakanim"

# plugin constants
_addon   = xbmcaddon.Addon(id=_plugId)
_plugin  = _addon.getAddonInfo("name")
_version = _addon.getAddonInfo("version")

xbmc.log("[PLUGIN] %s: version %s initialized" % (_plugin, _version))

if __name__ == "__main__":
    from resources.lib import wakanim
    # start addon
    wakanim.main(sys.argv)
