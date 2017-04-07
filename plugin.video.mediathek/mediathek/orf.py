# -*- coding: utf-8 -*-
# -------------LicenseHeader--------------
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
import re,json,urllib;
from mediathek import *
from bs4 import BeautifulSoup;

class ORFMediathek(Mediathek):
  def __init__(self, simpleXbmcGui):

    self.rootLink = "http://tvthek.orf.at"
    self.gui = simpleXbmcGui;
    self.menuTree = [];
    self.menuTree.append(TreeNode("0","Startseite","http://tvthek.orf.at/",True));
    self.menuTree.append(TreeNode("1","Sendungen","http://tvthek.orf.at/profiles/a-z",True));


    self.searchLink = "http://tvthek.orf.at/search?q=%s"




    self.regex_extractProfileSites = re.compile("<a class=\"item_inner clearfix\"\s*?href=\"(http://tvthek.orf.at/profile/.*?/\d+)\".*src=\"(http://api-tvthek.orf.at/uploads/media/profiles/.*?_profiles_list.jpeg)\"(.|\s)*?<h4 class=\"item_title\">(.*?)</h4>");
    self.regex_extractTopicSites = re.compile("<a href=\"(http://tvthek.orf.at/topic/.*?/\d+)\"\s*?title=\"(.*?)\"\s*?class=\"more");
    self.regex_extractVideoPages = re.compile("<a href=\"(http://tvthek.orf.at/.*?/\d+)\"");
    self.regex_extractJson = re.compile("data-jsb=\"({&quot;videoplayer_id&quot;.*})\">");

  @classmethod
  def name(self):
    return "ORF";

  def isSearchable(self):
    return True;

  def searchVideo(self, searchText):
    self.buildPageMenu(self.searchLink%urllib.quote(searchText.encode('UTF-8')),0);

  def extractVideoLinks(self,videoPageLinks,elementCount):
    for videoPageLink in videoPageLinks:

      videoPage = self.loadPage(videoPageLink.group(1));
      jsonContent = self.regex_extractJson.search(videoPage);
      if(jsonContent == None):
        return;
      jsonContent = jsonContent.group(1);
      jsonContent = BeautifulSoup(jsonContent,"html.parser");
      jsonContent = json.loads(jsonContent.prettify(formatter=None).encode('UTF-8'));
      jsonContent = jsonContent["selected_video"];
      title = jsonContent["title"];
      pictureLink = jsonContent["preview_image_url"];

      videoLinks={};

      for source in jsonContent["sources"]:
        if(source["protocol"] == "http"):
          quality = source["quality"];
          url = source["src"];
          if(quality == "Q1A"):
            videoLinks[0] = SimpleLink(url, -1);
          if(quality == "Q4A"):
            videoLinks[1] = SimpleLink(url, -1);
          if(quality == "Q6A"):
            videoLinks[2] = SimpleLink(url, -1);
          if(quality == "Q8C"):
            videoLinks[3] = SimpleLink(url, -1);
      if("title_separator" in jsonContent):
        titleSeperator = jsonContent["title_separator"];
        titleArray = title.split(titleSeperator);
        try:
          title = titleArray[0];
          subTitle = titleArray[1];
        except IndexError:
          subTitle = "";
        self.gui.buildVideoLink(DisplayObject(title,subTitle,pictureLink,"",videoLinks, True, None),self,elementCount);
      else:
        self.gui.buildVideoLink(DisplayObject(title,None,pictureLink,"",videoLinks, True, None),self,elementCount);

  def buildPageMenu(self, link, initCount):
    mainPage = self.loadPage(link);

    for topic in self.regex_extractTopicSites.finditer(mainPage):
      self.gui.buildVideoLink(DisplayObject(topic.group(2),None,None,"",topic.group(1), False, None),self,0);
      initCount=initCount+1;
    for profile in self.regex_extractProfileSites.finditer(mainPage):
      self.gui.buildVideoLink(DisplayObject(profile.group(4),None,profile.group(2),"",profile.group(1), False, None),self,0);
      initCount=initCount+1;
    videoPageLinks = list(self.regex_extractVideoPages.finditer(mainPage));

    self.extractVideoLinks(videoPageLinks,len(videoPageLinks)+initCount);

