# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
# plugin.video.Mediathek - Gives access to most video-platforms from German public service broadcasters
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
import sys, urllib2,urllib, time;
import socket
socket.setdefaulttimeout(1);

class SimpleLink(object):
  def __init__(self, basePath, size):
    self.basePath = basePath;
    self.size = size;
    
class ComplexLink(object):
  def __init__(self, basePath, playPath, size):
    self.basePath = basePath;
    self.playPath = playPath;
    self.size = size;

class TreeNode(object):
  def __init__(self,path,name,link,displayElements,childNodes = []):
     self.name = name;
     self.path = path;
     self.link = link;
     self.displayElements = displayElements;
     self.childNodes = childNodes;
     
class DisplayObject(object):
  def __init__(self,title,subTitle,picture,description,link=[],isPlayable = True, date = None, duration = None):
    self.title = title
    self.subTitle = subTitle
    self.link = link
    self.picture = picture
    self.isPlayable = isPlayable
    self.description = description
    self.date = date;
    self.duration = duration;

class Mediathek(object):
  
  def loadPage(self,url, values = None, maxTimeout = None):
    try:
      safe_url = url.replace( " ", "%20" ).replace("&amp;","&")
      
      if(values is not None): 
        data = urllib.urlencode(values)
        req = urllib2.Request(safe_url, data)
      else:
        req = urllib2.Request(safe_url)
      req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20100101 Firefox/15.0.1')
      req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
      req.add_header('Accept-Language', 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3')
      req.add_header('Accept-Charset', 'utf-8')
      
      if maxTimeout == None:
        maxTimeout = 60;
      
      waittime = 0;
      doc = False;
      while not doc and waittime < maxTimeout:
        try:
          if waittime > 0: 
            time.sleep(waittime);
          self.gui.log("download %s %d"%(safe_url,waittime));
          sock = urllib2.urlopen( req )
          doc = sock.read();
          sock.close()
        except:
          if(waittime == 0):
            waittime = 1;
          else:
            waittime *= 2;
            
      if doc:
        try:
          return doc.encode('utf-8');
        except:
          return doc;
      else:
        return ''
    except:
      return ''
      
  def buildMenu(self, path, treeNode = None):
    if(type(path) in (str,unicode)):
      path = path.split('.');
    if(len(path) > 0):
      index = int(path.pop(0));
    
      if(treeNode == None):
        treeNode = self.menuTree[index];
      else:
        treeNode = treeNode.childNodes[index];
      self.buildMenu(path,treeNode);
    else:
      if(treeNode == None):
        treeNode = self.menuTree[0];
      self.gui.log(treeNode.name);
      for childNode in treeNode.childNodes:
        self.gui.buildMenuLink(childNode,self, len(treeNode.childNodes));
      if(treeNode.displayElements):
        self.buildPageMenu(treeNode.link,len(treeNode.childNodes));
        
  def displayCategories(self):
    if(len(self.menuTree)>1 or not self.menuTree[0].displayElements):
      for treeNode in self.menuTree:
        self.gui.buildMenuLink(treeNode,self,len(self.menuTree)) 
    else:
      self.buildPageMenu(self.menuTree[0].link, 0);