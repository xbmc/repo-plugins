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
import re,math,traceback,time
from mediathek import *
from datetime import datetime,timedelta
import json
    
class ZDFMediathek(Mediathek):
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    
    today = datetime.today();
    
    self.menuTree = (
      TreeNode("0","Startseite","https://zdf-cdn.live.cellular.de/mediathekV2/start-page",True),
      TreeNode("1","Kategorien","https://zdf-cdn.live.cellular.de/mediathekV2/categories",True),
      TreeNode("2","Sendungen von A-Z","https://zdf-cdn.live.cellular.de/mediathekV2/brands-alphabetical",True),
      TreeNode("3","Sendung verpasst?","",False,(
        TreeNode("3.0","Heute","https://zdf-cdn.live.cellular.de/mediathekV2/broadcast-missed/%s"%(today.strftime("%Y-%m-%d")),True),
        TreeNode("3.1","Gestern","https://zdf-cdn.live.cellular.de/mediathekV2/broadcast-missed/%s"%((today-timedelta(days=1)).strftime("%Y-%m-%d")),True),
        TreeNode("3.2","Vorgestern","https://zdf-cdn.live.cellular.de/mediathekV2/broadcast-missed/%s"%((today-timedelta(days=2)).strftime("%Y-%m-%d")),True),
        TreeNode("3.3",(today-timedelta(days=3)).strftime("%A"),"https://zdf-cdn.live.cellular.de/mediathekV2/broadcast-missed/%s"%((today-timedelta(days=3)).strftime("%Y-%m-%d")),True),
        TreeNode("3.4",(today-timedelta(days=4)).strftime("%A"),"https://zdf-cdn.live.cellular.de/mediathekV2/broadcast-missed/%s"%((today-timedelta(days=4)).strftime("%Y-%m-%d")),True),
        TreeNode("3.5",(today-timedelta(days=5)).strftime("%A"),"https://zdf-cdn.live.cellular.de/mediathekV2/broadcast-missed/%s"%((today-timedelta(days=5)).strftime("%Y-%m-%d")),True),
        TreeNode("3.6",(today-timedelta(days=6)).strftime("%A"),"https://zdf-cdn.live.cellular.de/mediathekV2/broadcast-missed/%s"%((today-timedelta(days=6)).strftime("%Y-%m-%d")),True),
        TreeNode("3.7",(today-timedelta(days=7)).strftime("%A"),"https://zdf-cdn.live.cellular.de/mediathekV2/broadcast-missed/%s"%((today-timedelta(days=7)).strftime("%Y-%m-%d")),True),
        )),
      TreeNode("4","Live TV","https://zdf-cdn.live.cellular.de/mediathekV2/live-tv/%s"%(today.strftime("%Y-%m-%d")),True)
      );
  @classmethod
  def name(self):
    return "ZDF";
    
  def isSearchable(self):
    return False;
  
  def searchVideo(self, searchText):
    return;
    
  def buildPageMenu(self, link, initCount):
    self.gui.log("buildPageMenu: "+link);
    jsonObject = json.loads(self.loadPage(link));
    callhash = self.gui.storeJsonFile(jsonObject);
    
    if("stage" in jsonObject):
      for stageObject in jsonObject["stage"]:
        if(stageObject["type"]=="video"):
          self.buildVideoLink(stageObject,initCount);
    
    if("cluster" in jsonObject):
      for counter, clusterObject in enumerate(jsonObject["cluster"]):
        if "teaser" in clusterObject and "name" in clusterObject:
          path = "cluster.%d.teaser"%(counter)
          self.gui.buildJsonLink(self,clusterObject["name"],path,callhash,initCount)
    if("broadcastCluster" in jsonObject):
      for counter, clusterObject in enumerate(jsonObject["broadcastCluster"]):
        if clusterObject["type"].startswith("teaser") and "name" in clusterObject:
          path = "broadcastCluster.%d.teaser"%(counter)
          self.gui.buildJsonLink(self,clusterObject["name"],path,callhash,initCount)
    if("epgCluster" in jsonObject):
      for epgObject in jsonObject["epgCluster"]:
        if("liveStream" in epgObject and len(epgObject["liveStream"])>0):
          self.buildVideoLink(epgObject["liveStream"], initCount);
    
          
        
  def buildJsonMenu(self, path,callhash, initCount):
    jsonObject=self.gui.loadJsonFile(callhash);
    jsonObject=self.walkJson(path,jsonObject);
   
    categoriePages=[];
    videoObjects=[];
    
    for entry in jsonObject:
      if entry["type"] == "brand":
        categoriePages.append(entry);
      if entry["type"] == "video" and len(videoObjects) < 50:
        videoObjects.append(entry);  
    
    self.gui.log("CategoriePages: %d"%len(categoriePages));
    self.gui.log("VideoPages: %d"%len(videoObjects));  
    for categoriePage in categoriePages:
      title=categoriePage["titel"];
      subTitle=categoriePage["beschreibung"];
      imageLink="";
      for width,imageObject in categoriePage["teaserBild"].iteritems():
        if int(width)<=840:
          imageLink=imageObject["url"];
      url = categoriePage["url"];
      self.gui.buildVideoLink(DisplayObject(title,subTitle,imageLink,"",url,False),self,initCount);
    
    
    
    for videoObject in videoObjects:
      self.buildVideoLink(videoObject,initCount);
      
      
  def buildVideoLink(self,videoObject,counter):
    title=videoObject["headline"];
    subTitle=videoObject["titel"];
    
    if(len(title)==0):
      title = subTitle;
      subTitle = "";
    description=videoObject["beschreibung"];
    imageLink="";
    for width,imageObject in videoObject["teaserBild"].iteritems():
      if int(width)<=840:
        imageLink=imageObject["url"];
    if("formitaeten" in videoObject):
      links = self.extractLinks(videoObject);
      self.gui.buildVideoLink(DisplayObject(title,subTitle,imageLink,description,links,True,None,videoObject.get('length')),self,counter);
    else:
      link = videoObject["url"];
      self.gui.buildVideoLink(DisplayObject(title,subTitle,imageLink,description,link,"JsonLink",None,videoObject.get('length')),self,counter);
    
  def playVideoFromJsonLink(self,link):
    jsonObject = json.loads(self.loadPage(link));
    links = self.extractLinks(jsonObject["document"]);
    self.gui.play(links);
  def extractLinks(self,jsonObject):
    links={};
    for formitaete in jsonObject["formitaeten"]:
      url = formitaete["url"];
      quality = formitaete["quality"];
      hd = formitaete["hd"];
      self.gui.log("quality:%s hd:%s url:%s"%(quality,hd,url));
      if hd == True:
        links[4] = SimpleLink(url, -1); 
      else:
        if quality == "low":
          links[0] = SimpleLink(url, -1); 
        if quality == "med":
          links[1] = SimpleLink(url, -1); 
        if quality == "high":
          links[2] = SimpleLink(url, -1); 
        if quality == "veryhigh":
          links[3] = SimpleLink(url, -1);
        if quality == "auto":
          links[3] = SimpleLink(url, -1);
    return links;
    
      
    

    
    
