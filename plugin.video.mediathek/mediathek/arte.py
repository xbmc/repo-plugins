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
    return True;
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    self.rootLink = "http://videos.arte.tv";
    self.menuTree = (
      TreeNode("0","Neuste Videos",self.rootLink+"/de/do_delegate/videos/index-3188626,view,rss.xml",True),
      
      TreeNode("1","Programme","",False, (
        TreeNode("1.0",u"360° - Geo",self.rootLink+"/de/do_delegate/videos/sendungen/360_geo/index-3188704,view,rss.xml",True),
        TreeNode("1.1",u"ARTE Journal",self.rootLink+"/de/do_delegate/videos/artejournal/index-3188708,view,rss.xml",True),
        TreeNode("1.2",u"ARTE Lounge",self.rootLink+"/de/do_delegate/arte_lounge/index-3219086,view,rss.xml",True),
        TreeNode("1.3",u"ARTE Reportage",self.rootLink+"/de/do_delegate/videos/sendungen/arte_reportage/index-3188710,view,rss.xml",True),
        TreeNode("1.4",u"Cut up",self.rootLink+"/de/do_delegate/cut_up/index-3199714,view,rss.xml",True),
        TreeNode("1.5",u"Der Blogger",self.rootLink+"/de/do_delegate/videos/sendungen/blogger/index-3193602,view,rss.xml",True),
        TreeNode("1.6",u"Die Nacht / La nuit",self.rootLink+"/de/do_delegate/die_nacht_la_nuit/index-3188716,view,rss.xml",True),
        TreeNode("1.7",u"Geschichte am Mittwoch",self.rootLink+"/de/do_delegate/geschichte_mittwoch/index-3188722,view,rss.xml",True),
        TreeNode("1.8",u"Giordano trifft",self.rootLink+"/de/do_delegate/giordano_hebdo/index-3199710,view,rss.xml",True),
        TreeNode("1.9",u"Global",self.rootLink+"/de/do_delegate/global_mag/index-3188718,view,rss.xml",True),
        TreeNode("1.10",u"Karambolage",self.rootLink+"/de/do_delegate/videos/sendungen/karambolage/index-3224652,view,rss.xml",True),
        TreeNode("1.11",u"Künstler hautnah",self.rootLink+"/de/do_delegate/l_art_et_la_maniere/index-3188720,view,rss.xml",True),
        TreeNode("1.12",u"Kurzschluss",self.rootLink+"/de/do_delegate/videos/sendungen/kurzschluss/index-3188712,view,rss.xml",True),
        TreeNode("1.13",u"Metropolis",self.rootLink+"/de/do_delegate/videos/sendungen/metropolis/index-3188724,view,rss.xml",True),
        TreeNode("1.14",u"Philosophie",self.rootLink+"/de/do_delegate/videos/sendungen/philosophie/index-3188728,view,rss.xml",True),
        TreeNode("1.15",u"Tracks",self.rootLink+"/de/do_delegate/videos/tracks/index-3188628,view,rss.xml",True),
        TreeNode("1.16",u"X:enius",self.rootLink+"/de/do_delegate/videos/sendungen/xenius/index-3188730,view,rss.xml",True),
        TreeNode("1.17",u"Yourope",self.rootLink+"/de/do_delegate/videos/sendungen/yourope/index-3188732,view,rss.xml",True),
      )),
      TreeNode("2","Themen","",False,(
        TreeNode("2.0",u"Aktuelles",self.rootLink+"/de/do_delegate/videos/alle_videos/aktuelles/index-3188636,view,rss.xml",True),
        TreeNode("2.1",u"Dokumentationen",self.rootLink+"/de/do_delegate/videos/alle_videos/dokus/index-3188646,view,rss.xml",True),
        TreeNode("2.2",u"Entdeckung",self.rootLink+"/de/do_delegate/videos/entdeckung/index-3188644,view,rss.xml",True),
        TreeNode("2.3",u"Europa",self.rootLink+"/de/do_delegate/videos/alle_videos/europa/index-3188648,view,rss.xml",True),
        TreeNode("2.4",u"Geopolitik & Geschichte",self.rootLink+"/de/do_delegate/videos/alle_videos/geopolitik_geschichte/index-3188654,view,rss.xml",True),
        TreeNode("2.5",u"Gesellschaft",self.rootLink+"/de/do_delegate/videos/alle_videos/gesellschaft/index-3188652,view,rss.xml",True),
        TreeNode("2.6",u"Junior",self.rootLink+"/de/do_delegate/videos/alle_videos/junior/index-3188656,view,rss.xml",True),
        TreeNode("2.7",u"Kino & Serien",self.rootLink+"/de/do_delegate/videos/alle_videos/kino_serien/index-3188642,view,rss.xml",True),
        TreeNode("2.8",u"Kunst & Kultur",self.rootLink+"/de/do_delegate/videos/alle_videos/kunst_kultur/index-3188640,view,rss.xml",True),
        TreeNode("2.9",u"Popkultur & Musik",self.rootLink+"/de/do_delegate/videos/alle_videos/popkultur_musik/index-3188638,view,rss.xml",True),
        TreeNode("2.10",u"Umwelt & Wissenschaft",self.rootLink+"/de/do_delegate/videos/alle_videos/umwelt_wissenschaft/index-3188650,view,rss.xml",True),
      )),
    );
    
    self.regex_ExtractVideoIdent = re.compile(".*/(.*\\d+)\.html");
    
    
    self.regex_Clips = re.compile("/de/videos/[^/]*-(\\d*).html")
    self.regex_ExtractVideoConfig = re.compile("http://videos\\.arte\\.tv/de/do_delegate/videos/.*-\\d*,view,asPlayerXml\\.xml");
    self.regex_ExtractRtmpLink = re.compile("<url quality=\"(sd|hd)\">(rtmp://.*mp4:.*)</url>")
    self.regex_ExtractTopicPages = re.compile("<a href=\"([^\"]*)\"[^<]*>([^<]*)</a> \((\\d+)\)");
    self.regex_DescriptionLink = re.compile("http://videos\\.arte\\.tv/de/videos/.*?\\.html");
    self.regex_Description = re.compile("<div class=\"recentTracksCont\">\\s*<div>\\s*<p>.*?</p>");
    self.replace_html = re.compile("<.*?>");
    
    self.baseXmlLink = self.rootLink+"/de/do_delegate/videos/%s,view,asPlayerXml.xml"
    self.searchLink = self.rootLink+"/de/do_search/videos/suche?q=";
    
  def buildPageMenu(self, link, initCount):
    self.gui.log("buildPageMenu: "+link);
    rssFeed = self.loadXml(link);
    self.extractVideoObjects(rssFeed, initCount);
  
  
  def loadXml(self, link):
    self.gui.log("load:"+link)
    xmlPage = self.loadPage(link);
    return minidom.parseString(xmlPage);  
    
  def searchVideo(self, searchText):
    link = self.searchLink + searchText
    self.buildPageMenu(link,0);
    
  def extractVideoObjects(self, rssFeed, initCount):
    nodes = rssFeed.getElementsByTagName("item");
    nodeCount = initCount + len(nodes)
    for itemNode in nodes:
      link = title = self.readText(itemNode,"link");
      ident = self.regex_ExtractVideoIdent.match(link).group(1);
      link = self.baseXmlLink%ident;
      xmlPage = self.loadXml(link); 
      for videosNode in xmlPage.getElementsByTagName("videos"):
        print videosNode.toxml();
        print len(videosNode.childNodes);
        for videoNode in videosNode.childNodes:
          if(videoNode.nodeType == Node.ELEMENT_NODE):
            langAttr = videoNode.getAttribute("lang");
            if(langAttr == "de"):
              link = videoNode.getAttribute("ref");
              self.extractVideoInformation(link,nodeCount);
  
  def parseDate(self,dateString):
    self.gui.log(dateString);
    dateString = regex_dateString.search(dateString).group();
    for month in month_replacements.keys():
      dateString = dateString.replace(month,month_replacements[month]);
    return time.strptime(dateString,"%d %m %Y");
    
  def extractVideoInformation(self, link, elementCount):
    try:
      xmlPage = self.loadXml(link);
      try:
        
        for titleNode in xmlPage.getElementsByTagName("name"):
          if(titleNode.hasChildNodes()):
            title = titleNode.firstChild.data;
            break;
        picture = xmlPage.getElementsByTagName("firstThumbnailUrl")[0].firstChild.data;
        dateString = xmlPage.getElementsByTagName("dateVideo")[0].firstChild.data;
        date = self.parseDate(dateString);
        
        links = {}
        
        for urlNode in xmlPage.getElementsByTagName("urls")[0].childNodes:
          if(urlNode.nodeType == Node.ELEMENT_NODE):
            quality = urlNode.getAttribute("quality");
            if(quality == "sd"):
              quality = 0;
            else:
              quality = 2;
            
            urlString = urlNode.firstChild.data;
            self.gui.log(urlString);
            stringArray = urlString.split("mp4:");
            
            links[quality] = SimpleLink("%s playpath=MP4:%s swfUrl=http://videos.arte.tv/blob/web/i18n/view/player_11-3188338-data-4836231.swf swfVfy=1"%(stringArray[0],stringArray[1]),0);
        if(len(links) > 0):
          self.gui.log("Picture: "+picture);
          self.gui.buildVideoLink(DisplayObject(title,"",picture,"",links,True,date),self,elementCount);
        xmlPage.unlink();
      except:
        self.gui.log("something goes wrong while processing "+link);
        print xmlPage;
        self.gui.log("Exception: ");
        traceback.print_exc();
        self.gui.log("Stacktrace: ");
        traceback.print_stack();
    except:
      self.gui.log("something goes wrong while loading "+link);
  
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
  
  def readText(self,node,textNode):
    try:
      node = node.getElementsByTagName(textNode)[0].firstChild;
      return unicode(node.data);
    except:
      return "";
      