# -*- coding: utf-8 -*- 
#-------------LicenseHeader--------------
# plugin.video.Mediathek - Gives acces to the most video-platforms from german public service broadcaster
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
import re,time,traceback
import zipfile
import StringIO
from mediathek import *
from xml.dom import minidom;
import sys, urllib2,urllib, time;
import socket
socket.setdefaulttimeout(1);

class BayerischesFSMediathek(Mediathek):
  @classmethod
  def name(self):
    return "BayernFS";
  def isSearchable(self):
    return False;
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    
    if(self.gui.preferedStreamTyp == 0):
      self.baseType = "rtsp_mov_http"
    else:
      self.baseType = "rtsp_mov_http"
    
    self.root_url="http://mediathek-video.br.de/js/config.js";
    self.regexp_findArchive=re.compile("http://.*/archive/archive\.xml\.zip\.adler32");
    
    self.menuTree = (
      TreeNode("0","Alle","http://LoadAll",True),
      );


  def buildPageMenu(self, link, initCount):
    self.gui.log("buildPageMenu: "+link);

    a=self.loadAndUnzip();
    print a
    try:
      self.xml_cont = minidom.parseString(a); 
    except:
      self.menuTree = (
        TreeNode("0","Plugin Broken, Sry ;)","http://LoadAll",False,initCount),
      );
      return;
    displayItems=[];
    for itemNode in self.xml_cont.getElementsByTagName("ausstrahlung"):
      displayItem = self.extractVideoInformation(itemNode);
      if(displayItem is not None):
        displayItems.append(displayItem);
    itemCount = len(displayItems) +initCount    
    for displayItem in sorted(displayItems, key = lambda item:item.date, reverse=True):
      self.gui.buildVideoLink(displayItem,self,itemCount);
  def readText(self,node,textNode):
    try:
      node = node.getElementsByTagName(textNode)[0].firstChild;
      return unicode(node.data);
    except:
      return "";
  
  def loadAndUnzip(self):
    configDoc = self.loadPage(self.root_url)
    archiveLink = self.regexp_findArchive.search(configDoc).group();
    
    req = urllib2.Request(archiveLink);
    req.add_header('User-Agent', 'Mozilla/5.0')
    req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    req.add_header('Accept-Language', 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3')
    req.add_header('Accept-Charset', 'utf-8')
    waittime = 2;
    doc = False;
    
    self.gui.log("loadAndUnzip: download %s"%(archiveLink));
    
    while not doc and waittime < 60:
      try:
        if waittime > 0: 
          time.sleep(waittime);
          sock = urllib2.urlopen( req );
          doc = sock.read();
          if not doc: throw();
          sock.close();
      except:
          print("timeout after %d"%(waittime));
          waittime *= 2;
      if doc:
        break;
    
    try:
      zipf = zipfile.ZipFile(StringIO.StringIO(doc));
    except:
      print("Error Downloading ZIP");
      return '';
      
    for fileName in zipf.infolist():
      return zipf.read(fileName);

  def parseDate(self,dateString):
    return time.strptime(dateString,"%Y-%m-%dT%H:%M:%S");
    
  def extractVideoInformation(self, itemNode):
    title = self.readText(itemNode,"titel");
    
    dateString = self.readText(itemNode,"beginnPlan");
    pubDate = self.parseDate(dateString);
    
    try:
      subtitle = self.readText(itemNode,"nebentitel");
    except:
      subtitle = "";
    
    try:
      description = self.readText(itemNode,"beschreibung");
    except:
      description = "";
    
    try:
      picture = self.readText(itemNode,"bild");
    except:
      picture="";

    links = {};
    links[0] = SimpleLink("broken", 0);
    links[1] = SimpleLink("broken", 0);
    links[2] = SimpleLink("broken", 0);

    try:
      videos = itemNode.getElementsByTagName("videos")[0];
      if not videos.hasChildNodes():
        print "no videos";
        return None;

      for videotag in videos.getElementsByTagName("video"):
        print videotag.attributes;
        if (not videotag.hasAttribute("host")):
          return None;
        link = "rtmp://" + videotag.attributes["host"].value + "/" + videotag.attributes["application"].value + "/";
        if (videotag.attributes["groesse"].value == "small"):
            links[0] = SimpleLink(link+videotag.attributes["stream"].value, 0);
        if (videotag.attributes["groesse"].value == "large"):
            links[1] = SimpleLink(link+videotag.attributes["stream"].value, 0);
        if (videotag.attributes["groesse"].value == "xlarge"):
            links[2] = SimpleLink(link+videotag.attributes["stream"].value, 0);
    except:
      self.gui.log("Exception: ");
      traceback.print_exc();
      self.gui.log("Stacktrace: ");
      traceback.print_stack();
      
      return None;
    
    return DisplayObject(title,subtitle,picture,description,links,True, pubDate)
    
      
