# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
# plugin.video.podcatcher- A plugin to organise Podcasts
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
import xbmc, xbmcgui, xbmcplugin,xbmcaddon, sys, re, time
__plugin__ = "PodCatcher"

regex_decimal = re.compile("\\d+");
regex_duration = re.compile("(\\d+:){0,2}\\d+");
settings = xbmcaddon.Addon(id='plugin.audio.podcatcher')
translation = settings.getLocalizedString

class SimpleXbmcGui(object):
  def __init__(self,path):
    self.path = path;

  @staticmethod
  def log(msg):
    if not isinstance(msg,str) and not isinstance(msg,unicode):
      xbmc.log("[%s]: %s" % (__plugin__, type(msg)))
    else:
      xbmc.log("[%s]: %s" % (__plugin__, msg.encode('utf8')))

  def buildMediaItem(self, element, markUnread):
    if(element.subTitle == ""):
      title = "%s (%s)"%(element.title,element.duration);
    else:
      title = "%s - %s (%s)"%(element.title,element.subTitle,element.duration);

    if(type(element).__name__ == 'FeedItem'):
      title = "[%s] %s"%(time.strftime("%d.%m",element.date),title);

    if(markUnread and not element.readed):
      title = "(*) %s"%(title);
    else:
      title = "%s"%(title);

    liz=xbmcgui.ListItem(title);
    if(element.picture is not ""):
      liz.setArt({"icon":"DefaultFolder.png", "thumb":element.picture});
    else :
      liz.setArt({"icon":"DefaultFolder.png"});
    liz.setInfo("music",{
      "size": element.size,
      "date": time.strftime("%d.%m.%Y",element.date),
      "duration": self.durationStringToSec(element.duration),
      "year": int(time.strftime("%Y",element.date)),
      "artist": element.author,
      "title": title,
      "comment": element.description
      });
    return liz;

  def buildMenuEntry(self, menuElement, elementCount ):
    if(self.path == ""):
      path = "%d"%(self.counter);
    else:
      path = "%s.%d"%(self.path,self.counter);

    self.log(type(menuElement).__name__);
    if(type(menuElement).__name__ == 'FeedItem'):
      liz = self.buildMediaItem(menuElement,True);
      liz.addContextMenuItems([(translation(4020),"XBMC.RunPlugin(%s?path=%s&action=markRead)"%(sys.argv[0],path))],True)
      u = "%s?path=%s&action=play&guid=%s" % (sys.argv[0],path,menuElement.guid)
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

    else:
      if(menuElement.hasUnreadItems()):
        title = "(*) %s"%(menuElement.title);
      else:
        title = "%s"%(menuElement.title);
      self.log(menuElement.picture)
      if(menuElement.picture is not ""):
        liz=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=menuElement.picture)
      else :
        liz=xbmcgui.ListItem(title, "")

      contextMenuEntries = [
        (translation(30010),"XBMC.RunPlugin(%s?path=%s&action=markRead)"%(sys.argv[0],path)),
        (translation(30011),"XBMC.RunPlugin(%s?path=%s&action=play)"%(sys.argv[0],path)),
        (translation(30030),"XBMC.RunPlugin(%s?path=%s&action=reload)"%(sys.argv[0],path))
        ]
      liz.addContextMenuItems(contextMenuEntries,True)
      u = "%s?path=%s&action=browse" % (sys.argv[0],path)
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True,totalItems = elementCount)
    self.counter+=1;

  def play(self, playableObject):
    player = xbmc.Player();
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear();
    playerItem = xbmcgui.ListItem(playableObject.title)
    if(type(playableObject).__name__ == 'FeedItem'):
      self.log("play(): " + playableObject.link);
      player.play(str(playableObject.link),playerItem);
    else:
      items = [];
      playableObject.getAllUnreadItems(items);

      for item in items:
        listItem = self.buildMediaItem(item,False);
        playlist.add(url=item.link, listitem=listItem)

      player.play(playlist, playerItem);
      xbmc.executebuiltin("ActivateWindow(musicplaylist)");

  def openMenuContext(self):
    self.counter = 0;
    self.dialogProgress = xbmcgui.DialogProgress();

  @staticmethod
  def closeMenuContext():
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

  @staticmethod
  def refresh():
    xbmc.executebuiltin("Container.Refresh")

  @staticmethod
  def durationStringToSec(durationString):
    if(durationString is not None and regex_duration.match(durationString) is not None):
      decimalArray = regex_decimal.findall(durationString);
      if(len(decimalArray)==3):
        return int(decimalArray[0])*3600 + int(decimalArray[1])*60 +int(decimalArray[2])
      elif(len(decimalArray)==2):
        return int(decimalArray[0])*60 +int(decimalArray[1])
      else:
        return int(decimalArray[0])
    else:
      return 0;

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
