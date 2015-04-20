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
import re,time
from mediathek import *
from xml.dom import minidom;


regex_dateString = re.compile("\\d{2} ((\\w{3})|(\\d{2})) \\d{4}");
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

class DreiSatMediathek(Mediathek):
  @classmethod
  def name(self):
    return "3Sat";
  def isSearchable(self):
    return True;
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
    
    
    self.webEmType = "video/webm";
    self.menuTree = (
      TreeNode("0","Bauerfeind","http://www.3sat.de/mediathek/rss/mediathek_bauerfeind.xml",True),
      TreeNode("1","Bookmark","http://www.3sat.de/mediathek/rss/mediathek_bookmark.xml",True),
      TreeNode("2",u"Börse","http://www.3sat.de/mediathek/rss/mediathek_boerse.xml",True),
      TreeNode("3","Buchzeit","http://www.3sat.de/mediathek/rss/mediathek_buchzeit.xml",True),
      TreeNode("4","daVinci","http://www.3sat.de/mediathek/rss/mediathek_davinci.xml",True),
      TreeNode("5","delta","http://www.3sat.de/mediathek/rss/mediathek_delta.xml",True),
      TreeNode("6","Film","http://www.3sat.de/mediathek/rss/mediathek_film.xml",True),
      TreeNode("7","Gero von Boehm","http://www.3sat.de/mediathek/rss/mediathek_gero.xml",True),
      TreeNode("8","hessenreporter","http://www.3sat.de/mediathek/rss/mediathek_hessenreporter.xml",True),
      TreeNode("9","hitec","http://www.3sat.de/mediathek/rss/mediathek_hitec.xml",True),
      TreeNode("10","Kabarett","http://www.3sat.de/mediathek/rss/mediathek_kabarett.xml",True),
      TreeNode("11","Kinomagazin","http://www.3sat.de/mediathek/rss/mediathek_kinomag.xml",True),
      TreeNode("12","Kulturzeit","http://www.3sat.de/mediathek/rss/mediathek_Kulturzeit.xml",True),
      TreeNode("13","makro","http://www.3sat.de/mediathek/rss/mediathek_makro.xml",True),
      TreeNode("14","Musik","http://www.3sat.de/mediathek/rss/mediathek_musik.xml",True),
      TreeNode("15","nano","http://www.3sat.de/mediathek/rss/mediathek_nano.xml",True),
      TreeNode("16","neues","http://www.3sat.de/mediathek/rss/mediathek_neues.xml",True),
      TreeNode("17",u"Peter Voß fragt","http://www.3sat.de/mediathek/rss/mediathek_begegnungen.xml",True),
      TreeNode("18","Recht brisant","http://www.3sat.de/mediathek/rss/mediathek_Recht%20brisant.xml",True),
      TreeNode("19","scobel","http://www.3sat.de/mediathek/rss/mediathek_scobel.xml",True),
      TreeNode("20","SCHWEIZWEIT","http://www.3sat.de/mediathek/rss/mediathek_schweizweit.xml",True),
      TreeNode("21","Theater","http://www.3sat.de/mediathek/rss/mediathek_theater.xml",True),
      TreeNode("22","vivo","http://www.3sat.de/mediathek/rss/mediathek_vivo.xml",True),
      );
      
    self.rootLink = "http://www.3sat.de"
    self.searchLink = 'http://www.3sat.de/mediathek/mediathek';
    link = "/mediathek/mediathek.php\\?obj=\\d+";
    self.regex_searchResult = re.compile("href=\""+link+"\" class=\"media_result_thumb\"");
    self.regex_searchResultLink = re.compile(link)
    self.regex_searchLink = re.compile("http://(w|f)streaming.zdf.de/.*?(\\.asx|\\.smil)")
    self.regex_searchTitle = re.compile("<h2>.*</h2>");
    self.regex_searchDetail = re.compile("<span class=\"text\">.*");
    self.regex_searchDate = re.compile("\\d{2}.\\d{2}.\\d{4}");
    self.regex_searchImage = re.compile("(/dynamic/mediathek/stills/|/mediaplayer/stills/)\\d*_big\\.jpg");
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
      video = video.replace("fstreaming","wstreaming").replace(".smil",".asx");
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
    for itemNode in nodes:
      self.extractVideoInformation(itemNode,nodeCount);
  
  def parseDate(self,dateString):
    dateString = regex_dateString.search(dateString).group();
    for month in month_replacements.keys():
      dateString = dateString.replace(month,month_replacements[month]);
    return time.strptime(dateString,"%d %m %Y");
    
  def extractVideoInformation(self, itemNode, nodeCount):
    title = self.readText(itemNode,"title");
    
    dateString = self.readText(itemNode,"pubDate");
    pubDate = self.parseDate(dateString);
    
    descriptionNode = itemNode.getElementsByTagName("description")[0].firstChild.data;
    description = unicode(descriptionNode);
    
    pictureNode = itemNode.getElementsByTagName("media:thumbnail")[0];
    picture = pictureNode.getAttribute("url");
    links = {};
    for contentNode in itemNode.getElementsByTagName("media:content"):
      mediaType = contentNode.getAttribute("type");
      if(not (self.baseType == mediaType or mediaType == self.webEmType)):
        continue;
      
      height = int(contentNode.getAttribute("height"));
      url = contentNode.getAttribute("url");
      size = int(contentNode.getAttribute("fileSize"));
      if(height < 150):
        links[0] = SimpleLink(url, size);
      elif (height < 300):
        links[1] = SimpleLink(url, size);
      else:
        links[2] = SimpleLink(url, size);
    if links:
      self.gui.buildVideoLink(DisplayObject(title,"",picture,description,links,True, pubDate),self,nodeCount);
      
