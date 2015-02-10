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
    return True;
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    
    if(self.gui.preferedStreamTyp == 0):
      self.baseType = "rtsp_mov_http"
    else:
      self.baseType = "rtsp_mov_http"
    
    self.channel = "bfs"
    #self.channel = "bfsalpha"
    
    self.root_url="http://mediathek-video.br.de/js/config.js";
    self.regexp_findArchive=re.compile("http://.*/archive/archive\.xml\.zip\.adler32");
    
    self.menuTree = [
      TreeNode("0","Alle","LoadAll",True),
      TreeNode("1","Alle Mitschnitte","LoadAusstrahlung",True),
      TreeNode("2","Alle Podcasts","LoadPodcasts",True),
      ];
    
    #Zip Archiv einlesen
    a=self.loadAndUnzip();
    try:
      self.xml_cont = minidom.parseString(a); 
    except:
      self.menuTree = (
        TreeNode("0","Plugin Broken, Sry ;)","http://LoadAll",False,initCount),
      );
      return;

    #Alle Sendungen einlesen
    self.broadcasts = {}
    for itemNode in self.xml_cont.getElementsByTagName("sendungen")[0].getElementsByTagName("sendung"):
      broadcast = self.extractBroadcastInformation(itemNode);
      self.broadcasts[broadcast['id']] = broadcast;
    
    #Sendungen raussuchen, für die es Mitschnitte gibt
    self.sendungen = {}
    for itemNode in self.xml_cont.getElementsByTagName("ausstrahlung"):
      sender = itemNode.getAttribute("sender");
      sendung = self.readText(itemNode,"sendung")
      if not self.broadcasts[sendung]['sender']:
        self.broadcasts[sendung]['sender'] = sender
      if self.broadcasts[sendung]['sender'] != self.channel:
        self.broadcasts[sendung]['display'] = False
      else:
        videos = itemNode.getElementsByTagName("videos")[0];
        if videos.hasChildNodes():
          self.broadcasts[sendung]['display'] = True
    
    #Sendungen anzeigen
    displayItems=[];
    for broadcast in self.broadcasts.itervalues():
      if broadcast['display']:
        displayItems.append(broadcast);

    x=3
    for displayItem in sorted(displayItems, key = lambda item:item['name'].lower(), reverse=False):
      self.menuTree.append(TreeNode(str(x),displayItem['name'],displayItem['id'],True));
      x = x+1

  def buildPageMenu(self, link, initCount, searchText = ""):
    self.gui.log("buildPageMenu: "+link);
    displayItems=[];
    if not link == "LoadPodcasts":
      #Mitschnitte
      for itemNode in self.xml_cont.getElementsByTagName("ausstrahlung"):
        sendung = self.readText(itemNode,"sendung")
        if self.broadcasts[sendung]['sender'] == self.channel:
          if link == "LoadAusstrahlung" or link == "LoadAll" or link == "LoadSearch" or link == sendung:
            picture = self.broadcasts[sendung]["node"].getAttribute("bild")
            displayItem = self.extractVideoInformation(itemNode, picture, searchText);
            if(displayItem is not None):
              displayItems.append(displayItem);
    if not link == "LoadAusstrahlung":
      #Podcasts
      for itemNode in self.broadcasts.itervalues():
        if itemNode['sender'] == self.channel:
          if link == "LoadAll" or link == "LoadPodcasts" or link == "LoadSearch" or link == itemNode['id'] :
            if itemNode["node"].getElementsByTagName("podcasts")[0].hasChildNodes():
              podcasts  = itemNode["node"]
              for podcastFeed in podcasts.getElementsByTagName("podcasts")[0].getElementsByTagName("feed"):
                picture = self.readText(podcastFeed,"image")
                for podcastNode in podcastFeed.getElementsByTagName("podcast"):
                  displayItem = self.extractPodcastInformation(podcastNode,picture, searchText);
                  if(displayItem is not None):
                    displayItems.append(displayItem);

    itemCount = len(displayItems) +initCount    
    for displayItem in sorted(displayItems, key = lambda item:item.date, reverse=True):
      self.gui.buildVideoLink(displayItem,self,itemCount);

  def searchVideo(self, searchText):
    searchText = searchText.lower()
    self.buildPageMenu("LoadSearch", 0, searchText)

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
      
    for fileName in zipf.namelist():
      return zipf.read(fileName);

  def parseDate(self,dateString):
    return time.strptime(dateString,"%Y-%m-%dT%H:%M:%S");
 
  def extractBroadcastInformation(self,itemNode):
    broadcast = {}
    broadcast["id"] = itemNode.getAttribute("id")
    broadcast["name"] = itemNode.getAttribute("name")
    broadcast["bild"] = itemNode.getAttribute("bild")
    broadcast["sender"] = None
    if itemNode.getElementsByTagName("podcasts")[0].hasChildNodes() and self.channel == "bfs":
      broadcast["display"] = True
    else:
      broadcast["display"] = False
    broadcast["node"] = itemNode
    return broadcast
    
  def extractVideoInformation(self, itemNode, picture = "", searchText = ""):
    title = self.readText(itemNode,"titel");
    
    dateString = self.readText(itemNode,"beginnPlan");
    pubDate = self.parseDate(dateString);
    
    subtitle = self.readText(itemNode,"nebentitel");
      
    description = self.readText(itemNode,"beschreibung");
    
    
    if not searchText == "":
      if not searchText in title.lower() and not searchText in description.lower():
          return None;
    
    links = {};

    try:
      videos = itemNode.getElementsByTagName("videos")[0];
      if not videos.hasChildNodes():
        #print "no videos";
        return None;

      for videotag in videos.getElementsByTagName("video"):
        #print videotag.attributes;
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
    
    startBei =  (self.readText(itemNode,"startBei"));
    endeBei =  (self.readText(itemNode,"endeBei"));
    
    duration = 0
    if startBei.strip() and endeBei.strip():
      duration = str((int(endeBei)+int(startBei))/1000)
    
    return DisplayObject(title,subtitle,picture,description,links,True, pubDate, duration)
    
  def extractPodcastInformation(self, itemNode, picture = "", searchText = ""):
    title = self.readText(itemNode,"title");
    
    dateString = self.readText(itemNode,"pubdate");
    pubDate = self.parseDate(dateString);
    
    description = self.readText(itemNode,"description");
    
    duration = self.readText(itemNode,"duration");

    link = itemNode.getElementsByTagName("enclosure")[0].getAttribute("streamurl");

    links = {};
    links[0] = SimpleLink(link, 0);
    
    if not searchText == "":
      if not searchText in title.lower() and not searchText in description.lower():
          return None;
    
    return DisplayObject(title,"",picture,description,links,True, pubDate, duration)
    
      
