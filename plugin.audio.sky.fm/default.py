#!/usr/bin/env python
# -*- coding: utf-8 -*-
########################################
#  Sky.fm XBMC plugin
#  by Tim C. 'Bitcrusher' Steinmetz
#  http://qualisoft.dk
#  Github: https://github.com/Bitcrusher/Sky-FM-XBMC-plugin
#  Git Read-only: git://github.com/Bitcrusher/Sky-FM-XBMC-plugin.git
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
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#


import os
import pickle
from pprint import pprint
import sys
import re
import string
import urllib

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import time
from xml.dom import minidom
from httpcomm import HTTPComm
from ConfigParser import SafeConfigParser
import json
from random import randrange
import Queue
import threading

# Import JSON - compatible with Python<v2.6
try:
    import json
except ImportError:
    import simplejson as json


# Config parser
pluginConfig = SafeConfigParser()
pluginConfig.read(os.path.join(os.path.dirname(__file__), "config.ini"))


# Various constants used throughout the script
HANDLE = int(sys.argv[1])
ADDON = xbmcaddon.Addon(id=pluginConfig.get('plugin', 'id'))

# Plugin constants
__plugin__ = ADDON.getAddonInfo('name')
__author__ = "Tim C. Steinmetz"
__url__ = "http://qualisoft.dk/"
__platform__ = "xbmc media center, [LINUX, OS X, WIN32]"
__date__ = pluginConfig.get('plugin', 'date')
__version__ = ADDON.getAddonInfo('version')


class musicAddonXbmc:

    """
     Let's get some tunes!
    """
    def run(self):
        xbmcgui.Dialog().ok(ADDON.getLocalizedString(30201),
                        ADDON.getLocalizedString(30202),
                        ADDON.getLocalizedString(30203))


        li = xbmcgui.ListItem(label=ADDON.getLocalizedString(30201))
        li.setProperty("IsPlayable", "false")
        xbmcplugin.addDirectoryItem(handle=HANDLE, url='', listitem=li, isFolder=False)

        li = xbmcgui.ListItem(label=ADDON.getLocalizedString(30202))
        li.setProperty("IsPlayable", "false")
        xbmcplugin.addDirectoryItem(handle=HANDLE, url='', listitem=li, isFolder=False)

        li = xbmcgui.ListItem(label=ADDON.getLocalizedString(30203))
        li.setProperty("IsPlayable", "false")
        xbmcplugin.addDirectoryItem(handle=HANDLE, url='', listitem=li, isFolder=False)



        # tell XMBC there are no more items to list
        xbmcplugin.endOfDirectory(HANDLE, succeeded=True)

        return True


MusicAddonInstance = musicAddonXbmc()
MusicAddonInstance.run()
