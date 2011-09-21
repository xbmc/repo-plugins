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
import re, traceback
from mediathek import *
from xml.dom import minidom
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
  def isSearchable(self):
    return True;
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    self.rootLink = "http://videos.arte.tv";
    self.menuTree = (
      TreeNode("0","ARTE+7",self.rootLink+"/de/videos",True),
      TreeNode("1","Alle Videos",self.rootLink+"/de/videos/alleVideos",True),
      TreeNode("2","Alle Sendungen",self.rootLink+"/de/videos/sendungen",True),
      TreeNode("3","Events",self.rootLink+"/de/videos/events/index-3188672.html",True),
    );
    
    self.regex_Clips = re.compile("/de/videos/[^/]*-(\\d*).html")
    self.regex_ExtractVideoConfig = re.compile("http://videos\\.arte\\.tv/de/do_delegate/videos/.*-\\d*,view,asPlayerXml\\.xml");
    self.regex_ExtractRtmpLink = re.compile("<url quality=\"(sd|hd)\">(rtmp://.*mp4:.*)</url>")
    self.regex_ExtractTopicPages = re.compile("<a href=\"([^\"]*)\"[^<]*>([^<]*)</a> \((\\d+)\)");
    self.regex_DescriptionLink = re.compile("http://videos\\.arte\\.tv/de/videos/.*?\\.html");
    self.regex_Description = re.compile("<div class=\"recentTracksCont\">\\s*<div>\\s*<p>.*?</p>");
    self.replace_html = re.compile("<.*?>");
    
    self.baseXmlLink = self.rootLink+"/de/do_delegate/videos/global-%s,view,asPlayerXml.xml"
    self.searchLink = self.rootLink+"/de/do_search/videos/suche?q=";
    
  def buildPageMenu(self, link, initCount):
    self.gui.log("buildPageMenu: "+link);
    mainPage = self.loadPage(link);
    elementCount = self.extractTopicObjects(mainPage, initCount);
    self.extractVideoObjects(mainPage, elementCount);
    
  def searchVideo(self, searchText):
    link = self.searchLink + searchText
    self.buildPageMenu(link,0);
    
  def extractVideoObjects(self,mainPage, initCount):
    videoIDs = [];
    for videoID in self.regex_Clips.findall(mainPage):
      if videoID not in videoIDs:
        videoIDs.append(videoID);
    elementCount = initCount+len(videoIDs);    
    for videoID in videoIDs:
      self.extractVideoInformation(videoID,elementCount);
  
  def parseDate(self,dateString):
    self.gui.log(dateString);
    dateString = regex_dateString.search(dateString).group();
    for month in month_replacements.keys():
      dateString = dateString.replace(month,month_replacements[month]);
    return time.strptime(dateString,"%d %m %Y");
    
  def extractVideoInformation(self, videoID, elementCount):
    link = self.baseXmlLink%(videoID);
    xmlPage = self.loadPage(link);
    try:
      link = self.regex_DescriptionLink.search(xmlPage).group();
      self.gui.log("load descriptionHtml: "+link);
      descPage = self.loadPage(link);
      
      try:
        desc = self.regex_Description.search(descPage).group()
        
        desc = unicode(desc.decode('UTF-8'));
        desc = self.replace_html.sub("", desc);
      except:
        self.gui.log("something goes wrong while processing "+link);
        desc="";
        
      
      link = self.regex_ExtractVideoConfig.search(xmlPage).group();
      self.gui.log("load configXml: "+link);
      xmlPage = self.loadPage(link);
    
      configXml = minidom.parseString(xmlPage);
      for titleNode in configXml.getElementsByTagName("name"):
        if(titleNode.hasChildNodes()):
          title = titleNode.firstChild.data;
          break;
      picture = configXml.getElementsByTagName("firstThumbnailUrl")[0].firstChild.data;
      dateString = configXml.getElementsByTagName("dateVideo")[0].firstChild.data;
      date = self.parseDate(dateString);
      
      links = {}
      
      urlNodes = configXml.getElementsByTagName("urls")[0].toxml();
      for touple in self.regex_ExtractRtmpLink.findall(urlNodes):
        quality = touple[0];
        if(quality == "sd"):
          quality = 0;
        else:
          quality = 2;
        
        urlString = touple[1];
        self.gui.log(urlString);
        stringArray = urlString.split("mp4:");
        
        links[quality] = SimpleLink("%s playpath=MP4:%s swfUrl=http://videos.arte.tv/blob/web/i18n/view/player_11-3188338-data-4836231.swf swfVfy=1"%(stringArray[0],stringArray[1]),0);
      if(len(links) > 0):
        self.gui.log("Picture: "+picture);
        self.gui.buildVideoLink(DisplayObject(title,"",picture,desc,links,True,date),self,elementCount);
      configXml.unlink();
    except:
      self.gui.log("something goes wrong while processing "+link);
      print xmlPage;
      self.gui.log("Exception: ");
      traceback.print_exc();
      self.gui.log("Stacktrace: ");
      traceback.print_stack();
  
  def extractTopicObjects(self,mainPage,initCount):
    touples = self.regex_ExtractTopicPages.findall(mainPage)
    elementCount = len(touples) + initCount
    for touple in touples:      
      try:
        title = touple[1].encode('UTF-8');
      except:
        title = touple[1].decode('UTF-8');
      numbers = touple[2];
      link = touple[0];
      self.gui.buildVideoLink(DisplayObject(title,"","","",self.rootLink+link,False),self,elementCount);
    return elementCount;
      