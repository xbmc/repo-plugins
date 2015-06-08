# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
# plugin.video.mediathek - display german mediathekes
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
import xbmc, xbmcgui, xbmcplugin,xbmcaddon, sys, urllib, os, time, re 
from html import transformHtmlCodes
from xml.dom import minidom

regex_findLink = re.compile("mms://[^\"]*wmv");

__plugin__ = "Mediathek"

settings = xbmcaddon.Addon(id='plugin.video.mediathek')
translation = settings.getLocalizedString

class SimpleXbmcGui(object):
  def __init__(self):
    self.settings = xbmcaddon.Addon(id='plugin.video.mediathek');
    self.quality = int(xbmcplugin.getSetting(int(sys.argv[1]), "quality" ));
    self.preferedStreamTyp = int(xbmcplugin.getSetting(int(sys.argv[1]), "preferedStreamType"));
    
    self.log("quality: %s"%(self.quality));
    
  def log(self, msg):
    if type(msg) not in (str, unicode):
      xbmc.log("[%s]: %s" % (__plugin__, type(msg)))
    else:
      xbmc.log("[%s]: %s" % (__plugin__, msg.encode('utf8')))
      
  def buildVideoLink(self, displayObject, mediathek, objectCount):
    if(displayObject.subTitle == "" or displayObject.subTitle == displayObject.title):
      title = transformHtmlCodes(displayObject.title);
    else:
      title = transformHtmlCodes(displayObject.title +" - "+ displayObject.subTitle);
    
    if displayObject.date is not None:
      title = "(%s) %s"%(time.strftime("%d.%m",displayObject.date),title);  
    
    if displayObject.picture is not None:
      listItem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=displayObject.picture)
    else:
      listItem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png")
    
    if(displayObject.isPlayable):
      if(displayObject.isPlayable == "PlayList"):
        link = displayObject.link[0]
        
        url = "%s?type=%s&action=openPlayList&link=%s" % (sys.argv[0],mediathek.name(), urllib.quote_plus(link.basePath))
        
        self.log(url);
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listItem,isFolder=True,totalItems = objectCount)
      else:
        self.log(displayObject.title);
        if(self.quality in displayObject.link):
          link = displayObject.link[self.quality];
        else:
          selectedKey = -1;
          for key in displayObject.link.keys():
            if(key < self.quality and key > selectedKey):
              selectedKey = key;
          if(selectedKey > -1):
            link = displayObject.link[selectedKey];
          else:
            selectedKey = displayObject.link.keys()[0];
            for key in displayObject.link.keys():
              if(key < selectedKey):
                selectedKey = key;
            link = displayObject.link[selectedKey];
        
        if(type(link).__name__ == "ComplexLink"):
          self.log("PlayPath:"+ link.playPath);
          listItem.setProperty("PlayPath", link.playPath);

        self.log("URL:"+ link.basePath);
        try:
          listItem.setInfo("video",{
            "size": link.size,
            "date": time.strftime("%d.%m.%Y",displayObject.date),
            "year": int(time.strftime("%Y",displayObject.date)),
            "title": title,
            "plot": transformHtmlCodes(displayObject.description),
            "duration": displayObject.duration
          }); 
        except:
          pass;
      
      
        listItem.setProperty('IsPlayable', 'true');
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=link.basePath,listitem=listItem,isFolder=False,totalItems = objectCount)
    else:
      url = "%s?type=%s&action=openTopicPage&link=%s" % (sys.argv[0],mediathek.name(), urllib.quote_plus(displayObject.link))
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listItem,isFolder=True,totalItems = objectCount)
      
  def buildMenuLink(self,menuObject,mediathek,objectCount):
    title = menuObject.name;
    listItem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png")
           
    url = "%s?type=%s&action=openMenu&path=%s" % (sys.argv[0],mediathek.name(), menuObject.path)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listItem,isFolder=True,totalItems = objectCount)

  def listAvaibleMediathekes(self, mediathekNames):
    rootPath = os.path.join(self.settings.getAddonInfo('path'),"resources/logos/png/");
    for name in mediathekNames:
      listItem=xbmcgui.ListItem(name, iconImage="DefaultFolder.png",thumbnailImage=os.path.join(rootPath,name+".png"))
      url = "%s?type=%s" % (sys.argv[0], name)
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listItem,isFolder=True)
  
  def openMenuContext(self):
    self.dialogProgress = xbmcgui.DialogProgress();
  
  def closeMenuContext(self):
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
  def getHomeDir(self):
    return self.settings.getAddonInfo("profile");
  
  def back(self):
    xbmc.executebuiltin("Action(PreviousMenu)");
    
  def keyboardInput(self):
    keyboard = xbmc.Keyboard("")
    keyboard.doModal();
    return keyboard;
    
  def addSearchButton(self,mediathek):
    title = translation(30100);
    listItem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png")
    if(mediathek is not None):       
      url = "%s?type=%s&action=search" % (sys.argv[0],mediathek.name())
    else:
      url = "%s?action=search" % (sys.argv[0])
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listItem,isFolder=True)
  
  def readText(self,node,textNode):
    try:
      node = node.getElementsByTagName(textNode)[0].firstChild;
      return unicode(node.data);
    except:
      return "";
      
  def playPlaylist(self, remotePlaylist):
    player = xbmc.Player();
    
    playerItem = xbmcgui.ListItem(remotePlaylist);
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO);
    playlist.clear();
    print "playPlaylist";
    
    for link in regex_findLink.findall(remotePlaylist):
      print link;
      listItem=xbmcgui.ListItem(link);
      listItem.setProperty("PlayPath", link);
      playlist.add(url=link, listitem=listItem);
    
    player.play(playlist, playerItem, false);
      
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
