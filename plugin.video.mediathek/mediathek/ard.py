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
import re, time, datetime, json;
from bs4 import BeautifulSoup;
from mediathek import *

class ARDMediathek(Mediathek):
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    self.rootLink = "https://www.ardmediathek.de"
    self.menuTree = (
                      TreeNode("0" ,"ARD"          ,self.rootLink+"/ard/",True),
                      TreeNode("1" ,"Das Erste"    ,self.rootLink+"/daserste/",True),
                      TreeNode("2" ,"BR"           ,self.rootLink+"/br/",True),
                      TreeNode("3" ,"HR"           ,self.rootLink+"/hr/",True),
                      TreeNode("4" ,"MDR"          ,self.rootLink+"/mdr/",True),
                      TreeNode("5" ,"NDR"          ,self.rootLink+"/ndr/",True),
                      TreeNode("6" ,"Radio Bremen" ,self.rootLink+"/radiobremen/",True),
                      TreeNode("7" ,"RBB"          ,self.rootLink+"/rbb/",True),
                      TreeNode("8" ,"SR"           ,self.rootLink+"/sr/",True),
                      TreeNode("9" ,"SWR"          ,self.rootLink+"/swr/",True),
                      TreeNode("10","WDR"          ,self.rootLink+"/wdr/",True),
                      TreeNode("11","ONE"          ,self.rootLink+"/one/",True),
                      TreeNode("12","ARD-alpha"    ,self.rootLink+"/alpha/",True)
                      )
    self.configLink = self.rootLink+"/play/media/%s?devicetype=pc&feature=flash"
    self.regex_VideoPageLink = re.compile("<a href=\".*Video\?.*?documentId=(\d+).*?\" class=\"textLink\">\s+?<p class=\"dachzeile\">(.*?)<\/p>\s+?<h4 class=\"headline\">(.*?)<\/h4>\s+?<p class=\"subtitle\">(?:(\d+.\d+.\d+) \| )?(\d*) Min.")
    self.regex_CategoryPageLink = re.compile("<a href=\"(.*(?:Sendung|Thema)\?.*?documentId=\d+.*?)\" class=\"textLink\">(?:.|\n)+?<h4 class=\"headline\">(.*?)<\/h4>")
    self.pageSelectString = "&mcontent%s=page.%s"
    self.regex_DetermineSelectedPage = re.compile("&mcontents{0,1}=page.(\d+)");

    self.regex_videoLinks = re.compile("\"_quality\":(\d).*?\"_stream\":\[?\"(.*?)\"");
    self.regex_pictureLink = re.compile("_previewImage\":\"(.*?)\"");


    self.regex_Date = re.compile("\\d{2}\\.\\d{2}\\.\\d{2}");


    self.replace_html = re.compile("<.*?>");
    self.regex_DetermineClient = re.compile(self.rootLink+"/(.*)/");
    self.categoryListingKey = "$ROOT_QUERY.widget({\"client\":\"%s\",\"pageNumber\":%s,\"pageSize\":%s,\"widgetId\":\"%s\"})"
    self.playerLink = self.rootLink+"/ard/player/%s"
    self.regex_ExtractJson = re.compile("__APOLLO_STATE__ = ({.*});");
    self.tumbnail_size = "600";

  @classmethod
  def name(self):
    return "ARD";
  def isSearchable(self):
    return False;
  def extractJsonFromPage(self,link):
    pageContent = self.loadPage(link).decode('UTF-8');
    content = self.regex_ExtractJson.search(pageContent).group(1);
    pageContent = BeautifulSoup(content,"html.parser");
    jsonContent= pageContent.prettify(formatter=None);
    return json.loads(jsonContent);

  def buildPageMenu(self, link, initCount):
    self.gui.log("Build Page Menu: %s"%(link));
    jsonContent = self.extractJsonFromPage(link);
    callHash = self.gui.storeJsonFile(jsonContent);
    client = self.regex_DetermineClient.search(link).group(1);

    for key in jsonContent:
      if(key.startswith("Widget:")):
        self.GenerateCaterogyLink(jsonContent[key], callHash, jsonContent, client);
    return 0;

  def GenerateCaterogyLink(self, widgetContent, callHash, jsonContent,client):
    widgetId = widgetContent["id"];
    title = widgetContent["title"];
    if(widgetContent["titleVisible"] == True):
      self.gui.buildJsonLink(self, title, "%s.%s"%(client,widgetId), callHash,0);
    else:
      widgetContent = jsonContent[self.buildcategoryListingKey(client,widgetId,jsonContent)];
      self.GenerateCaterogyLinks(widgetContent, jsonContent)

  def buildcategoryListingKey(self,client,widgetId,jsonContent):
    #ich werd zum elch... erst noch die "dynamische" Pagesize/Number nachschlagen ...
    widgetContent = jsonContent["Widget:%s"%widgetId];
    paginationId = widgetContent["pagination"]["id"];
    paginationContent = jsonContent[paginationId];
    pageSize = paginationContent["pageSize"];
    pageNumber = paginationContent["pageNumber"];

    return self.categoryListingKey%(client,pageNumber,pageSize,widgetId);

  def buildJsonMenu(self, path, callhash, initCount):
    jsonContent = self.gui.loadJsonFile(callhash);
    path = path.split(".");
    client = path[0];
    widgetId = path[1];

    widgetContent = jsonContent[self.buildcategoryListingKey(client,widgetId,jsonContent)];
    self.GenerateCaterogyLinks(widgetContent, jsonContent)

  def GenerateCaterogyLinks(self, widgetContent, jsonContent):
    for teaser in widgetContent["teasers"]:
      teaserId = teaser["id"];
      self.GenerateVideoLink(jsonContent[teaserId],jsonContent);

  def GenerateVideoLink(self, teaserContent, jsonContent):
    title = teaserContent["shortTitle"];
    subTitle = None;
    picture = self.getPictureLink(teaserContent["images"],jsonContent);
    videoLinks = self.getVideoLinks(teaserContent["links"],jsonContent);
    if(teaserContent["broadcastedOn"] is not None):
      date = time.strptime(teaserContent["broadcastedOn"],"%Y-%m-%dT%H:%M:%SZ");
    else:
      date = None;
    duration = teaserContent["duration"];
    self.gui.buildVideoLink(DisplayObject(title, subTitle, picture,"",videoLinks,"JsonLink",date,duration),self,0);

  def getVideoLinks(self, linkSource, jsonContent):
    #WTF geht es noch sinnloser?
    key = linkSource["id"]
    key = jsonContent[key]["target"]["id"];
    return self.playerLink%jsonContent[key]["id"];

  def getPictureLink(self, pictureSource, jsonContent):
    if(pictureSource is not None):
      key=pictureSource["id"];
      pictureConfig = jsonContent[key];
      for key in pictureConfig:
        if(key.startswith("aspect") and pictureConfig[key] is not None):
          key = pictureConfig[key]["id"];
          return jsonContent[key]["src"].replace("{width}",self.tumbnail_size);
    return None;

  def playVideoFromJsonLink(self,link):
    #WTF OHHHHHHHHH JAAAAAA - es geht noch sinnloser...
    jsonContent = self.extractJsonFromPage(link);

    videoLinks = {}
    for key in jsonContent:
      if("_mediaStreamArray." in key):
        streamConfig = jsonContent[key];
        if(streamConfig["_quality"] == "auto"):
          quality = 3;
        else:
          quality = int(streamConfig["_quality"]);
        link = streamConfig["_stream"]["json"][0];
        if(not link.startswith("http")):
          link = "https:"+link;
        self.gui.log("VideoLink: "+link);
        videoLinks[quality] = SimpleLink(link,-1);

    self.gui.play(videoLinks);
