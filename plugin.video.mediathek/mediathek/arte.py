## -*- coding: utf-8 -*-
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
import re, traceback, urllib,json;
from mediathek import *
from xml.dom import minidom
from xml.dom import Node;
from bs4 import BeautifulSoup;

regex_dateString = re.compile("\\d{1,2} ((\\w{3})|(\\d{2})) \\d{4}");
month_replacements = {
    "Jan":"01",
    "Feb":"02",
    "Mar":"03",
    "Apr":"04",
    "May":"05",
    "Jun":"06",
    "Jul":"07",
    "Aug":"08",
    "Sep":"09",
    "Oct":"10",
    "Nov":"11",
    "Dec":"12",
  };

class ARTEMediathek(Mediathek):
  @classmethod
  def name(self):
    return "ARTE";
  @classmethod
  def isSearchable(self):
    return False;

  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    self.rootLink = "http://www.arte.tv";
    self.basePage = self.rootLink+"/guide/de/plus7";
    self.jsonLink = "https://api.arte.tv/api/player/v1/config/de/%s"

    self.menuTree = (
      TreeNode("0","Arte+7","mainPage",True),
      TreeNode("1","Sendungen von A-Z","showCluster",True),
      TreeNode("2","Kategorien","showCategories",True),
    );

    self.selector_videoPages = "li.video > a";

    self.regex_VideoPageLinksHTML = re.compile("href=[\"'](http:\\\\/\\\\/www\\.arte\\.tv\\\\/guide\\\\/de\\\\/\d{6}-\d{3}/.+?)[\"']");
    self.regex_VideoPageLinksJSON = re.compile("\"url\":\"((http:\\\\/\\\\/www\\.arte\\.tv){0,1}\\\\/guide\\\\/de\\\\/\d{6}-\d{3}\\\\/.+?)\"");
    self.regex_findVideoIds = re.compile("(\d{6}-\d{3})(-A)");
    self.regex_JSONPageLink = re.compile("http://arte.tv/papi/tvguide/videos/stream/player/D/\d{6}-\d{3}.+?/ALL/ALL.json");
    self.regex_JSON_VideoLink = re.compile("\"HTTP_MP4_.+?\":{.*?\"bitrate\":(\d+),.*?\"url\":\"(http://.*?.mp4)\".*?\"versionShortLibelle\":\"([a-zA-Z]{2})\".*?}");
    self.regex_JSON_ImageLink = re.compile("\"IUR\":\"(http://.*?\\.arte\\.tv/papi/tvguide/images/.*?\\..{3})\"");
    self.regex_JSON_Detail = re.compile("\"VDE\":\"(.*?)\"");
    self.regex_JSON_Titel = re.compile("\"VTI\":\"(.*?)\"");

    regexSourceString="%s=\"([\[{].*?[}\]])\"";
    self.regex_cluster=re.compile(regexSourceString%"data-clusters");
    self.regex_categories = re.compile(regexSourceString%"data-categoriesVideos");
    self.regex_playlists = re.compile(regexSourceString%"data-highlightedPlaylists");

    self.categories = {
      "DailyMostViewed":re.compile(regexSourceString%"data-dailyMostViewedVideos"),
      "Most Viewed": re.compile(regexSourceString%"data-mostViewedVideos"),
      "ExpiringVideos":re.compile(regexSourceString%"data-nextExpiringVideos"),
    }

    self.regex_extractVideoSources = (
        re.compile(regexSourceString%"data-highlightedVideos"),
        re.compile(regexSourceString%"data-latestVideos"),
        re.compile(regexSourceString%"data-categoryVideoSet"),
      );




  def buildPageMenu(self, link, initCount):
    if(link == "showCluster"):
      self.showCluster();
    elif (link == "mainPage"):
      self.showMainPage();
    elif (link == "showCategories"):
      self.showCategories();
    else:
      if(not link.startswith("http")):
        link = self.rootLink+link;
      pageContent = self.loadPage(link).decode('UTF-8');
      linkFound = self.extractVideoLinksFromHtml(pageContent)
      if(not linkFound):
        self.extractVideoLinks(pageContent,0);

  def buildJsonMenu(self, path,callhash, initCount):
    jsonContent=self.gui.loadJsonFile(callhash);
    if(path == "init"):
      jsonObject = jsonContent;
    else:
      jsonObject=self.walkJson(path,jsonContent);
    self.gui.log(json.dumps(jsonObject));
    if("videos" in jsonObject):
      self.extractVideoLinksFromJson(jsonObject);
    if(isinstance(jsonObject,list)):
      for counter,jsonObject in enumerate(jsonObject):
        if("day" in jsonObject):
          self.gui.buildJsonLink(self,jsonObject["day"],"%d"%counter,callhash,0)

  def buildJsonLink(self,name,content):
    content = BeautifulSoup(content);
    jsonContent = json.loads(content.prettify(formatter=None))
    callhash = self.gui.storeJsonFile(jsonContent,name);
    self.gui.buildJsonLink(self,name,"init",callhash,0)

  def showMainPage(self):
    self.gui.log("buildPageMenu: "+self.basePage);
    pageContent = self.loadPage(self.basePage).decode('UTF-8');

    for name,regex in self.categories.iteritems():
      match = regex.search(pageContent);
      if(match is not None):
        self.buildJsonLink(name,match.group(1));

    self.extractVideoLinksFromHtml(pageContent)

  def extractVideoLinksFromHtml(self, htmlPage):
    someMatch = False;
    for regex in self.regex_extractVideoSources:
      match = regex.search(htmlPage);
      if(match is not None):
        someMatch = True;
        content = BeautifulSoup(match.group(1));
        jsonContent = json.loads(content.prettify(formatter=None))
        self.extractVideoLinksFromJson(jsonContent)
    return someMatch;


  def extractVideoLinksFromJson(self,jsonContent):
    for jsonObject in jsonContent["videos"]:
        self.buildVideoEntry(jsonObject);

  def showCluster(self):
    pageContent = self.loadPage(self.basePage).decode('UTF-8');
    content = BeautifulSoup(self.regex_cluster.search(pageContent).group(1));
    jsonContent = json.loads(content.prettify(formatter=None))
    for menuItem in jsonContent:
      self.buildMenuEntry(menuItem);

  def showCategories(self):
    pageContent = self.loadPage(self.basePage).decode('UTF-8');
    content = BeautifulSoup(self.regex_categories.search(pageContent).group(1));
    jsonContent = json.loads(content.prettify(formatter=None))
    for jsonObject in jsonContent:
      jsonCategorie = jsonObject["category"]
      title = unicode(jsonCategorie["title"]);
      link=jsonCategorie["url"];
      self.gui.buildVideoLink(DisplayObject(title,"","","",link,False,None),self,0);

  def buildMenuEntry(self, menuItem):
    title = menuItem["title"];
    subTitle = menuItem["subtitle"];
    link=menuItem["permalink"];
    self.gui.buildVideoLink(DisplayObject(title,subTitle,"","",link,False,None),self,0);

  def buildVideoEntry(self, jsonObject):
    title = jsonObject["title"];
    subTitle = jsonObject["subtitle"];
    detail = jsonObject["teaser"];
    picture = None;
    for pictureItem in jsonObject["thumbnails"]:
      if(picture is None or picture["width"]<pictureItem["width"]):
        picture = pictureItem;
    link=self.jsonLink%jsonObject["id"];
    self.gui.buildVideoLink(DisplayObject(title,"",picture["url"],detail,link,"JsonLink", None),self,0);


  def playVideoFromJsonLink(self,link):
    jsonObject = json.loads(self.loadPage(link));
    links = self.extractLinks(jsonObject["videoJsonPlayer"]);
    self.gui.play(links);


  def extractLinks(self,jsonObject):
    links={};

    vsrObjects = jsonObject["VSR"];
    if(not isinstance(vsrObjects,dict)):
      return links;

    for videoObject in jsonObject["VSR"].itervalues():
      if videoObject["mediaType"] == "mp4":
        url = videoObject["url"];
        quality = videoObject["quality"];
        self.gui.log("%s %s"%(quality,url))
        if quality == "MQ":
          links[0] = SimpleLink(url, -1); 
        if quality == "HQ":
          links[1] = SimpleLink(url, -1); 
        if quality == "EQ":
          links[2] = SimpleLink(url, -1); 
        if quality == "SQ":
          links[3] = SimpleLink(url, -1);
    return links;

  def extractVideoLinks(self, htmlPage, initCount):
    links = set();
    jsonLinks = set();
    for videoPageLink in self.regex_findVideoIds.finditer(htmlPage):
      link = self.jsonLink%videoPageLink.group(1)
      self.gui.log(link);
      if(link not in jsonLinks):
        jsonLinks.add(link);

    for videoPageLink in self.regex_VideoPageLinksJSON.finditer(htmlPage):
      link = videoPageLink.group(1).replace("\\/","/");
      if(link not in links):
        links.add(link);
    for link in self.regex_JSONPageLink.finditer(htmlPage):
      jsonLinks.add(link.group(0));
    linkCount = initCount + len(links);
    for link in links:
      if(not link.startswith(self.rootLink)):
        videoPage = self.loadPage(self.rootLink+link);
      else:
        videoPage = self.loadPage(link);
      match = self.regex_JSONPageLink.search(videoPage);
      if(match is not None):
        jsonLinks.add(match.group(0));

    linkCount = linkCount + len(jsonLinks);

    self.gui.log("Found %s unique links"%len(jsonLinks));
    for link in jsonLinks:
      jsonPage = json.loads(self.loadPage(link));
      self.extractVideoLinksFromJSONPage(jsonPage["videoJsonPlayer"],linkCount)

  def extractVideoLinksFromJSONPage(self, jsonPage, linkCount):

    videoLinks = self.extractLinks (jsonPage);
    if(len(videoLinks) == 0):
      return;

    picture = jsonPage["VTU"]["IUR"];
    title = jsonPage["VTI"];

    subTitle = ""
    if("subtitle" in jsonPage):
      subTitle = jsonPage["subtitle"];


    self.gui.buildVideoLink(DisplayObject(title,subTitle,picture,"",videoLinks,True, None),self,linkCount);
