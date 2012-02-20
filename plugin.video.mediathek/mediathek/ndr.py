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
import re,time
from mediathek import *
from xml.dom import minidom;

regex_dateString = re.compile("\\d{4}-\\d{2}-\\d{2}");

class NDRMediathek(Mediathek):
  @classmethod
  def name(self):
    return "NDR";
  def isSearchable(self):
    return False;
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    
    if(self.gui.preferedStreamTyp == 0):
      self.baseType = "video/x-ms-asf";
    elif (self.gui.preferedStreamTyp == 1):  
      self.baseType = "video/x-ms-asf"
    elif (self.gui.preferedStreamTyp == 2):
      self.baseType ="video/x-ms-asf";
    else:
      self.baseType ="video/quicktime";
    
    self.menuTree = (
      TreeNode("0","Die neuesten Videos","http://www.ndr.de/mediathek/videoliste100-rss.xml",True),
      );

    self.regex_extractVideoLink = re.compile("mms://ndr\.wmod\.llnwd\.net/.*?\.wmv");
      
    self.rootLink = "http://www.ndr.de"
    self.searchLink = 'http://www.3sat.de/mediathek/mediathek';
    link = "/mediathek/mediathek.php\\?obj=\\d+";
    self.regex_searchResult = re.compile("href=\""+link+"\" class=\"media_result_thumb\"");
    self.regex_searchResultLink = re.compile(link)
    self.regex_searchLink = re.compile("http://wstreaming.zdf.de/.*?\\.asx")
    self.regex_searchTitle = re.compile("<h2>.*</h2>");
    self.regex_searchDetail = re.compile("<span class=\"text\">.*");
    self.regex_searchDate = re.compile("\\d{2}.\\d{2}.\\d{4}");
    self.regex_searchImage = re.compile("/dynamic/mediathek/stills/\\d*_big\\.jpg");
    self.replace_html = re.compile("<.*?>");
    
  def buildPageMenu(self, link, initCount):
    self.gui.log("buildPageMenu: "+link);
    rssFeed = self.loadConfigXml(link);
    self.extractVideoObjects(rssFeed, initCount);
    
  def searchVideo(self, searchText):
    values ={'mode':'search',
             'query':searchText,
             'red': '',
             'query_time': '',
             'query_sort': '',
             'query_order':''
             }
    mainPage = self.loadPage(self.searchLink,values);
    results = self.regex_searchResult.findall(mainPage);
    for result in results:
      objectLink = self.regex_searchResultLink.search(result).group();
      infoLink = self.rootLink+objectLink
      infoPage = self.loadPage(infoLink);
      title = self.regex_searchTitle.search(infoPage).group();
      detail = self.regex_searchDetail.search(infoPage).group();
      
      image = self.regex_searchImage.search(infoPage).group();
      title = self.replace_html.sub("", title);
      detail = self.replace_html.sub("", detail);
      try:
        dateString = self.regex_searchDate.search(infoPage).group();
        pubDate = time.strptime(dateString,"%d.%m.%Y");
      except:
        pubDate = time.gmtime();
      
      videoLink = self.rootLink+objectLink+"&mode=play";
      videoPage = self.loadPage(videoLink);
      video = self.regex_searchLink.search(videoPage).group();
      links = {}
      links[2] = SimpleLink(video,0)
      self.gui.buildVideoLink(DisplayObject(title,"",self.rootLink + image,detail,links,True, pubDate),self,len(results));
      
  def readText(self,node,textNode):
    try:
      node = node.getElementsByTagName(textNode)[0].firstChild;
      return unicode(node.data);
    except:
      return "";
  
  def loadConfigXml(self, link):
    self.gui.log("load:"+link)
    xmlPage = self.loadPage(link);
    return minidom.parseString(xmlPage);  
    
  def extractVideoObjects(self, rssFeed, initCount):
    nodes = rssFeed.getElementsByTagName("item");
    nodeCount = initCount + len(nodes)
    displayObjects = [];
    for itemNode in nodes:
      displayObjects.append(self.extractVideoInformation(itemNode,nodeCount));
    sorted(displayObjects, key = lambda item:item.date, reverse=True);
    for displayObject in displayObjects:  
      self.gui.buildVideoLink(displayObject,self,nodeCount);
  def parseDate(self,dateString):
    dateString = regex_dateString.search(dateString).group();
    
    return time.strptime(dateString,"%Y-%m-%d");
  
  def loadVideoLinks(self, link):
    videoPage = self.loadPage(link);
    links = {};
    for link in self.regex_extractVideoLink.finditer(videoPage):
      link = link.group();
      if link.find("wm.lo"):
        links[0] = SimpleLink(link, 0);
      if link.find("wm.hi"):
        links[1] = SimpleLink(link, 0);      
      if link.find("wm.hq"):
        links[2] = SimpleLink(link, 0);
    return links;
    
  def extractVideoInformation(self, itemNode, nodeCount):
    title = self.readText(itemNode,"title");
    dateString = self.readText(itemNode,"dc:date");
    pubDate = self.parseDate(dateString);
    
    descriptionNode = self.readText(itemNode,"description");
    description = unicode(descriptionNode);
    
    picture = self.readText(itemNode,"mp:data");
    videoPageLink = self.readText(itemNode,"link");
    
    links = self.loadVideoLinks(videoPageLink);
    return DisplayObject(title,"",picture,description,links,True, None);
    
    
