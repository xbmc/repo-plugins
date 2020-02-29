# -*- coding: utf-8 -*-
# -------------LicenseHeader--------------
# plugin.video.mediathek - Gives access to most video-platforms from German public service broadcasters
# Copyright (C) 2010  Raptor 2101 [raptor2101@gmx.de]
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>. 

from future import standard_library
standard_library.install_aliases()
from builtins import str
import os
import sys
import urllib.request, urllib.parse, urllib.error
import xbmc
import xbmcaddon
from simplexbmc import SimpleXbmcGui
from mediathek.factory import MediathekFactory
__plugin__ = "mediathek"

settings = xbmcaddon.Addon(id='plugin.video.mediathek')

gui = SimpleXbmcGui(settings)


def get_params():
    paramDict = {}
    try:
        if sys.argv[2]:
            paramPairs = sys.argv[2][1:].split("&")
            for paramsPair in paramPairs:
                paramSplits = paramsPair.split('=')
                if (len(paramSplits)) == 2:
                    paramDict[paramSplits[0]] = paramSplits[1]
    except:
        errorOK()
    return paramDict


params = get_params()
mediathekName = params.get("type", "")
action = params.get("action", "")

DIR_HOME = xbmc.translatePath(settings.getAddonInfo("profile"))
if not os.path.exists(DIR_HOME):
    os.mkdir(DIR_HOME)

gui.log("Quality: %s" % gui.quality)
gui.log("argv[0]: %s" % sys.argv[0])
gui.log("argv[1]: %s" % sys.argv[1])
gui.openMenuContext()
factory = MediathekFactory()

if mediathekName == "":
    if action == "":
        gui.addSearchButton(None)
        gui.listAvailableMediathekes(factory.getAvaibleMediathekTypes())
    else:
        result = gui.keyboardInput()
        if result.isConfirmed():
            searchText = str(result.getText().decode('UTF-8'))
            for name in factory.getAvaibleMediathekTypes():
                mediathek = factory.getMediathek(name, gui)
                if mediathek.isSearchable():
                    mediathek.searchVideo(searchText)
        else:
            gui.back()

else:
    cat = int(params.get("cat", 0))
    mediathek = factory.getMediathek(mediathekName, gui)

    if action == "openTopicPage":
        link = urllib.parse.unquote_plus(params.get("link", "")).decode('UTF-8')
        gui.log(link)
        mediathek.buildPageMenu(link, 0)
    elif action == "openPlayList":
        link = urllib.parse.unquote_plus(params.get("link", ""))
        gui.log(link)
        remotePlaylist = mediathek.loadPage(link)
        gui.playPlaylist(remotePlaylist)
    elif action == "openMenu":
        path = params.get("path", "0")
        mediathek.buildMenu(path)
    elif action == "search":
        result = gui.keyboardInput()
        if result.isConfirmed():
            searchText = str(result.getText().decode('UTF-8'))
            mediathek.searchVideo(searchText)
        else:
            gui.back()
    elif action == "openJsonPath":
        path = params.get("path", "0")
        callhash = params.get("callhash", "0")
        mediathek.buildJsonMenu(path, callhash, 0)
    elif action == "openJsonLink":
        link = urllib.parse.unquote_plus(params.get("link", ""))
        mediathek.playVideoFromJsonLink(link)
    else:
        if mediathek.isSearchable():
            gui.addSearchButton(mediathek)
        mediathek.displayCategories()
gui.closeMenuContext()
