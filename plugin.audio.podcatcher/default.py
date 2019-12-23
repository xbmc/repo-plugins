# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
# plugin.audio.podcatcher - A plugin to organise Podcasts
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
"""
 A plugin to organize audio-podcast
"""

import sys, os, xbmcaddon,xbmc
from feedreader.opml import OpmlFile
from feedreader.archivefile import ArchiveFile

from simplexbmc import SimpleXbmcGui

__plugin__ = "AudioPodcast"
__author__ = 'Raptor 2101 [raptor2101@gmx.de]'
__date__ = '06-09-2010'

def get_params():
  """ extract params from argv[2] to make a dict (key=value) """
  paramDict = {}
  try:
    if sys.argv[2]:
      paramPairs=sys.argv[2][1:].split( "&" )
      for paramsPair in paramPairs:
        paramSplits = paramsPair.split('=')
        if (len(paramSplits))==2:
          paramDict[paramSplits[0]] = paramSplits[1]
  except IndexError:
    errorOK()
  return paramDict


params=get_params()
path=params.get("path", "")
action=params.get("action","")

__settings__ = xbmcaddon.Addon(id='plugin.audio.podcatcher')
__language__ = __settings__.getLocalizedString

gui = SimpleXbmcGui(path);

DIR_HOME = xbmc.translatePath(__settings__.getAddonInfo("profile"))
if not os.path.exists(DIR_HOME):
  os.mkdir(DIR_HOME);

DIR_ARCHIVES = os.path.join(DIR_HOME, 'archives')
if not os.path.exists(DIR_ARCHIVES):
  os.mkdir(DIR_ARCHIVES);
ArchiveFile.setArchivePath(DIR_ARCHIVES);


PATH_FILE_OPML = __settings__.getSetting("opmlFile")
if (PATH_FILE_OPML == ""):
  PATH_FILE_OPML = os.path.join(DIR_HOME,"opml.xml");
if not os.path.exists(PATH_FILE_OPML):
  gui.errorOK(__language__(30040),__language__(30041));
else:
  gui.log(PATH_FILE_OPML)
  opmlFile = OpmlFile(PATH_FILE_OPML, DIR_HOME, gui);

  if not path:
    path = ""
    action = "browse"

  gui.log("Path: "+path);
  gui.log("Action: "+action);

  if(len(path) > 0):
    path = path.split('.');
  else:
    path = [];

  if(action == "play" or action == "markRead" or action == "reload"):
    if action == "play":
      opmlFile.play(path);
    elif action == "markRead":
      opmlFile.markRead(path);
    else:
      opmlFile.reload(path);
    gui.refresh();
  else:
    gui.openMenuContext();
    opmlFile.displayMenu(path);
    gui.closeMenuContext();
