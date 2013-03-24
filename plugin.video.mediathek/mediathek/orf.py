# -*- coding: utf-8 -*-
import re,time,urllib
from xml.dom import Node;
from xml.dom import minidom;
from mediathek import *

class ORFMediathek(Mediathek):
  def __init__(self, simpleXbmcGui):
    
    self.rootLink = "http://tvthek.orf.at"
    self.gui = simpleXbmcGui;
    self.menuTree = [];
    self.menuTree.append(TreeNode("0","Startseite","http://tvthek.orf.at/",True));
    
    menuPage = self.loadPage(self.rootLink+"/programs");
    
    findMenuLink = re.compile("<li><a href=\"(/programs/.*?)\" title=\".*?\">(.*?)</a></li>");
    findCategorie = re.compile("<h4>(.*?)</h4>\\s*?<ul>((\\s*?%s\\s*?)+)</ul>"%findMenuLink.pattern)
    
    categories = [];
    
    for categorieMatch in findCategorie.finditer(menuPage):
      
      title = categorieMatch.group(1);
      
      items = [];
      for menuMatch in findMenuLink.finditer(categorieMatch.group(2)):
        items.append(TreeNode("1.%d.%d"%(len(categories),len(items)), menuMatch.group(2),"%s%s"%(self.rootLink,menuMatch.group(1)),True));
      
      categories.append(TreeNode("1.%d"%len(categories), title,"",False,items));
    
    self.menuTree.append(TreeNode("1","Sendungen","",False,categories));
    
    videoLinkPage = "/programs/.*"
    imageLink = "http://tvthek.orf.at/assets/.*?.jpeg"
    

    self.regex_extractVideoPageLink = re.compile(videoLinkPage+"?\"");
    self.regex_extractImageLink = re.compile(imageLink);
    self.regex_extractTitle = re.compile("<strong>.*<span");
    self.regex_extractVideoLink = re.compile("/programs/.*.asx");
    self.regex_extractVideoObject = re.compile("<a href=\""+videoLinkPage+"\" title=\".*\">\\s*<span class=\"spcr\">\\s*<img src=\""+imageLink+"\" title=\".*\" alt=\".*\" />\\s*<span class=\".*\"></span>\\s*<strong>.*<span class=\"nowrap duration\">.*</span></strong>\\s*<span class=\"desc\">.*</span>\\s*</span>\\s*</a>");
    
    self.regex_extractSearchObject = re.compile("<li class=\"clearfix\">\\s*<a href=\".*\" title=\".*\" class=\".*\"><img src=\".*\" alt=\".*\" /><span class=\"btn_play\">.*</span></a>\\s*<p>.*</p>\\s*<h4><a href=\".*\" title=\".*\">.*</a></h4>\\s*<p><a href=\".*\" title=\".*\"></a></p>\\s*</li>");
    
    self.regex_extractProgrammLink = re.compile("/programs/.*?\"");
    self.regex_extractProgrammTitle = re.compile("title=\".*?\"");
    self.regex_extractProgrammPicture = re.compile("/binaries/asset/segments/\\d*/image1");
    
    self.regex_extractFlashVars = re.compile("ORF.flashXML = '.*?'");
    self.regex_extractHiddenDate = re.compile("\d{4}-\d{2}-\d{2}");
    self.regex_extractXML = re.compile("%3C.*%3E");
    self.regex_extractReferingSites = re.compile("<li><a href=\"/programs/\d+.*?/episodes/\d+.*?\"");
    
    self.replace_html = re.compile("<.*?>");
    
    
    self.searchLink = "http://tvthek.orf.at/search?q="
  @classmethod
  def name(self):
    return "ORF";
    
  def isSearchable(self):
    return True;
  
  def createVideoLink(self,title,image,videoPageLink,elementCount):
    videoPage = self.loadPage(self.rootLink+videoPageLink);
    
    videoLink = self.regex_extractVideoLink.search(videoPage);
    if(videoLink == None):
      return;
    
    simpleLink = SimpleLink(self.rootLink+videoLink.group(), 0);
    videoLink = {0:simpleLink};
      
    counter = 0
    playlist = self.loadPage(simpleLink.basePath);
    for line in playlist:
      counter+=1;

    if(counter == 1):
      self.gui.buildVideoLink(DisplayObject(title,"",image,"",videoLink, True, time.gmtime()),self,elementCount);
    else:
      self.gui.buildVideoLink(DisplayObject(title,"",image,"",videoLink, "PlayList", time.gmtime()),self,elementCount);
  
  def searchVideo(self, searchText):
    link = self.searchLink = "http://tvthek.orf.at/search?q="+searchText;
    mainPage = self.loadPage(link);
    result = self.regex_extractSearchObject.findall(mainPage);
    
    for searchObject in result:
      videoLink = self.regex_extractProgrammLink.search(searchObject).group().replace("\"","");
      title = self.regex_extractProgrammTitle.search(searchObject).group().replace("title=\"","").replace("\"","");
      title = title.decode("UTF-8");
      pictureLink = self.regex_extractProgrammPicture.search(searchObject).group();
      
      print videoLink;
      
      self.createVideoLink(title,pictureLink,videoLink, len(result));
  
  def extractLinksFromFlashXml(self, flashXml, date, elementCount):
    print flashXml.toprettyxml().encode('UTF-8');
    playlistNode = flashXml.getElementsByTagName("Playlist")[0];
    linkNode=flashXml.getElementsByTagName("AsxUrl")[0];
    link=linkNode.firstChild.data;
    asxLink = SimpleLink(self.rootLink+link,0);
    videoLink = {0:asxLink};
    for videoItem in playlistNode.getElementsByTagName("Items")[0].childNodes:
      if(videoItem.nodeType == Node.ELEMENT_NODE):
        titleNode=videoItem.getElementsByTagName("Title")[0];
        
        descriptionNode=videoItem.getElementsByTagName("Description")[0];
        title=titleNode.firstChild.data;
                
        stringArray = link.split("mp4:");
        
        try:
          description=descriptionNode.firstChild.data;
        except:
          description="";
        self.gui.buildVideoLink(DisplayObject(title,"","",description,videoLink, True, date),self,elementCount);
        
  def extractFlashLinks(self, flashVars,videoPageLinks,elementCount):
    for flashVar in flashVars:
      encodedXML = self.regex_extractXML.search(flashVar).group();
      
      dateString = self.regex_extractHiddenDate.search(flashVar).group();
      date = time.strptime(dateString,"%Y-%m-%d");      
      
      parsedXML = minidom.parseString(urllib.unquote(encodedXML));  
      self.extractLinksFromFlashXml(parsedXML, date,elementCount);
    
    
    for videoPageLink in videoPageLinks:
      videoPageLink = self.rootLink+videoPageLink.replace("<li><a href=\"","").replace("\"","");
      print videoPageLink;
      videoPage = self.loadPage(videoPageLink);
      flashVars = self.regex_extractFlashVars.findall(videoPage);
      for flashVar in flashVars:
        encodedXML = self.regex_extractXML.search(flashVar).group();
        
        dateString = self.regex_extractHiddenDate.search(flashVar).group();
        date = time.strptime(dateString,"%Y-%m-%d");
        
        parsedXML = minidom.parseString(urllib.unquote(encodedXML));  
        self.extractLinksFromFlashXml(parsedXML,date,elementCount);
    
    
    
    
  def buildPageMenu(self, link, initCount):
    mainPage = self.loadPage(link);
    videoPageLinks = self.regex_extractReferingSites.findall(mainPage);
    flashVars = self.regex_extractFlashVars.findall(mainPage);
    links = self.regex_extractVideoObject.findall(mainPage);
    elementCount = initCount + len(links)+len(flashVars)+len(videoPageLinks);
    
    self.extractFlashLinks(flashVars,videoPageLinks,elementCount);
    
    for linkObject in links:
      
      videoLink = self.regex_extractVideoPageLink.search(linkObject).group().replace("\"","");
      
      image = self.regex_extractImageLink.search(linkObject).group();
      title = self.regex_extractTitle.search(linkObject).group().decode('UTF8');
      
      title = self.replace_html.sub("", title);
      title = title.replace(" <span","");
      
      self.createVideoLink(title,image,videoLink, elementCount);

