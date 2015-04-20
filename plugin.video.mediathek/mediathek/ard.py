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
import re, time;
from mediathek import *

class ARDMediathek(Mediathek):
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    self.rootLink = "http://www.ardmediathek.de"
    self.menuTree = (
                      TreeNode("0","Neuste Videos",self.rootLink+"/tv/Neueste-Videos/mehr?documentId=21282466",True),
                      TreeNode("1","Sendungen von A-Z","",False,(
                        TreeNode("1.0","0-9",self.rootLink+"/tv/sendungen-a-z?buchstabe=0-9",True),
                        TreeNode("1.1","A",self.rootLink+"/tv/sendungen-a-z?buchstabe=A",True),
                        TreeNode("1.2","B",self.rootLink+"/tv/sendungen-a-z?buchstabe=B",True),
                        TreeNode("1.3","C",self.rootLink+"/tv/sendungen-a-z?buchstabe=C",True),
                        TreeNode("1.4","D",self.rootLink+"/tv/sendungen-a-z?buchstabe=D",True),
                        TreeNode("1.5","E",self.rootLink+"/tv/sendungen-a-z?buchstabe=E",True),
                        TreeNode("1.6","F",self.rootLink+"/tv/sendungen-a-z?buchstabe=F",True),
                        TreeNode("1.7","G",self.rootLink+"/tv/sendungen-a-z?buchstabe=G",True),
                        TreeNode("1.8","H",self.rootLink+"/tv/sendungen-a-z?buchstabe=H",True),
                        TreeNode("1.9","I",self.rootLink+"/tv/sendungen-a-z?buchstabe=I",True),
                        TreeNode("1.10","J",self.rootLink+"/tv/sendungen-a-z?buchstabe=J",True),
                        TreeNode("1.11","K",self.rootLink+"/tv/sendungen-a-z?buchstabe=K",True),
                        TreeNode("1.12","L",self.rootLink+"/tv/sendungen-a-z?buchstabe=L",True),
                        TreeNode("1.13","M",self.rootLink+"/tv/sendungen-a-z?buchstabe=M",True),
                        TreeNode("1.14","N",self.rootLink+"/tv/sendungen-a-z?buchstabe=N",True),
                        TreeNode("1.15","O",self.rootLink+"/tv/sendungen-a-z?buchstabe=O",True),
                        TreeNode("1.16","P",self.rootLink+"/tv/sendungen-a-z?buchstabe=P",True),
                        TreeNode("1.17","Q",self.rootLink+"/tv/sendungen-a-z?buchstabe=Q",True),
                        TreeNode("1.18","R",self.rootLink+"/tv/sendungen-a-z?buchstabe=R",True),
                        TreeNode("1.19","S",self.rootLink+"/tv/sendungen-a-z?buchstabe=S",True),
                        TreeNode("1.20","T",self.rootLink+"/tv/sendungen-a-z?buchstabe=T",True),
                        TreeNode("1.21","U",self.rootLink+"/tv/sendungen-a-z?buchstabe=U",True),
                        TreeNode("1.22","V",self.rootLink+"/tv/sendungen-a-z?buchstabe=V",True),
                        TreeNode("1.23","W",self.rootLink+"/tv/sendungen-a-z?buchstabe=W",True),
                        TreeNode("1.24","X",self.rootLink+"/tv/sendungen-a-z?buchstabe=X",True),
                        TreeNode("1.25","Y",self.rootLink+"/tv/sendungen-a-z?buchstabe=Y",True),
                        TreeNode("1.26","Z",self.rootLink+"/tv/sendungen-a-z?buchstabe=Z",True),
                        )),
		      TreeNode("2","Reportagen und Dokus",self.rootLink+"/tv/Reportage-Doku/mehr?documentId=21301806",True),
		      TreeNode("3","Film-Highlights",self.rootLink+"/tv/Film-Highlights/mehr?documentId=21301808",True),
		      TreeNode("4","Channels","",False,(
			  TreeNode("4.0","Kinder",self.rootLink+"/tv/Kinder-Familie/mehr?documentId=21282542",True),
			  TreeNode("4.1","Satire & Unterhaltung",self.rootLink+"/tv/Satire-Unterhaltung/mehr?documentId=21282544",True),
			  TreeNode("4.2","Kultur",self.rootLink+"/tv/Kultur/mehr?documentId=21282546",True),
			  TreeNode("4.3","Serien & Soaps",self.rootLink+"/tv/Serien-Soaps/mehr?documentId=21282548",True),
			  TreeNode("4.4","Wissen",self.rootLink+"/tv/Wissen/mehr?documentId=21282530",True),
			))
                      )
    self.configLink = self.rootLink+"/play/media/%s?devicetype=pc&feature=flash"
    
    self.regex_VideoPageLink = re.compile("<a href=\".*Video\?documentId=(\d+)&amp;bcastId=\d+\" class=\"textLink\">\s+?<p class=\"dachzeile\">(.*?)</p>\s+?<h4 class=\"headline\">(.*?)</h4>")
    self.regex_CategoryPageLink = re.compile("<a href=\"(.*Sendung\?documentId=\d+&amp;bcastId=\d+)\" class=\"textLink\">\s+?<p class=\"dachzeile\">.*?</p>\s+?<h4 class=\"headline\">(.*?)</h4>\s+?<p class=\"subtitle\">(.*?)</p>")
    self.pageSelectString = "&mcontent%s=page.%s"
    self.regex_DetermineSelectedPage = re.compile("&mcontents{0,1}=page.(\d+)");
    
    self.regex_videoLinks = re.compile("\"_quality\":(\d).*?\"_stream\":\"(.*?)\"");
    self.regex_pictureLink = re.compile("_previewImage\":\"(.*?)\"");
    
    
    self.regex_Date = re.compile("\\d{2}\\.\\d{2}\\.\\d{2}");
    
    
    self.replace_html = re.compile("<.*?>");
    
  @classmethod
  def name(self):
    return "ARD";
  def isSearchable(self):
    return False;
    
  def buildPageMenu(self, link, initCount, subLink = False):
    self.gui.log("Build Page Menu: %s SubLink: %d"%(link,subLink));    
    mainPage = self.loadPage(link);
    
    elementCount = 0;
    
    elementCount = self.extractElements(mainPage);
    
    
    self.generateNextPageElement(link, elementCount);
    return elementCount;
  def generateNextPageElement(self, link, elementCount):
    marker = "";
    if("Sendung?documentId" in link):
      marker = "s";
      
    numberElement = self.regex_DetermineSelectedPage.search(link);  
    if(numberElement is not None):
      oldNumber = int(numberElement.group(1));
      newNumber = oldNumber + 1;
      link = link.replace(self.pageSelectString%(marker,oldNumber),self.pageSelectString%(marker,newNumber));
      
      self.gui.buildVideoLink(DisplayObject("Weiter","","","",link,False),self,elementCount);
    else:
      link += self.pageSelectString%(marker,2)
      
      self.gui.buildVideoLink(DisplayObject("Weiter","","","",link,False),self,elementCount);
      
  def extractElements(self,mainPage):
    videoElements = list(self.regex_VideoPageLink.finditer(mainPage));
    linkElements = list(self.regex_CategoryPageLink.finditer(mainPage));
    
    counter = len(videoElements) + len(linkElements);
    for element in linkElements:
      link = self.rootLink+element.group(1);
      title = element.group(2).decode('utf-8');
      subTitle = element.group(3).decode('utf-8');
      self.gui.buildVideoLink(DisplayObject(title,subTitle,"","",link,False),self,counter);
    for element in videoElements:
      videoId = element.group(1);
      title = element.group(2).decode('utf-8');
      subTitle = element.group(3).decode('utf-8');
      self.decodeVideoInformation(videoId, title, subTitle, counter);
    
    
    
    return counter;
    
  def decodeVideoInformation(self, videoId, title, subTitle, nodeCount):
    link = self.configLink%videoId;
    self.gui.log("VideoLink: "+link);
    videoPage = self.loadPage(link);
    videoLinks = {}
    for match in self.regex_videoLinks.finditer(videoPage):
      quality = int(match.group(1));
      link = SimpleLink(match.group(2),0);
      
      if(quality > 0):
       quality -= 1
      videoLinks[quality] = link
    match = self.regex_pictureLink.search(videoPage)  
    picture = None
    if(match is not None):
      picture = self.rootLink+match.group(1);
    if(len(videoLinks)>0):
      self.gui.buildVideoLink(DisplayObject(title, subTitle,picture,"",videoLinks,True,None,0),self,nodeCount);
