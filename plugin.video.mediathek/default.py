# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
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

import urllib,xbmc,os
from simplexbmc import SimpleXbmcGui
from mediathek.factory import MediathekFactory
__plugin__ = "mediathek"

gui = SimpleXbmcGui();

def get_params():
  paramDict = {}
  try:
    print "get_params() argv=", sys.argv
    if sys.argv[2]:
      paramPairs=sys.argv[2][1:].split( "&" )
      for paramsPair in paramPairs:
        paramSplits = paramsPair.split('=')
        if (len(paramSplits))==2:
          paramDict[paramSplits[0]] = paramSplits[1]
  except:
    errorOK()
  return paramDict


params = get_params();
mediathekName = params.get("type", "")
action=params.get("action", "")

gui.log("Quality: %s"%gui.quality);
gui.log("argv[0]: %s"%sys.argv[0]);
gui.log("argv[1]: %s"%sys.argv[1]);
gui.openMenuContext();
factory = MediathekFactory();


        
        
if(mediathekName == ""):
  if(action == ""):
    gui.addSearchButton(None);
    gui.listAvaibleMediathekes(factory.getAvaibleMediathekTypes());
  else:
    result = gui.keyboardInput();
    if (result.isConfirmed()):
      searchText = unicode(result.getText().decode('UTF-8'));
      for name in factory.getAvaibleMediathekTypes():
        mediathek = factory.getMediathek(name, gui);
        if(mediathek.isSearchable()):
          mediathek.searchVideo(searchText);
    else:
      gui.back();
      
else:
  cat=int(params.get("cat", 0))
  mediathek = factory.getMediathek(mediathekName,gui);
    
  if(action == "openTopicPage"):
    link = urllib.unquote_plus(params.get("link", ""));
    gui.log(link);
    mediathek.buildPageMenu(link, 0);
  elif(action == "openPlayList"):
    link = urllib.unquote_plus(params.get("link", ""));
    gui.log(link);
    remotePlaylist = mediathek.loadPage(link);
    gui.playPlaylist(remotePlaylist);
  elif(action == "openMenu"):
    path = params.get("path", "0");
    mediathek.buildMenu(path)
  elif(action == "search"):
    result = gui.keyboardInput();
    if (result.isConfirmed()):
      searchText = unicode(result.getText().decode('UTF-8'));
      mediathek.searchVideo(searchText);
    else:
      gui.back();
  else:
    if(mediathek.isSearchable()):
      gui.addSearchButton(mediathek);
    mediathek.displayCategories();
gui.closeMenuContext();

