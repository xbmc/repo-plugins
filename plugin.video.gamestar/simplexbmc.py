# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
# plugin.video.gamestar - Downloads/view videos from gamestar.de
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
import xbmc, xbmcgui, xbmcplugin,xbmcaddon, sys, urllib, urllib2, os, re, time
__plugin__ = "Gamestar"

regex_getTargetPath = re.compile("[^/]*\\..{3}$");

class SimpleXbmcGui(object):
  def __init__(self, showSourcename):
    self.showSourcename = showSourcename;
    
  def log(self, msg):
    if type(msg) not in (str, unicode):
      xbmc.log("[%s]: %s" % (__plugin__, type(msg)))
    else:
      xbmc.log("[%s]: %s" % (__plugin__, msg.encode('utf8')))
    
  def buildVideoLink(self, videoItems):
    for videoItem in videoItems:
      if(self.showSourcename):
        title = "[%s] %s"%(videoItem.sourceName, videoItem.title)
      else:
        title = "%s"%(videoItem.title)
      listItem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=videoItem.picture)
        
      url = videoItem.url;
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listItem,isFolder=False)
    

  def showCategories(self,categorieItems):
    for (index,pictureLink) in categorieItems.iteritems():    
      addon = xbmcaddon.Addon("plugin.video.gamestar")
      
      title = addon.getLocalizedString(index)
      listItem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=pictureLink)
      u = "%s?&action=list&cat=%s" % (sys.argv[0], index)
        
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=listItem,isFolder=True)
  
  def openMenuContext(self):
    self.dialogProgress = xbmcgui.DialogProgress();
  
  def closeMenuContext(self):
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
        
  def refresh(self):
    xbmc.executebuiltin("Container.Refresh");
  
  def play(self, path):
    player = xbmc.Player();
    player.play(path);
  
  def errorOK(self,title="", msg=""):
    e = str( sys.exc_info()[ 1 ] )
    self.log(e)
    if not title:
      title = __plugin__
    if not msg:
      msg = "ERROR!"
    if(e == None):
      xbmcgui.Dialog().ok( title, msg, e )  
    else:
      xbmcgui.Dialog().ok( title, msg)  
