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
import re, time;
from mediathek import *

class ARDMediathek(Mediathek):
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    self.rootLink = "http://www.ardmediathek.de"
    self.menuTree = (
                      TreeNode("0","Neuste Videos",self.rootLink+"/ard/servlet/content/3474442",True),
                      TreeNode("1","Kategorien","",False,(
                        TreeNode("1.0",u"Nachrichten",self.rootLink+"/kategorien/nachrichten?clipFilter=fernsehen&documentId=506",True),
                        TreeNode("1.1",u"Politik & Zeitgeschehen",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=206",True),
                        TreeNode("1.2",u"Wirtschaft & Börse",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=726",True),
                        TreeNode("1.3",u"Sport",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=618",True),
                        TreeNode("1.4",u"Ratgeber & Technik",self.rootLink+"/kategorien/ratgeber-und-technik?clipFilter=fernsehen&documentId=636",True),
                        TreeNode("1.5",u"Gesundheit & Ernährung",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=548",True),
                        TreeNode("1.6",u"Kultur & Gesellschaft",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=564",True),
                        TreeNode("1.7",u"Musik",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=1062",True),
                        TreeNode("1.8",u"Literatur",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=1228",True),
                        TreeNode("1.9",u"Medien",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=1230",True),
                        TreeNode("1.10",u"Filme & Serien",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=546",True),
                        TreeNode("1.11",u"Unterhaltung & Lifestyle",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=1232",True),
                        TreeNode("1.12",u"Comedy & Satire",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=544",True),
                        TreeNode("1.13",u"Wissen & Bildung",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=568",True),
                        TreeNode("1.14",u"Natur & Freizeit",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=920",True),
                        TreeNode("1.15",u"Kinder & Familie",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=608",True),
                        TreeNode("1.16",u"Religion & Kirche",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=678",True),
                        TreeNode("1.17",u"In der Region",self.rootLink+"/ard/servlet/content/3516690?clipFilter=fernsehen&documentId=550",True),
                        )),
                      TreeNode("2","Sendungen von A-Z","",False,(
                        TreeNode("2.0","0-9",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=0-9/index.html",True),
                        TreeNode("2.1","A",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=A/index.html",True),
                        TreeNode("2.2","B",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=B/index.html",True),
                        TreeNode("2.3","C",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=C/index.html",True),
                        TreeNode("2.4","D",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=D/index.html",True),
                        TreeNode("2.5","E",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=E/index.html",True),
                        TreeNode("2.6","F",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=F/index.html",True),
                        TreeNode("2.7","G",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=G/index.html",True),
                        TreeNode("2.8","H",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=H/index.html",True),
                        TreeNode("2.9","I",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=I/index.html",True),
                        TreeNode("2.10","J",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=J/index.html",True),
                        TreeNode("2.11","K",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=K/index.html",True),
                        TreeNode("2.12","L",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=L/index.html",True),
                        TreeNode("2.13","M",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=M/index.html",True),
                        TreeNode("2.14","N",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=N/index.html",True),
                        TreeNode("2.15","O",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=O/index.html",True),
                        TreeNode("2.16","P",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=P/index.html",True),
                        TreeNode("2.17","Q",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=Q/index.html",True),
                        TreeNode("2.18","R",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=R/index.html",True),
                        TreeNode("2.19","S",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=S/index.html",True),
                        TreeNode("2.20","T",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=T/index.html",True),
                        TreeNode("2.21","U",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=U/index.html",True),
                        TreeNode("2.22","V",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=V/index.html",True),
                        TreeNode("2.23","W",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=W/index.html",True),
                        TreeNode("2.24","X",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=X/index.html",True),
                        TreeNode("2.25","Y",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=Y/index.html",True),
                        TreeNode("2.26","Z",self.rootLink+"/ard/servlet/ajax-cache/3474820/view=list/initial=Z/index.html",True),
                        )),
                      )
      
    videoDocument_link_Regex = "/.*?documentId=(\\d*)"
    metaInfo_link_Regex = "/ard/servlet/ajax-cache/\\d*/view=ajax(/clipFilter=fernsehen){0,1}(/isFromList=true){0,1}/index.html"
    ajaxDocumentLink = "/ard/servlet/ajax-cache/(\\d*)/view=(switch|ajax|list)(/clipFilter=fernsehen){0,1}(/content=fernsehen){0,1}(/documentId=\\d*){0,1}/index.html"
    self.findImage_regex = "<img.*?src=\".*?\".*?/>"; #?
    #Regex für das Parsen der hauptseiten
    self.regex_ajaxLinkTag = re.compile("<a href=\""+ajaxDocumentLink+"\" title=\"\"><span>Neueste Clips</span></a>")
    self.regex_ajaxLink = re.compile(ajaxDocumentLink);
    self.regex_videoLinks = re.compile("<img.*?src=\"(.*?)\".*?/>\\s*?</div>\\s*?<h3 class=\"mt-title\">\\s*?<a href=\""+videoDocument_link_Regex+"\" class=\".*\" rel=\""+metaInfo_link_Regex+"\">");
    self.regex_videoSeriesLinks = re.compile("<a id=\".*\" class=\".*\" rel=\""+metaInfo_link_Regex+"\" href=\""+videoDocument_link_Regex+"\">");
    self.regex_subLinks = re.compile("<a class=\"mt-box_preload.*?\" href=\""+ajaxDocumentLink+"\">");
    self.regex_videoDocumentLink = re.compile(videoDocument_link_Regex);
    self.regex_MetaInfo = re.compile(metaInfo_link_Regex);
    self.regex_Date = re.compile("\\d{2}\\.\\d{2}\\.\\d{2}");
    
    
    self.replace_html = re.compile("<.*?>");
    
    #regex für die MetaInfos
    self.regex_pictureLink = re.compile("ard/[^\"]*");
    self.regex_title = re.compile("<h3 class=\"mt-title\">.*<a.*>[^<]*?</a>")
    self.regex_category = re.compile("<p class=\"mt-source\">.*</p>");
    self.regex_description = re.compile("<p.*?>.*?</p>",re.DOTALL);
    
    #regex für das extrahieren des Medialinks
    self.regex_MediaCollection = re.compile("mediaCollection\\.addMediaStream\\(\\d*, \\d*, \".*\", \".*\", \".*?\"\\);");
    self.regex_findLinks = re.compile("\".*?\"");
    self.searchLink = "http://www.ardmediathek.de/ard/servlet/content/3517006?detail=%d&s=%s"
    
  @classmethod
  def name(self):
    return "ARD";
  def isSearchable(self):
    return True;
    
  def searchVideo(self, searchText):
    sendungen = self.searchSendungen(searchText);
    clips = self.searchClips(searchText);
    
    elementCount = len(sendungen)+len(clips);
    
    for sendung in sendungen:
      self.buildSearchResultLink(sendung, False, elementCount);
    for clip in clips:
      self.buildSearchResultLink(clip, True, elementCount);
  
  def searchSendungen(self, searchText):
    searchLink = self.searchLink%(10,searchText);
    self.gui.log(searchLink);   
    resultPage = self.loadPage(searchLink);
    return list(self.regex_videoLinks.finditer(resultPage));
  
  def searchClips(self, searchText):
    searchLink = self.searchLink%(40,searchText);
    self.gui.log(searchLink);   
    resultPage = self.loadPage(searchLink);
    return list(self.regex_videoLinks.finditer(resultPage));  
  
  def buildSearchResultLink(self, element, isPlayable, elementCount):
    imageLink = element.group(1);
    element = element.group()
    videoDocumentLink = self.regex_videoDocumentLink.search(element).group();
    metaInfoLink = self.regex_MetaInfo.search(element).group();
    displayObject = self.extractMetaInfo(self.rootLink+metaInfoLink, imageLink);
    
    if(isPlayable):
      displayObject.link = self.getVideoLink(self.rootLink+videoDocumentLink);
    else:
      displayObject.link = self.rootLink+videoDocumentLink;
      displayObject.isPlayable = False;
      
    self.gui.buildVideoLink(displayObject, self, elementCount);
    
    
  def buildPageMenu(self, link, initCount, subLink = False):
    self.gui.log("Build Page Menu: "+link);    
    mainPage = self.loadPage(link);
    
    try:
      self.gui.log("Elements");
      if(subLink):
        link = self.regex_ajaxLink.search(mainPage).group();
        self.gui.log(link);
      else:
        htmlTag = self.regex_ajaxLinkTag.search(mainPage).group();
        link = self.regex_ajaxLink.search(htmlTag).group();
      
      ajaxPage = self.loadPage(self.rootLink + link);
      
      return self.extractVideoObjects(ajaxPage);
    except:
      self.gui.log("Categorien");
      elementCount = self.extractCategorieObjects(mainPage);
      if(elementCount == 0):
        for link in self.regex_subLinks.finditer(mainPage):
          link = link.group();
          link = self.regex_ajaxLink.search(link).group();
          self.gui.log("SubLink: "+link)
          elementCount += self.buildPageMenu(self.rootLink+link, 0,True);
          if(elementCount > 60):
            break;
      return elementCount;
          
          
      
      
  def extractCategorieObjects(self,mainPage):
    elements = list(self.regex_videoLinks.finditer(mainPage));
    counter = len(elements);
    for element in elements:
      imageLink = element.group(1);
      element = element.group(0)
      
      videoDocumentLink = self.regex_videoDocumentLink.search(element).group();
      metaInfoLink = self.regex_MetaInfo.search(element).group();
      
      displayObject = self.extractMetaInfo(self.rootLink+metaInfoLink, imageLink);
      if displayObject is not None:
        displayObject.link = self.rootLink+videoDocumentLink;
        displayObject.isPlayable = False;
        self.gui.buildVideoLink(displayObject, self, counter);
    return counter;
  
  def extractVideoObjects(self,mainPage):
    elements = list(self.regex_videoLinks.finditer(mainPage));
    counter = len(elements);
    for element in elements:
      
      imageLink = element.group(1);
      element = element.group(0)
      
      videoDocumentLink = self.regex_videoDocumentLink.search(element).group();
      metaInfoLink = self.regex_MetaInfo.search(element).group();
      
      displayObject = self.extractMetaInfo(self.rootLink+metaInfoLink, imageLink);
      displayObject.link = self.getVideoLink(self.rootLink+videoDocumentLink);
      
      self.gui.buildVideoLink(displayObject,self, counter);
    return counter;
      
  def extractMetaInfo(self, link, imageLink):
    self.gui.log("MetaInfoLink %s"%link);
    metaInfoPage = self.loadPage(link);
    
    if not metaInfoPage.find("Livestream") == -1:
      print "Livestream"
      return None
    
    pictureLink = self.rootLink + imageLink;
    title = self.regex_title.search(metaInfoPage).group()
    title = self.replace_html.sub("",title);
    title = unicode(title,"UTF-8");
    category = self.regex_title.search(metaInfoPage).group();
    category = self.replace_html.sub("",category);
    category = unicode(category,"UTF-8");
    category = category.replace("aus:&nbsp;","");
    description = self.regex_description.search(metaInfoPage).group();
    description = self.replace_html.sub("",description);
    description = unicode(description,'UTF-8');
    
    try:
      date = self.regex_Date.search(metaInfoPage).group();
      date = time.strptime(date,"%d.%m.%y");
    except:
      date = None;
      
    return DisplayObject(title,category,pictureLink,description,[],True, date);
    
  def getVideoLink(self, link):
    self.gui.log("VideoLink: "+link);
    videoPage = self.loadPage(link);
    linkDict = {};
    for element in self.regex_MediaCollection.findall(videoPage):
      splitted = element.split(", ");
      if(splitted[1] == "0"):
        quality = 0;
      elif(splitted[1] == "1"):
        quality = 1;
      else:
        quality = 2;

      links = self.regex_findLinks.findall(element);
      if(links[0] == "\"\""):
        linkDict[quality] = SimpleLink(links[1].replace("\"",""),0);
      else:
        url = links[0].replace("\"","")
        playPath = links[1].replace("\"","")
        linkDict[quality] = SimpleLink("%s playpath=%s"%(url,playPath),0);
    return linkDict;
