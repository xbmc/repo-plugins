"""
    Copyright (C) 2020 Scott Ware
    This file is part of Scoot Media Streamer (plugin.video.sms)
    SPDX-License-Identifier: GPL-3.0-only
    See LICENSE.txt for more information
"""

import xbmc

def getVersion():
    build = xbmc.getInfoLabel('System.BuildVersion')
    version = int(build.split(".", 1)[0])
    return version
