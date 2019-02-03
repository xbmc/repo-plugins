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
import re,traceback,time
from mediathek import *
from datetime import datetime,timedelta
import json

class ZDFMediathek(Mediathek):
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;

    today = datetime.today();

    self.menuTree = (
      TreeNode("0","Startseite","https://zdf-cdn.live.cellular.de/mediathekV2/start-page",True),
      TreeNode("1","Kategorien","",False,(
          TreeNode("1.0",u"Comedy/Show"         ,"https://zdf-cdn.live.cellular.de/mediathekV2/document/comedy-und-show-100",True),
          TreeNode("1.1",u"Doku/Wissen"         ,"https://zdf-cdn.live.cellular.de/mediathekV2/document/doku-wissen-104",True),
          TreeNode("1.2",u"Filme"               ,"https://zdf-cdn.live.cellular.de/mediathekV2/document/filme-104",True),
          TreeNode("1.3",u"Geschichte"          ,"https://zdf-cdn.live.cellular.de/mediathekV2/document/geschichte-108",True),
          TreeNode("1.4",u"nachrichten"         ,"https://zdf-cdn.live.cellular.de/mediathekV2/document/nachrichten-100",True),
          TreeNode("1.5",u"Kinder/ZDFtivi"      ,"https://zdf-cdn.live.cellular.de/mediathekV2/document/kinder-100",True),
          TreeNode("1.6",u"Krimi"               ,"https://zdf-cdn.live.cellular.de/mediathekV2/document/krimi-102",True),
          TreeNode("1.7",u"Kultur"              ,"https://zdf-cdn.live.cellular.de/mediathekV2/document/kultur-104",True),
          TreeNode("1.8",u"Politik/Gesellschaft","https://zdf-cdn.live.cellular.de/mediathekV2/document/politik-gesellschaft-102",True),
          TreeNode("1.9",u"Serien"              ,"https://zdf-cdn.live.cellular.de/mediathekV2/document/serien-100",True),
          TreeNode("1.10",u"Sport"              ,"https://zdf-cdn.live.cellular.de/mediathekV2/document/sport-106",True),
          TreeNode("1.11",u"Verbraucher"        ,"https://zdf-cdn.live.cellular.de/mediathekV2/document/verbraucher-102",True),
        )),
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
    return True;

  def searchVideo(self, searchText):
    self.buildPageMenu("https://zdf-cdn.live.cellular.de/mediathekV2/search?q=%s"%searchText,0);

  def buildPageMenu(self, link, initCount):
    self.gui.log("buildPageMenu: "+link);
    jsonObject = json.loads(self.loadPage(link));
    callhash = self.gui.storeJsonFile(jsonObject);

    if("stage" in jsonObject):
      for stageObject in jsonObject["stage"]:
        if(stageObject["type"]=="video"):
          self.buildVideoLink(stageObject,initCount);
    if("results" in jsonObject):
      for stageObject in jsonObject["results"]:
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
      if entry["type"] == "video":
        videoObjects.append(entry);
    self.gui.log("CategoriePages: %d"%len(categoriePages));
    self.gui.log("VideoPages: %d"%len(videoObjects));
    for categoriePage in categoriePages:
      title=categoriePage["titel"];
      subTitle=categoriePage["beschreibung"];
      imageLink="";
      for width,imageObject in list(categoriePage["teaserBild"].items()):
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
    if("beschreibung" in videoObject):
      description=videoObject["beschreibung"];
    imageLink="";
    if("teaserBild" in videoObject):
      for width,imageObject in list(videoObject["teaserBild"].items()):
        if int(width)<=840:
          imageLink=imageObject["url"];
    if("visibleFrom" in videoObject):
      date = time.strptime(videoObject["visibleFrom"],"%d.%m.%Y %H:%M");
    else:
      date = time.gmtime();
    if("formitaeten" in videoObject):
      links = self.extractLinks(videoObject);
      self.gui.buildVideoLink(DisplayObject(title,subTitle,imageLink,description,links,True,date,videoObject.get('length')),self,counter);
    else:
      link = videoObject["url"];
      self.gui.buildVideoLink(DisplayObject(title,subTitle,imageLink,description,link,"JsonLink",date,videoObject.get('length')),self,counter);

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

