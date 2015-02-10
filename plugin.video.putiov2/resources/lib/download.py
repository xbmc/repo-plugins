#!/usr/bin/env python
# coding: utf-8
# 
# put.io xbmc addon
# Copyright (C) 2009  Alper Kanat <alper@put.io>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# 

import sys
import time

import xbmc
import xbmcgui as xg

try:
    fileName = sys.argv[1]
    fileUrl = sys.argv[2]
    
    xbmc.executebuiltin(
        'XBMC.Notification("Download Initiated!", "Starting to download: %s", 10000, "DefaultProgram.png")' % fileName
    )

    xbmc.log("starting to download [%s] at [%s]" % (fileName, fileUrl))
    
    # TODO: start download with wget/curl or with python lib.
    # TODO: show a progress bar for status
except IndexError:
    xbmc.executebuiltin(
        'XBMC.Notification("Download Failure", "Download of %s has been failed!", 10000, "%s")' % (
            fileName,
            "special://home/addons/plugin.video.putio/resources/images/error.png"
        )
    )