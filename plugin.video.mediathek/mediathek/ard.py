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
import re, time, datetime;
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
                      TreeNode("2","Ausgewählte Dokus".decode("utf-8"),self.rootLink+"/tv/Ausgew%C3%A4hlte-Dokus/mehr?documentId=33649086",True),
                      TreeNode("3","Ausgewählte Filme".decode("utf-8"),self.rootLink+"/tv/Ausgew%C3%A4hlte-Filme/mehr?documentId=33649088",True),
                      TreeNode("4","Alle Reportagen und Dokus",self.rootLink+"/tv/Alle-Dokus-Reportagen/mehr?documentId=29897596",True),
                      TreeNode("5","Alle Filme",self.rootLink+"/tv/Alle-Filme/mehr?documentId=33594630",True),
                      TreeNode("6","Alle Serien",self.rootLink+"/tv/Serien/mehr?documentId=26402940",True),
                      TreeNode("7","Themen",self.rootLink+"/tv/Themen/mehr?documentId=21301810",True),
                      TreeNode("8","Rubriken","",False,(
                        TreeNode("8.0","Kinder",self.rootLink+"/tv/Kinder/Tipps?documentId=21282542",True),
                        TreeNode("8.1","Unterhaltung & Comedy",self.rootLink+"/tv/Unterhaltung-Comedy/mehr?documentId=21282544",True),
                        TreeNode("8.2","Kultur",self.rootLink+"/tv/Kultur/mehr?documentId=21282546",True),
                        TreeNode("8.3","Wissen",self.rootLink+"/tv/Wissen/mehr?documentId=21282530",True),
                        TreeNode("8.4","Politik",self.rootLink+"/tv/Politik/mehr?documentId=29684598",True),
                        TreeNode("8.5","Ratgeber",self.rootLink+"/tv/Ratgeber/mehr?documentId=27112994",True),
                        TreeNode("8.6","Krimi",self.rootLink+"/tv/Krimi/mehr?documentId=27258656",True),
                        TreeNode("8.7","Reise",self.rootLink+"/tv/Reise/mehr?documentId=29769608",True),
                        )),
                      )
    self.configLink = self.rootLink+"/play/media/%s?devicetype=pc&feature=flash"
                                                     #.*Video\?bcastId=\d+&amp;documentId=(\d+)\" class=\"textLink\">\s+?<p class=\"dachzeile\">(.*?)</p>\s+?<h4 class=\"headline\">(.*?)</h4>
    self.regex_VideoPageLink = re.compile("<a href=\".*Video\?.*?documentId=(\d+).*?\" class=\"textLink\">\s+?<p class=\"dachzeile\">(.*?)<\/p>\s+?<h4 class=\"headline\">(.*?)<\/h4>\s+?<p class=\"subtitle\">(?:(\d+.\d+.\d+) \| )?(\d*) Min.")
    self.regex_CategoryPageLink = re.compile("<a href=\"(.*(?:Sendung|Thema)\?.*?documentId=\d+.*?)\" class=\"textLink\">(?:.|\n)+?<h4 class=\"headline\">(.*?)<\/h4>")
    self.pageSelectString = "&mcontent%s=page.%s"
    self.regex_DetermineSelectedPage = re.compile("&mcontents{0,1}=page.(\d+)");
    
    self.regex_videoLinks = re.compile("\"_quality\":(\d).*?\"_stream\":\[?\"(.*?)\"");
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
    if len(videoElements) == 0:
      linkElements = list(self.regex_CategoryPageLink.finditer(mainPage));
    else:
      linkElements = []
    
    counter = len(videoElements) + len(linkElements);
    for element in linkElements:
      link = self.rootLink+element.group(1);
      title = element.group(2).decode('utf-8');
      # subTitle = element.group(3).decode('utf-8');
      subTitle = ""
      self.gui.buildVideoLink(DisplayObject(title,subTitle,"","",link,False),self,counter);
    for element in videoElements:
      videoId = element.group(1);
      title = element.group(2).decode('utf-8');
      subTitle = element.group(3).decode('utf-8');
      if element.group(4):
        datestring = element.group(4).decode('utf-8');
        date = datetime.date(*[int(x) for x in datestring.split('.')[::-1]]).timetuple()
      else:
        date = None
      durationstring = element.group(5).decode('utf-8');
      duration = int(durationstring) * 60;
      self.decodeVideoInformation(videoId, title, subTitle, counter, date, duration);
    
    
    
    return counter;
    
  def decodeVideoInformation(self, videoId, title, subTitle, nodeCount, date, duration):
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
      picture = match.group(1);
    if(len(videoLinks)>0):
      self.gui.buildVideoLink(DisplayObject(title, subTitle,picture,"",videoLinks,True,date,duration),self,nodeCount);
