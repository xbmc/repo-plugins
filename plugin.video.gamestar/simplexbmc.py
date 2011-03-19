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
import xbmc, xbmcgui, xbmcplugin,xbmcaddon, sys, urllib, urllib2, os,re
__plugin__ = "Gamestar"

regex_getTargetPath = re.compile("[^/]*\\..{3}$");

class SimpleXbmcGui(object):
  def __init__(self, archivePath):
    self.archivePath = archivePath;
    
  def log(self, msg):
    if type(msg) not in (str, unicode):
      xbmc.output("[%s]: %s" % (__plugin__, type(msg)))
    else:
      xbmc.output("[%s]: %s" % (__plugin__, msg.encode('utf8')))
    
  def buildVideoLink(self,videoItem,forcePrecaching):
    
    title = videoItem.title
    listItem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=videoItem.picture)
    
    if(not forcePrecaching):
      listItem.setProperty('IsPlayable', 'true');
      
    url = videoItem.url;
    if(self.archivePath is not None):
      targetFile = regex_getTargetPath.search(url).group()
      targetFile = os.path.join(self.archivePath, targetFile);
      if(os.path.exists(targetFile)):
        url = targetFile;
        listItem.addContextMenuItems([("Download","XBMC.RunPlugin(%s?url=%s&action=download)"%(sys.argv[0],url))])
      elif(forcePrecaching):
        listItem.addContextMenuItems([("Download","XBMC.RunPlugin(%s?url=%s&action=downloadPlay)"%(sys.argv[0],url))])
        url = "%s?url=%s&action=downloadPlay"%(sys.argv[0],url);
      else:
        listItem.addContextMenuItems([("Download","XBMC.RunPlugin(%s?url=%s&action=download)"%(sys.argv[0],url))])
    self.log(url);  
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listItem,isFolder=False)
    

  def buildCategoryLink(self,galleryItem):
    addon = xbmcaddon.Addon("plugin.video.gamestar")
    GetString = addon.getLocalizedString
    title = GetString(galleryItem.title)
    listItem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=galleryItem.picture)
      
    u = "%s?&action=list&cat=%s" % (sys.argv[0], galleryItem.index)
      
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=listItem,isFolder=True)
  
  def openMenuContext(self):
    self.dialogProgress = xbmcgui.DialogProgress();
  
  def closeMenuContext(self):
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
  def download(self, sourceUrl):
    targetFile = regex_getTargetPath.search(sourceUrl).group();
    targetFile = os.path.join(self.archivePath,targetFile);
    self.log("starte download %s to %s "%(sourceUrl,targetFile));
    self.dp = xbmcgui.DialogProgress()
    self.dp.create("GamestarVideo","Downloading File",sourceUrl)
    if os.path.exists(targetFile+".tmp"):
      os.remove(targetFile+".tmp");
    if os.path.exists(targetFile):
      os.remove(targetFile);
    urllib.urlretrieve(sourceUrl,targetFile+".tmp",lambda nb, bs, fs, url=sourceUrl: self._pbhook(nb,bs,fs,sourceUrl,self.dp))
    os.rename(targetFile+".tmp",targetFile);
    return targetFile;
  
  def _pbhook(self, numblocks, blocksize, filesize, url=None,dp=None):
    try:
      percent = min((numblocks*blocksize*100)/filesize, 100)
      self.dp.update(percent)
    except:
      percent = 100
      self.dp.update(percent)
      if dp.iscanceled():
        self.dp.close()
        sys.exit("Download aborted")
        
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
