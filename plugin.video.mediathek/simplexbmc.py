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
from bs4 import BeautifulSoup;
import json
import hashlib
from mediathek import ComplexLink;

regex_findLink = re.compile("mms://[^\"]*wmv");

__plugin__ = "Mediathek"

settings = xbmcaddon.Addon(id='plugin.video.mediathek')
translation = settings.getLocalizedString

class SimpleXbmcGui(object):
  def __init__(self,settings):
    self.settings = xbmcaddon.Addon(id='plugin.video.mediathek');
    self.quality = int(xbmcplugin.getSetting(int(sys.argv[1]), "quality" ));
    self.preferedStreamTyp = int(xbmcplugin.getSetting(int(sys.argv[1]), "preferedStreamType"));
    self.log("quality: %s"%(self.quality));
    self.plugin_profile_dir = xbmc.translatePath(settings.getAddonInfo("profile"))
    if not os.path.exists(self.plugin_profile_dir):
      os.mkdir(self.plugin_profile_dir);

  def log(self, msg):
    if not isinstance(msg, (str, unicode)):
      xbmc.log("[%s]: %s" % (__plugin__, type(msg)))
    else:
      xbmc.log("[%s]: %s" % (__plugin__, msg.encode('utf8')))

  def buildVideoLink(self, displayObject, mediathek, objectCount):
    metaData = self.BuildMeteData(displayObject)
    if displayObject.picture is not None:
      listItem=xbmcgui.ListItem(metaData["title"], iconImage="DefaultFolder.png", thumbnailImage=displayObject.picture)
    else:
      listItem=xbmcgui.ListItem(metaData["title"], iconImage="DefaultFolder.png")
    listItem.setInfo("video",metaData);

    if(displayObject.isPlayable):
      if(displayObject.isPlayable == "PlayList"):
        link = displayObject.link[0]
        url = "%s?type=%s&action=openPlayList&link=%s" % (sys.argv[0],mediathek.name(), urllib.quote_plus(link.basePath))
        listItem.setProperty('IsPlayable', 'true');
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),url,listItem,False,objectCount)
      elif(displayObject.isPlayable == "JsonLink"):
        link = displayObject.link
        url = "%s?type=%s&action=openJsonLink&link=%s" % (sys.argv[0],mediathek.name(), urllib.quote_plus(link))
        listItem.setProperty('IsPlayable', 'true');
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),url,listItem, False, objectCount)
      else:
        link = self.extractLink(displayObject.link);
        if(isinstance(link,ComplexLink)):
          self.log("PlayPath:"+ link.playPath);
          listItem.setProperty("PlayPath", link.playPath);
        listItem.setProperty('IsPlayable', 'true');
        xbmcplugin.addDirectoryItem(int(sys.argv[1]),link.basePath,listItem,False,objectCount)
    else:
      url = "%s?type=%s&action=openTopicPage&link=%s" % (sys.argv[0],mediathek.name(), urllib.quote_plus(displayObject.link))
      xbmcplugin.addDirectoryItem(int(sys.argv[1]),url,listItem,True,objectCount)

  def BuildMeteData(self, displayObject):
    if(displayObject.subTitle is None or displayObject.subTitle == "" or displayObject.subTitle == displayObject.title):
      title = self.transformHtmlCodes(displayObject.title.rstrip());
    else:
      title = self.transformHtmlCodes(displayObject.title.rstrip() +" - "+ displayObject.subTitle.rstrip());
    if displayObject.date is not None:
      title = "(%s) %s"%(time.strftime("%d.%m",displayObject.date),title.rstrip());

    metaData = {
      "mediatype":"video",
      "title": title,
      "plotoutline":  self.transformHtmlCodes(displayObject.description)
    }

    if(displayObject.duration is not None):
      metaData["duration"] = int(displayObject.duration);

    if(displayObject.date is not None):
          self.log(time.strftime("%d.%m.%Y",displayObject.date));
          self.log(time.strftime("%Y",displayObject.date));
          metaData["date"] =time.strftime("%d.%m.%Y",displayObject.date);
          metaData["year"] =int(time.strftime("%Y",displayObject.date));
    return metaData;

  def transformHtmlCodes(self, content):
    return BeautifulSoup(content,"html.parser").prettify(formatter=None);

  def buildMenuLink(self,menuObject,mediathek,objectCount):
    title = menuObject.name;
    listItem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png")
    url = "%s?type=%s&action=openMenu&path=%s" % (sys.argv[0],mediathek.name(), menuObject.path)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listItem,isFolder=True,totalItems = objectCount)

  def storeJsonFile(self,jsonObject,additionalIdentifier = None):
    hashGenerator = hashlib.md5();
    hashGenerator.update(sys.argv[2]);
    if(additionalIdentifier is not None):
      hashGenerator.update(additionalIdentifier);
    callhash = hashGenerator.hexdigest();
    storedJsonFile = os.path.join(self.plugin_profile_dir,"%s.json"%callhash);
    with open(storedJsonFile, 'wb') as output:
      json.dump(jsonObject,output);
    return callhash;

  def loadJsonFile(self,callhash):
    storedJsonFile = os.path.join(self.plugin_profile_dir,"%s.json"%callhash);
    with open(storedJsonFile,"rb") as input:
      return json.load(input);

  def buildJsonLink(self,mediathek,title,jsonPath,callhash,objectCount):
    listItem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png")
    url = "%s?type=%s&action=openJsonPath&path=%s&callhash=%s" % (sys.argv[0],mediathek.name(), jsonPath,callhash)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listItem,isFolder=True,totalItems = objectCount)

  def listAvailableMediathekes(self, mediathekNames):
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
    for link in regex_findLink.findall(remotePlaylist):
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
  def play(self,links):
    link = self.extractLink(links);
    listItem = xbmcgui.ListItem(path=link.basePath)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=listItem)

  def extractLink(self, links):
    if(self.quality in links):
      return links[self.quality];
    else:
      selectedKey = -1;
      for key in links.keys():
        if(key < self.quality and key > selectedKey):
          selectedKey = key;
      if(selectedKey > -1):
        return links[selectedKey];
      else:
        selectedKey = links.keys()[0];
        for key in links.keys():
          if(key < selectedKey):
            selectedKey = key;
        return links[selectedKey];
