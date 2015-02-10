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
import re,math,traceback,time
from mediathek import *
from xml.dom import minidom
from xml.dom import Node;
    
class ZDFMediathek(Mediathek):
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    if(self.gui.preferedStreamTyp == 0):
      self.baseType = "http_na_na";
    elif (self.gui.preferedStreamTyp == 1):  
      self.baseType = "rtmp_smil_http"
    elif (self.gui.preferedStreamTyp == 2):
      self.baseType ="mms_asx_http";
    else:
      self.baseType ="rtsp_mov_http";
    
    self.menuTree = (
      TreeNode("0","Startseite","http://www.zdf.de/ZDFmediathek/hauptnavigation/startseite?flash=off",True,
        (
          TreeNode("0.0","Tipps","http://www.zdf.de/ZDFmediathek/hauptnavigation/startseite/tipps?flash=off",True),
          TreeNode("0.1","Ganze Sendungen","http://www.zdf.de/ZDFmediathek/hauptnavigation/nachrichten/ganze-sendungen?flash=off",True),
          TreeNode("0.2","Meist Gesehen","http://www.zdf.de/ZDFmediathek/hauptnavigation/nachrichten/meist-gesehen?flash=off",True)
        )
      ),
      TreeNode("1","Nachrichten","http://www.zdf.de/ZDFmediathek/hauptnavigation/nachrichten?flash=off",True),
      TreeNode("2","Sendung verpasst?","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-verpasst?flash=off",False,(
          TreeNode("2.0","Heute","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-verpasst/day0?flash=off",True),
          TreeNode("2.1","Gestern","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-verpasst/day1?flash=off",True),
          TreeNode("2.2","vor 2 Tagen","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-verpasst/day2?flash=off",True),
          TreeNode("2.3","vor 3 Tagen","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-verpasst/day3?flash=off",True),
          TreeNode("2.4","vor 4 Tagen","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-verpasst/day4?flash=off",True),
          TreeNode("2.5","vor 5 Tagen","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-verpasst/day5?flash=off",True),
          TreeNode("2.6","vor 6 Tagen","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-verpasst/day6?flash=off",True),
          TreeNode("2.7","vor 7 Tagen","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-verpasst/day7?flash=off",True),
        )
      ),
      TreeNode("3","LIVE","http://www.zdf.de/ZDFmediathek/hauptnavigation/live?flash=off",False,(
          TreeNode("3.0","Heute","http://www.zdf.de/ZDFmediathek/hauptnavigation/live/day0?flash=off",True),
          TreeNode("3.1","Gestern","http://www.zdf.de/ZDFmediathek/hauptnavigation/live/day1?flash=off",True),
          TreeNode("3.2","vor 2 Tagen","http://www.zdf.de/ZDFmediathek/hauptnavigation/live/day2?flash=off",True),
          TreeNode("3.3","vor 3 Tagen","http://www.zdf.de/ZDFmediathek/hauptnavigation/live/day3?flash=off",True),
          TreeNode("3.4","vor 4 Tagen","http://www.zdf.de/ZDFmediathek/hauptnavigation/live/day4?flash=off",True),
          TreeNode("3.5","vor 5 Tagen","http://www.zdf.de/ZDFmediathek/hauptnavigation/live/day5?flash=off",True),
          TreeNode("3.6","vor 6 Tagen","http://www.zdf.de/ZDFmediathek/hauptnavigation/live/day6?flash=off",True),
          TreeNode("3.7","vor 7 Tagen","http://www.zdf.de/ZDFmediathek/hauptnavigation/live/day7?flash=off",True),
        )
      ),
      TreeNode("4","Sendungen A-Z","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z?flash=off",False,
        (
          TreeNode("4.0","ABC","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz0?flash=off",True),
          TreeNode("4.1","DEF","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz1?flash=off",True),
          TreeNode("4.2","GHI","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz2?flash=off",True),
          TreeNode("4.3","JKL","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz3?flash=off",True),
          TreeNode("4.4","MNO","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz4?flash=off",True),
          TreeNode("4.5","PQRS","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz5?flash=off",True),
          TreeNode("4.6","TUV","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz6?flash=off",True),
          TreeNode("4.7","WXYZ","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz7?flash=off",True),
          TreeNode("4.8","0-9","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz8?flash=off",True),
        )
      ),
      TreeNode("5","Rubriken","http://www.zdf.de/ZDFmediathek/hauptnavigation/rubriken?flash=off",True),
      TreeNode("6","Themen","http://www.zdf.de/ZDFmediathek/hauptnavigation/themen?flash=off",True),
      );
    regex_imageLink = "/ZDFmediathek/contentblob/\\d+/timg\\d+x\\d+blob/\\d+";
    #ZDFmediathek/beitrag/live/
    self.regex_videoPageLink = "/ZDFmediathek/beitrag/((video)|(live))/\\d+?/.*flash=off";
    self.regex_topicPageLink = "/ZDFmediathek/((kanaluebersicht/aktuellste/\\d+.*)|(hauptnavigation/nachrichten/ganze-sendungen.*))flash=off";
    
    self._regex_extractTopicObject = re.compile("<li.*\\s*<div class=\"image\">\\s*<a href=\""+self.regex_topicPageLink+"\">\\s*<img src=\""+regex_imageLink+"\" title=\".*\" alt=\".*\"/>\\s*</a>\\s*</div>\\s*<div class=\"text\">\\s*<p( class=\".*\"){0,1}>\\s*<a href=\""+self.regex_topicPageLink+"\"( class=\"orangeUpper\"){0,1}>.*</a>\\s*</p>\\s*<p>\\s*<b>\\s*<a href=\""+self.regex_topicPageLink+"\">\\s*.*</a>");
    self._regex_extractPageNavigation = re.compile("<a href=\""+self.regex_topicPageLink+"\" .*>.*?</a>");
    
    
    self._regex_extractPictureLink = re.compile(regex_imageLink);
    self._regex_extractPicSize = re.compile("\\d{2,4}x\\d{2,4}");
    
    self._regex_extractTopicPageLink = re.compile(self.regex_topicPageLink);    
    self._regex_extractTopicTitle = re.compile("<a href=\"/ZDFmediathek/.*flash=off\".*>[^<].*</a>");
    
    self._regex_extractVideoPageLink = re.compile(self.regex_videoPageLink);
    self._regex_extractVideoID = re.compile("/\\d+/");
    self._regex_extractVideoLink = re.compile("");
    self.replace_html = re.compile("<.*?>");
    
    self.rootLink = "http://www.zdf.de";
    self.searchSite = "http://www.zdf.de/ZDFmediathek/suche?flash=off"
    self.xmlService = "http://www.zdf.de/ZDFmediathek/xmlservice/web/beitragsDetails?id=%s&ak=web";
  @classmethod
  def name(self):
    return "ZDF";
    
  def isSearchable(self):
    return True;
  
  def searchVideo(self, searchText):
    self.gui.log("searchVideo: "+searchText);
    values ={'sucheBtn.x':'25',
             'sucheBtn.y':'8',
             'sucheText': searchText}
    mainPage = self.loadPage(self.searchSite,values);
    videoPageLinks = list(self._regex_extractVideoPageLink.finditer(mainPage));
    
    self.initCount = 0;
    self.countTopic = 0;
    self.countVideo = len(videoPageLinks);
    
    self.extractVideoObjects(videoPageLinks);
    
  def buildPageMenu(self, link, initCount):
    self.gui.log("buildPageMenu: "+link);
    mainPage = self.loadPage(link);
    
    topicPageLinks = list(self._regex_extractTopicObject.finditer(mainPage));
    videoPageLinks = list(self._regex_extractVideoPageLink.finditer(mainPage));
    pageNavigation = list(self._regex_extractPageNavigation.finditer(mainPage));
        
    self.initCount = initCount;
    self.countTopic = len(topicPageLinks)+len(pageNavigation);
    self.countVideo = len(videoPageLinks);
    
    self.extractTopicObjects(topicPageLinks);
    self.extractVideoObjects(videoPageLinks);
    self.extractPageNavigation(pageNavigation);
  
  def extractPageNavigation(self, links):
    for element in links:
      element = element.group()
      
      title = self._regex_extractTopicTitle.search(element).group();
      title = unicode(title,'UTF-8');
      title = self.replace_html.sub("", title); #outerhtml wegschneiden
      title = title.replace("&nbsp;", ""); #sinnlose "steuerzeichen wegschneiden"
      
      videoPageLink = self.rootLink+self._regex_extractTopicPageLink.search(element).group();
      self.gui.buildVideoLink(DisplayObject(title,"","","",videoPageLink,False),self,self.getItemCount());
  
  def getItemCount(self):
    return self.initCount + self.countTopic + self.countVideo;
    
  def extractVideoObjects(self,videoPageLinks):
    lastID = -1;
    videos = []
    for pageLink in videoPageLinks:
      self.gui.log("pageLink: "+pageLink.group());
      videoID = self._regex_extractVideoID.search(pageLink.group()).group();
      videoID = videoID.replace("/","");
      if(not lastID == videoID):
        self.gui.log("append VideoID: %s len: %d"%(videoID,len(videos)));
        videos.append(videoID);
        lastID = videoID;
    
    self.countVideo = len(videos);
    self.gui.log("len %d"%(len(videos)));
    for videoID in videos:
      self.gui.log("decode VideoID: %s"%(videoID));
      self.loadConfigXml(videoID);
  
  def loadConfigXml(self, videoID):
    link = self.xmlService%(videoID);
    self.gui.log("load:"+link)
    xmlPage = self.loadPage(link);
    if(not xmlPage.startswith("<?xml")):
      return;
    try:  
      configXml = minidom.parseString(xmlPage);
      
      title = configXml.getElementsByTagName("title")[0].childNodes[0].data
      detail = configXml.getElementsByTagName("detail")[0].childNodes[0].data
      dateString = configXml.getElementsByTagName("airtime")[0].childNodes[0].data
      date = time.strptime(dateString,"%d.%m.%Y %H:%M");
      size = 0;
      picture = "";
      for picElement in configXml.getElementsByTagName("teaserimage"):
        picSizeString = picElement.getAttribute('key')
        picSizes = picSizeString.split("x");
        width = int(picSizes[0]);
        height = int(picSizes[0]);
        diag = math.sqrt(height*height+width*width);
        if(diag > size):
          size = diag;
          self.gui.log("%d %s"%(diag,picElement.childNodes[0].data));
          picture = picElement.childNodes[0].data;
      links = {};
      
      for streamObject in configXml.getElementsByTagName("formitaet"):
        baseType = streamObject.getAttribute("basetype")
        if(baseType.find(self.baseType)>-1):
          
          url = streamObject.getElementsByTagName("url")[0].childNodes[0].data;
          try:
            size = int(streamObject.getElementsByTagName("filesize")[0].childNodes[0].data);
          except:
            size = 0;
          if(self.baseType == "rtmp_smil_http"):
            links = self.getRtmpLinks(url, size);
            break;
          else:
            quality = streamObject.getElementsByTagName("quality")[0].childNodes[0].data;
            url = streamObject.getElementsByTagName("url")[0].childNodes[0].data;
            
            if url.find(".mp3") > -1:
              continue;

            if(quality == "low"):
              links[0] = SimpleLink(url, size);
            elif(quality == "high"):
              links[1] = SimpleLink(url, size);
            elif(quality == "veryhigh"):
              links[2] = SimpleLink(url, size);
            elif(quality == "hd"):
              links[3] = SimpleLink(url, size);
      if(len(links) == 0):
        links = {};
        for streamObject in configXml.getElementsByTagName("formitaet"):
          baseType = streamObject.getAttribute("basetype")
          if(baseType.find("asx_http")>-1):
            quality = streamObject.getElementsByTagName("quality")[0].childNodes[0].data;
            url = streamObject.getElementsByTagName("url")[0].childNodes[0].data;
            
            if(quality == "low"):
              links[0] = SimpleLink(url, size);
            elif(quality == "high"):
              links[1] = SimpleLink(url, size);
            elif(quality == "veryhigh"):
              links[2] = SimpleLink(url, size);
            elif(quality == "hd"):
              links[3] = SimpleLink(url, size); 
            break;
      configXml.unlink();
      if(len(links) > 0):
        self.gui.buildVideoLink(DisplayObject(title,"",picture,detail,links,True, date),self,self.getItemCount());
    except:
      self.gui.log("Error while processing the xml-file: %s"%link);
      print xmlPage;
      self.gui.log("Exception: ");
      traceback.print_exc();
      self.gui.log("Stacktrace: ");
      traceback.print_stack();
      #sys.exit();
  
  def getRtmpLinks(self, url, size):
    links = {};
    hostConfig = {};
    smilPage = self.loadPage(url);
    if(not smilPage.startswith("<?xml")):
      return None;
    
    xmlDocument = minidom.parseString(smilPage);
    
    self.cleanupNodes(xmlDocument.documentElement);
    xmlDocument.documentElement.normalize() 
    
    #extract hostData
    for paramGroup in xmlDocument.getElementsByTagName("paramGroup"):
      groupName = paramGroup.getAttribute("xml:id");
      print paramGroup.toxml()
      host = "";
      app = ""
      for param in paramGroup.childNodes:
        
        paramName = param.getAttribute("name");
        if(paramName == "app"): app = param.getAttribute("value");
        if(paramName == "host"): host = param.getAttribute("value");
      hostConfig[groupName] = "rtmp://"+host+"/"+app+"/";
      
    
    videoNodes = xmlDocument.getElementsByTagName("video");
   
    for videoNode in videoNodes:
      quality = videoNode.getElementsByTagName("param")[0].getAttribute("value");
      paramGroupName = videoNode.getAttribute("paramGroup");
      
      hostString = hostConfig[paramGroupName];
      urlString = videoNode.getAttribute("src");
      
      link = SimpleLink(hostString+" playPath="+urlString,size);
      if(quality == "low"):
        links[0] = link
      elif(quality == "high"):
        links[1] = link
      elif(quality == "veryhigh"):
        links[2] = link
      elif(quality == "hd"):
        links[3] = SimpleLink(url, size);
    xmlDocument.unlink();
    return links;
    
    
  def extractTopicObjects(self,pageLinks):
    for element in pageLinks:
      element = element.group()
      pictureLink = self.rootLink + self._regex_extractPictureLink.search(element).group();
      videoPageLink = self.rootLink + self._regex_extractTopicPageLink.search(element).group();
      titles = [];
      for title in self._regex_extractTopicTitle.findall(element):
        title = unicode(title,'UTF-8');
        title = self.replace_html.sub("", title); #outerhtml wegschneiden
        title = title.replace("&nbsp;", ""); #sinnlose "steuerzeichen wegschneiden"
        titles.append(title);
      while len(titles) < 2:
        titles.append("");
      self.gui.buildVideoLink(DisplayObject(titles[0],titles[1],pictureLink,"",videoPageLink,False),self,self.getItemCount());
  
  def cleanupNodes(self, rootNode):
    for node in rootNode.childNodes:
      if node.nodeType == Node.TEXT_NODE:
        node.data = node.data.strip()
      else:
        self.cleanupNodes(node);
