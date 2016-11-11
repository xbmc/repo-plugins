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
import re, traceback
from mediathek import *
from xml.dom import minidom
from xml.dom import Node;

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
    return False;
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    self.rootLink = "http://www.arte.tv";
    self.menuTree = (
      
      TreeNode("0","Arte+7","",False, (
        TreeNode("0.0",u"Alle Videos",self.rootLink+"/guide/de/plus7",True),
        TreeNode("0.1","Neuste Videos",self.rootLink+"/guide/de/plus7/alle-videos?sort=recent",True),
        TreeNode("0.2",u"Meistgesehen",self.rootLink+"/guide/de/plus7/alle-videos?sort=most",True),
        TreeNode("0.3",u"Letzte Chance",self.rootLink+"/guide/de/plus7/alle-videos?sort=last",True),
      )),
      TreeNode("1","Themen","",False,(
        TreeNode("1.0",u"Aktuelles & Gesellschaft"  ,self.rootLink+"/guide/de/plus7/aktuelles-gesellschaft",True),
        TreeNode("1.1",u"Fernsehfilm & Serien"      ,self.rootLink+"/guide/de/plus7/fernsehfilme-serien",True),
        TreeNode("1.2",u"Kino"                      ,self.rootLink+"/guide/de/plus7/kino",True),
        TreeNode("1.3",u"Kunst & Kultur"            ,self.rootLink+"/guide/de/plus7/kunst-kultur",True),
        TreeNode("1.4",u"Popkultur & Alternativ"    ,self.rootLink+"/guide/de/plus7/popkultur-alternativ",True),
        TreeNode("1.5",u"Entdeckung"                ,self.rootLink+"/guide/de/plus7/entdeckung",True),
        TreeNode("1.6",u"Geschichte"                ,self.rootLink+"/guide/de/plus7/geschichte",True),
        TreeNode("1.7",u"Junior"                    ,self.rootLink+"/guide/de/plus7/junior",True),
      )),
    );
    
    self.regex_VideoPageLinksHTML = re.compile("href=[\"'](http:\\\\/\\\\/www\\.arte\\.tv\\\\/guide\\\\/de\\\\/\d{6}-\d{3}/.+?)[\"']");
    self.regex_VideoPageLinksJSON = re.compile("\"url\":\"((http:\\\\/\\\\/www\\.arte\\.tv){0,1}\\\\/guide\\\\/de\\\\/\d{6}-\d{3}\\\\/.+?)\"");
    
    self.regex_findVideoIds = re.compile("(\d{6}-\d{3})(-A)");
    
    self.regex_JSONPageLink = re.compile("http://arte.tv/papi/tvguide/videos/stream/player/D/\d{6}-\d{3}.+?/ALL/ALL.json");
    self.regex_JSON_VideoLink = re.compile("\"HTTP_MP4_.+?\":{.*?\"bitrate\":(\d+),.*?\"url\":\"(http://.*?.mp4)\".*?\"versionShortLibelle\":\"([a-zA-Z]{2})\".*?}");
    self.regex_JSON_ImageLink = re.compile("\"IUR\":\"(http://.*?\\.arte\\.tv/papi/tvguide/images/.*?\\..{3})\"");
    self.regex_JSON_Detail = re.compile("\"VDE\":\"(.*?)\"");
    self.regex_JSON_Titel = re.compile("\"VTI\":\"(.*?)\"");
    
    self.jsonLink = "http://arte.tv/papi/tvguide/videos/stream/player/D/%s_PLUS7-D/ALL/ALL.json"
    
    
    
    
  def buildPageMenu(self, link, initCount):
    self.gui.log("buildPageMenu: "+link);
    htmlPage = self.loadPage(link).decode('UTF-8');
    self.extractVideoLinks(htmlPage, initCount);
  
  
  #def searchVideo(self, searchText):
  #  link = self.searchLink + searchText
  #  self.buildPageMenu(link,0);
    
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
    
    
    self.gui.log("Found %s unique links"%len(jsonLinks));
    
    for link in jsonLinks:
      jsonPage = self.loadPage(link).decode('UTF-8');
      self.extractVideoLinksFromJSONPage(jsonPage,linkCount)
        
  def extractVideoLinksFromJSONPage(self, jsonPage, linkCount):  
    videoLinks = {}
    for match in self.regex_JSON_VideoLink.finditer(jsonPage):
      bitrate = match.group(1);
      url = match.group(2);
      lang = match.group(3);
      if lang.lower() != 'de':
        continue;

      if(bitrate < 800):
        videoLinks[0] = SimpleLink(url,0);
      if(bitrate >= 800 and bitrate < 1500):
        videoLinks[1] = SimpleLink(url,0);
      if(bitrate >= 1500 and bitrate < 2200):
        videoLinks[2] = SimpleLink(url,0);
      if(bitrate >= 2200):
        videoLinks[3] = SimpleLink(url,0);
    if(len(videoLinks) == 0):
      return;
    
    picture = None
    title = None
    detail = None
    
    result = self.regex_JSON_ImageLink.search(jsonPage);
    if(result is not None):
      picture = result.group(1);
      self.gui.log(picture)
    
    result = self.regex_JSON_Titel.search(jsonPage);
    if(result is not None):
      title = result.group(1);
      self.gui.log(title)
    result = self.regex_JSON_Detail.search(jsonPage);
    if(result is not None):
      detail =  result.group(1);
    
    self.gui.buildVideoLink(DisplayObject(title,"",picture,detail,videoLinks,True, None),self,linkCount);
	
   
    
    
      
