# -*- coding: utf-8 -*-
import re,time,urllib
from xml.dom import Node;
from xml.dom import minidom;
from mediathek import *

class ORFMediathek(Mediathek):
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    self.menuTree = (
      TreeNode("0","Startseite","http://tvthek.orf.at/",True),
      TreeNode("1","Sendungen","",False,
        (
          TreeNode("1.0",u"Bundesländer","",False,
            (
              TreeNode("1.0.0",u"Burgenland heute","http://tvthek.orf.at/programs/70021-Burgenland-heute",True),
              TreeNode("1.0.1",u"Kärnten heute","http://tvthek.orf.at/programs/70022-Kaernten-heute",True),
              TreeNode("1.0.2",u"Niederösterreich heute","http://tvthek.orf.at/programs/70017-Niederoesterreich-heute",True),
              TreeNode("1.0.3",u"Oberoesterreich heute","http://tvthek.orf.at/programs/70016-Oberoesterreich-heute",True),
              TreeNode("1.0.4",u"Salzburg heute","http://tvthek.orf.at/programs/70019-Salzburg-heute",True),
              TreeNode("1.0.5",u"Steiermark heute","http://tvthek.orf.at/programs/70020-Steiermark-heute",True),
              TreeNode("1.0.6",u"Tirol heute","http://tvthek.orf.at/programs/70023-Tirol-heute",True),
              TreeNode("1.0.6",u"Vorarlberg heute","http://tvthek.orf.at/programs/70024-Vorarlberg-heute",True),
              TreeNode("1.0.6",u"Wien heute","http://tvthek.orf.at/programs/70018-Wien-heute",True),
            )
          ),
          TreeNode("1.1",u"Dokumentationen","",False,
            (
              TreeNode("1.1.0",u"Erlebnis Österreich","http://tvthek.orf.at/programs/1200-Erlebnis-Oesterreich",True),
              TreeNode("1.1.1",u"Menschen & Mächte","http://tvthek.orf.at/programs/170407-Menschen---Maechte",True),
              TreeNode("1.1.2",u"Universum","http://tvthek.orf.at/programs/35429-Universum",True),
            )
          ),
          TreeNode("1.2",u"Information","",False,
            (
              TreeNode("1.2.0",u"Club 2","http://tvthek.orf.at/programs/1283-Club-2",True),
              TreeNode("1.2.1",u"Heute in Österreich","http://tvthek.orf.at/programs/1257-Heute-in-Oesterreich",True),
              TreeNode("1.2.2",u"Hohes Haus","http://tvthek.orf.at/programs/1264-Hohes-Haus",True),
              TreeNode("1.2.3",u"Im Zentrum","http://tvthek.orf.at/programs/1279-Im-Zentrum",True),
              TreeNode("1.2.4",u"Österreich-Bild","http://tvthek.orf.at/programs/1296-Oesterreich-Bild",True),
              TreeNode("1.2.5",u"Pressestunde","http://tvthek.orf.at/programs/1273-Pressestunde",True),
              TreeNode("1.2.6",u"Runder Tisch","http://tvthek.orf.at/programs/70010-Runder-Tisch",True),
              TreeNode("1.2.7",u"Südtirol heute","http://tvthek.orf.at/programs/1277675-Suedtirol-heute",True),
              TreeNode("1.2.8",u"Wetter","http://tvthek.orf.at/programs/1250-Wetter",True),
              TreeNode("1.2.9",u"Wetter (ÖGS)","http://tvthek.orf.at/programs/1786041-Wetter--OeGS-",True),
              TreeNode("1.2.10",u"Wetter ZiB 20","http://tvthek.orf.at/programs/972117-Wetter-ZIB-20",True),
              TreeNode("1.2.11",u"ZiB 9","http://tvthek.orf.at/programs/71256-ZiB-9",True),
              TreeNode("1.2.12",u"ZiB 11","http://tvthek.orf.at/programs/71276-ZiB-11",True),
              TreeNode("1.2.13",u"ZiB 13","http://tvthek.orf.at/programs/71280-ZiB-13",True),
              TreeNode("1.2.14",u"ZiB 17","http://tvthek.orf.at/programs/71284-ZiB-17",True),
              TreeNode("1.2.15",u"Zeit im Bild","http://tvthek.orf.at/programs/1203-Zeit-im-Bild",True),
              TreeNode("1.2.16",u"Zeit im Bild (ÖGS)","http://tvthek.orf.at/programs/145302-Zeit-im-Bild--OeGS-",True),
              TreeNode("1.2.17",u"ZiB 20","http://tvthek.orf.at/programs/1218-ZiB-20",True),
              TreeNode("1.2.18",u"ZiB 2","http://tvthek.orf.at/programs/1211-ZiB-2",True),
              TreeNode("1.2.19",u"Spät ZiB","http://tvthek.orf.at/programs/79134-Spaet-ZiB",True),
              TreeNode("1.2.20",u"ZiB 24","http://tvthek.orf.at/programs/1225-ZiB-24",True),
              TreeNode("1.2.21",u"ZiB Flash","http://tvthek.orf.at/programs/1232-ZiB-Flash",True),
            )
          ),
          TreeNode("1.3",u"Magazine","",False,
            (
              TreeNode("1.3.0",u"Bewusst gesund - das Magazin","http://tvthek.orf.at/programs/1714463-Bewusst-gesund---das-Magazin",True),
              TreeNode("1.3.1",u"Bürgeranwalt","http://tvthek.orf.at/programs/1339-Buergeranwalt",True),
              TreeNode("1.3.2",u"Bürgerforum","http://tvthek.orf.at/programs/1343-Buergerforum",True),
              TreeNode("1.3.3",u"Konkret","http://tvthek.orf.at/programs/1336-Konkret",True),
              TreeNode("1.3.4",u"Land und Leute","http://tvthek.orf.at/programs/1369-Land-und-Leute",True),
              TreeNode("1.3.5",u"Stöckl am Samstag","http://tvthek.orf.at/programs/1651-Stoeckl-am-Samstag",True),
              TreeNode("1.3.6",u"Thema","http://tvthek.orf.at/programs/1319-Thema",True),
              TreeNode("1.3.7",u"Vera exklusiv","http://tvthek.orf.at/programs/35440-Vera-exklusiv",True),
              TreeNode("1.3.8",u"Weltjournal","http://tvthek.orf.at/programs/1328-Weltjournal",True),
              TreeNode("1.3.9",u"Winterzeit","http://tvthek.orf.at/programs/1003023-Winterzeit",True),
              TreeNode("1.3.10",u"€co","http://tvthek.orf.at/programs/1346-Eco",True),
            )
          ),
          TreeNode("1.4",u"Kultur","",False,
            (
              TreeNode("1.4.0",u"a.viso","http://tvthek.orf.at/programs/1299-a-viso",True),
              TreeNode("1.4.0",u"Kulturmontag","http://tvthek.orf.at/programs/1303-Kulturmontag",True),
            )
          ),
          TreeNode("1.5",u"Sport","http://tvthek.orf.at/programs/1379-Sportbild",True,
            (
            )
          ),
          TreeNode("1.6",u"Religion","",False,
            (
              TreeNode("1.6.0",u"Kreuz & Quer","http://tvthek.orf.at/programs/1193-Kreuz---Quer",True),
              TreeNode("1.6.1",u"Orientierung","http://tvthek.orf.at/programs/1366-Orientierung",True),
              TreeNode("1.6.2",u"Religionen der Welt","http://tvthek.orf.at/programs/1656-Religionen-der-Welt",True),
              TreeNode("1.6.3",u"Was ich glaube","http://tvthek.orf.at/programs/1287-Was-ich-glaube",True),
            )
          ),
          TreeNode("1.7",u"Society","",False,
            (
              TreeNode("1.7.0",u"Chilli","http://tvthek.orf.at/programs/1504477-Chili",True),
              TreeNode("1.7.1",u"Seitenblicke","http://tvthek.orf.at/programs/1360-Seitenblicke",True),
            )
          ),
          TreeNode("1.8",u"Show","",False,
            (
              TreeNode("1.8.0",u"ARGE Talkshow","http://tvthek.orf.at/programs/1864371-ARGE-Talkshow",True),
              TreeNode("1.8.1",u"Frisch gekocht","http://tvthek.orf.at/programs/1375-Frisch-gekocht",True),
              TreeNode("1.8.2",u"Was gibt es Neues?","http://tvthek.orf.at/programs/1309553-Was-gibt-es-Neues-",True),
              TreeNode("1.8.3",u"Willkommen Österreich","http://tvthek.orf.at/programs/1309549-Willkommen-Oesterreich",True),
              TreeNode("1.8.4",u"Helden von Morgen - Die Show","http://tvthek.orf.at/programs/1679635-HvM---Die-Show",True),
              TreeNode("1.8.5",u"Helden von Morgen - Die Entscheidung","http://tvthek.orf.at/programs/1710513-HvM---Die-Entscheidung",True),
            )
          ),
          TreeNode("1.9",u"Volksgruppen","",False,
            (
              TreeNode("1.9.0",u"Heimat, fremde Heimat","http://tvthek.orf.at/programs/1357-Heimat--fremde-Heimat",True),
              TreeNode("1.9.1",u"Dobar dan Hrvati","http://tvthek.orf.at/programs/85526-Dobar-dan-Hrvati",True),
              TreeNode("1.9.2",u"Dober dan, Koroška","http://tvthek.orf.at/programs/85528-Dober-dan--Koroschka",True),
              TreeNode("1.9.3",u"Adj' Isten magyarok","http://tvthek.orf.at/programs/85519-Adj--Isten-magyarok",True),
              TreeNode("1.9.4",u"Servus Szia Zdravo Del tuha","http://tvthek.orf.at/programs/85512-Servus-Szia-Zdravo-Del-tuha",True),
              TreeNode("1.9.5",u"České & Slovenské Ozveny","http://tvthek.orf.at/programs/181719-Tscheske---Slovenske-Ozveny",True),
            )
          ),          
        )
      )
    );
      
    self.rootLink = "http://tvthek.orf.at"
    
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

