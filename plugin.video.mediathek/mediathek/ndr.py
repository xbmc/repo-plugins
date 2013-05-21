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
import pprint
from mediathek import *
from xml.dom import minidom;

class NDRMediathek(Mediathek):
  @classmethod
  
  def name(self):
    return "NDR";
    
  def isSearchable(self):
    return True;
  
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    
    if(self.gui.preferedStreamTyp == 0): #http
      self.baseType = "http";
    elif (self.gui.preferedStreamTyp == 1):  #rtmp
      self.baseType = "rtmp"
    elif (self.gui.preferedStreamTyp == 2): #mms
      self.baseType ="mms";
#    elif (self.gui.preferedStreamTyp == 3): #mov
#      self.baseType ="mov";
    else:
      self.baseType ="rtmp";

    self.pageSize = "30";
     
    self.rootLink = "http://www.ndr.de"
    self.menuLink = self.rootLink+"/mediathek/mediathek100-mediathek_medium-tv_searchtype-"
        
    self.searchLink = self.rootLink+"/mediathek/mediatheksuche101.html?pagenumber=1&search_video=true&"
    
    self.regex_extractVideoLink = re.compile("rtmpt://ndr.fcod.llnwd.net/a3715/d1/flashmedia/streams/ndr/(.*\\.)(hi.mp4|lo.flv)");  
    
    #self.rtmpBaseLink = "rtmpt://ndr.fcod.llnwd.net/a3715/d1/flashmedia/streams/ndr/";
    self.rtmpBaseLink = "rtmp://cp160844.edgefcs.net/ondemand/flashmedia/streams/ndr/";
    #self.mmsBaseLink = "mms://ndr.wmod.llnwd.net/a3715/d1/msmedia/";
    self.mmsBaseLink = "mms://a874.v1608102.c160810.g.vm.akamaistream.net/7/874/160810/v0001/wm.origin.ndr.gl-systemhaus.de/msmedia/";
    self.httpBaseLink = "http://media.ndr.de/progressive/";
    
    
    #Hauptmenue
    self.menuTree = [
      TreeNode("0","Die neuesten Videos",self.menuLink+"teasershow_pageSize-"+self.pageSize+".xml",True),
      ];
    
    broadcastsLink = self.menuLink+"broadcasts.xml"
    broadcastsLinkPage = self.loadConfigXml(broadcastsLink);
    
    menuNodes = broadcastsLinkPage.getElementsByTagName("broadcast");
    displayObjects = [];
    x = 1
    for menuNode in menuNodes:
        menuId = menuNode.getAttribute('id')
        menuItem = unicode(menuNode.firstChild.data)
        menuLink = self.rootLink+"/mediatheksuche105_broadcast-"+menuId+"_format-video_page-1.html"
        self.menuTree.append(TreeNode(str(x),menuItem,menuLink,True));
        x = x+1
    
  def buildPageMenu(self, link, initCount):
    self.gui.log("buildPageMenu: "+link);
    
    htmlPage = self.loadPage(link);
    
    regex_extractVideoItems = re.compile("<div class=\"m_teaser\">(.*?)</p>\n</div>\n</div>",re.DOTALL);
    regex_extractVideoItemHref = re.compile("<a href=\".*?/([^/]*?)\.html\" title=\".*?\" .*?>");
    regex_extractVideoItemDate = re.compile("<div class=\"subline\">.*?(\\d{2}\.\\d{2}\.\\d{4} \\d{2}:\\d{2})</div>");
    
    videoItems = regex_extractVideoItems.findall(htmlPage)
    nodeCount = initCount + len(videoItems)
    
    for videoItem in videoItems:
      videoID = regex_extractVideoItemHref.search(videoItem).group(1)
      dateString = regex_extractVideoItemDate.search(videoItem).group(1)
      dateTime = time.strptime(dateString,"%d.%m.%Y %H:%M");
      self.extractVideoInformation(videoID,dateTime,nodeCount)
    
    #Pagination (weiter)
    regex_extractNextPage = re.compile("<a href=\"(.*?)\" class=\"button_next\"  title=\"(.*?)\".*?>")
    nextPageHref = regex_extractNextPage.search(htmlPage)
    if nextPageHref:
        menuItemName = nextPageHref.group(2)
        link = self.rootLink+nextPageHref.group(1)
        self.gui.buildVideoLink(DisplayObject(menuItemName,"","","description",link,False),self,nodeCount+1);
    
  def searchVideo(self, searchText):
    searchText = searchText.encode("UTF-8")
    searchText = urllib.urlencode({"query" : searchText})
    self.buildPageMenu(self.searchLink+searchText,0);   
        
  def readText(self,node,textNode):
    try:
      node = node.getElementsByTagName(textNode)[0].firstChild;
      return unicode(node.data);
    except:
      return "";
  
  def loadConfigXml(self, link):
    self.gui.log("load:"+link)
    xmlPage = self.loadPage(link);
    xmlPage = xmlPage.replace(" & "," &amp; ")
    
    try:
        xmlDom = minidom.parseString(xmlPage);
    except:
        xmlDom = False
    return xmlDom;
  
  def loadVideoLinks(self, videoNode):
    videoSources = videoNode.getElementsByTagName("sources")[0]
    videoSource = self.readText(videoSources, "source")
        
    videoInfo = self.regex_extractVideoLink.match(videoSource).group(1)
    
    link = {}
    if self.baseType == "http":
        link[0] = self.httpBaseLink+videoInfo+"lo.mp4";
        link[1] = self.httpBaseLink+videoInfo+"hi.mp4";
        link[2] = self.httpBaseLink+videoInfo+"hq.mp4";
    elif self.baseType == "mms":
        link[0] = self.mmsBaseLink+videoInfo+"wm.lo.wmv";
        link[1] = self.mmsBaseLink+videoInfo+"wm.hi.wmv";
        link[2] = self.mmsBaseLink+videoInfo+"wm.hq.wmv";
    else:
        link[0] = self.rtmpBaseLink+videoInfo+"lo.mp4";
        link[1] = self.rtmpBaseLink+videoInfo+"hi.mp4";
        link[2] = self.rtmpBaseLink+videoInfo+"hq.mp4"; 
    
    links = {};
    links[0] = SimpleLink(link[0], 0);
    links[1] = SimpleLink(link[1], 0);
    links[2] = SimpleLink(link[2], 0);
    
    return links;
    
  def extractVideoInformation(self, videoId, pubDate, nodeCount):
    videoPage = self.rootLink+"/fernsehen/sendungen/media/"+videoId+"-avmeta.xml"
    videoNode = self.loadConfigXml(videoPage)

    if videoNode:
        videoNode = videoNode.getElementsByTagName("video")[0]
        title = self.readText(videoNode,"headline");
        description = self.readText(videoNode,"teaser");
        duration = self.readText(videoNode,"duration");
        
        imageNode = videoNode.getElementsByTagName("images")[0].getElementsByTagName("image")
        if len(imageNode):
            imageNode = imageNode[0]
            imageNode = imageNode.getElementsByTagName("urls")[0]
            picture = self.readText(imageNode, "url")
        else:
            picture = None
    
        links = self.loadVideoLinks(videoNode)

        self.gui.buildVideoLink(DisplayObject(title,"",picture,description,links,True,pubDate,duration),self,nodeCount);
   
