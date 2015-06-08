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
      TreeNode("0","Neuste Videos",self.rootLink+"/guide/de",True),
      TreeNode("1","Arte+7","",False, (
        TreeNode("1.0",u"Alle Videos",self.rootLink+"/guide/de/plus7?regions=ALL%2Cdefault%2CDE_FR%2CSAT%2CEUR_DE_FR",True),
        TreeNode("1.1",u"Ausgewählte Videos",self.rootLink+"/guide/de/plus7/selection?regions=ALL%2Cdefault%2CDE_FR%2CSAT%2CEUR_DE_FR",True),
        TreeNode("1.2","Meistgesehen",self.rootLink+"/guide/de/plus7/plus_vues?regions=ALL%2Cdefault%2CDE_FR%2CSAT%2CEUR_DE_FR",True),
        TreeNode("1.3","Letzte Chance",self.rootLink+"/guide/de/plus7/derniere_chance?regions=ALL%2Cdefault%2CDE_FR%2CSAT%2CEUR_DE_FR",True),
      )),
      TreeNode("2","Programme","",False, (
	      TreeNode("2.0",u"28 Minuten",self.rootLink+"/guide/de/sendungen/VMI/28-minuten",True),
        TreeNode("2.1",u"360° - Geo",self.rootLink+"/guide/de/sendungen/TSG/360-geo-reportage",True),
        TreeNode("2.2",u"ARTE Journal",self.rootLink+"/guide/de/sendungen/AJT/arte-journal",True),
        TreeNode("2.3",u"ARTE Junior",self.rootLink+"/guide/de/sendungen/JUN/arte-junior",True),
        TreeNode("2.4",u"ARTE Reportage",self.rootLink+"/guide/de/sendungen/JTE/arte-reportage",True),
        TreeNode("2.5",u"Abgedreht",self.rootLink+"/guide/de/sendungen/PNB/abgedreht",True),
        TreeNode("2.6",u"Durch die Nacht mit …",self.rootLink+"/guide/de/sendungen/ACN/durch-die-nacht-mit",True),
        TreeNode("2.7",u"Futuremag",self.rootLink+"/guide/de/sendungen/FUM/futuremag",True),
        TreeNode("2.8",u"Karambolage",self.rootLink+"/guide/de/sendungen/KAR/karambolage",True),
        TreeNode("2.9",u"Kino auf ARTE",self.rootLink+"/guide/de/sendungen/FIL/kino-auf-arte",True),
        TreeNode("2.10",u"Kurzschluss",self.rootLink+"/guide/de/sendungen/COU/kurzschluss",True),
        TreeNode("2.11",u"Maestro",self.rootLink+"/guide/de/sendungen/MAE/maestro",True),
        TreeNode("2.12",u"Metropolis",self.rootLink+"/guide/de/sendungen/MTR/metropolis",True),
        TreeNode("2.13",u"Mit offenen Karten",self.rootLink+"/guide/de/sendungen/DCA/mit-offenen-karten",True),
        TreeNode("2.14",u"Philosophie",self.rootLink+"/guide/de/sendungen/PHI/philosophie",True),
        TreeNode("2.15",u"Square",self.rootLink+"/guide/de/sendungen/SUA/square",True),
        TreeNode("2.16",u"Tracks",self.rootLink+"/guide/de/sendungen/TRA/tracks",True),
        TreeNode("2.17",u"Vox Pop",self.rootLink+"/guide/de/sendungen/VOX/vox-pop",True),
        TreeNode("2.18",u"X:enius",self.rootLink+"/guide/de/sendungen/XEN/x-enius",True),
        TreeNode("2.19",u"Yourope",self.rootLink+"/guide/de/sendungen/YOU/yourope",True),
        TreeNode("2.20",u"Zu Tisch In ...",self.rootLink+"/guide/de/sendungen/CUI/zu-tisch-in",True),
      )),
      TreeNode("3","Themen","",False,(
        TreeNode("3.0",u"Aktuelles"               ,self.rootLink+"/guide/de/plus7/par_themes?name=Aktuelles&value=ACT&regions=EUR_DE_FR%2CDE_FR%2CSAT%2CALL",True),
        TreeNode("3.1",u"Dokumentationen"         ,self.rootLink+"/guide/de/plus7/par_themes?name=Dokumentationen&value=DOC&regions=EUR_DE_FR%2CDE_FR%2CSAT%2CALL",True),
        TreeNode("3.2",u"Entdeckung"              ,self.rootLink+"/guide/de/plus7/par_themes?name=Entdeckung&value=DEC&regions=EUR_DE_FR%2CDE_FR%2CSAT%2CALL",True),
        TreeNode("3.3",u"Europa"                  ,self.rootLink+"/guide/de/plus7/par_themes?name=Europa&value=EUR&regions=EUR_DE_FR%2CDE_FR%2CSAT%2CALL",True),
        TreeNode("3.4",u"Geopolitik & Geschichte" ,self.rootLink+"/guide/de/plus7/par_themes?name=Geopolitik+%26+Geschichte&value=GEO&regions=EUR_DE_FR%2CDE_FR%2CSAT%2CALL",True),
        TreeNode("3.5",u"Gesellschaft"            ,self.rootLink+"/guide/de/plus7/par_themes?name=Gesellschaft&value=SOC&regions=EUR_DE_FR%2CDE_FR%2CSAT%2CALL",True),
        TreeNode("3.6",u"Junior"                  ,self.rootLink+"/guide/de/plus7/par_themes?name=Junior&value=JUN&regions=EUR_DE_FR%2CDE_FR%2CSAT%2CALL",True),
        TreeNode("3.7",u"Kino & Serien"           ,self.rootLink+"/guide/de/plus7/par_themes?name=Kino+%26+Serien&value=CIN&regions=EUR_DE_FR%2CDE_FR%2CSAT%2CALL",True),
        TreeNode("3.8",u"Kunst & Kultur"          ,self.rootLink+"/guide/de/plus7/par_themes?name=Kunst+%26+Kultur&value=ART&regions=EUR_DE_FR%2CDE_FR%2CSAT%2CALL",True),
        TreeNode("3.9",u"Popkultur & Musik"       ,self.rootLink+"/guide/de/plus7/par_themes?name=Popkultur+%26+Musik&value=CUL&regions=EUR_DE_FR%2CDE_FR%2CSAT%2CALL",True),
        TreeNode("3.10",u"Umwelt & Wissenschaft"  ,self.rootLink+"/guide/de/plus7/par_themes?name=Umwelt+%26+Wissenschaft&value=ENV&regions=EUR_DE_FR%2CDE_FR%2CSAT%2CALL",True),
        TreeNode("3.11",u"Andere"                 ,self.rootLink+"/guide/de/plus7/par_themes?name=Junior&value=JUN&regions=EUR_DE_FR%2CDE_FR%2CSAT%2CALL",True),
      )),
    );
    
    self.regex_VideoPageLinksHTML = re.compile("href=[\"'](/guide/de/\d{6}-\d{3}/.+?)[\"']");
    self.regex_VideoPageLinksJSON = re.compile("\"url\":\"((http:\\\\/\\\\/www\\.arte\\.tv){0,1}\\\\/guide\\\\/de\\\\/\d{6}-\d{3}\\\\/.+?)\"");
    
    
    
    self.regex_JSONPageLink = re.compile("http://arte.tv/papi/tvguide/videos/stream/player/D/\d{6}-\d{3}.+?/ALL/ALL.json");
    self.regex_JSON_VideoLink = re.compile("\"HTTP_MP4_.+?\":{.*?\"bitrate\":(\d+),.*?\"url\":\"(http://.*?.mp4)\".*?\"versionShortLibelle\":\"([a-zA-Z]{2})\".*?}");
    self.regex_JSON_ImageLink = re.compile("\"original\":\"(http://www.arte.tv/papi/tvguide/images/.*?.jpg)\"");
    self.regex_JSON_Detail = re.compile("\"VDE\":\"(.*?)\"");
    self.regex_JSON_Titel = re.compile("\"VTI\":\"(.*?)\"");
    
    
    
    
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
    for videoPageLink in self.regex_VideoPageLinksHTML.finditer(htmlPage):
      link = videoPageLink.group(1);
      
      if(link not in links):
        links.add(link);

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
    picture = self.regex_JSON_ImageLink.search(jsonPage).group(1);
    title = self.regex_JSON_Titel.search(jsonPage).group(1);
    detail =  self.regex_JSON_Detail.search(jsonPage).group(1);
    
    self.gui.buildVideoLink(DisplayObject(title,"",picture,detail,videoLinks,True, None),self,linkCount);
	
   
    
    
      