# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
# plugin.video.Mediathek - Gives access to most video-platforms from German public service broadcasters
# Copyright (C) 2010  MaxMustermann [http://forum.xbmc.org/member.php?u=53843]
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
from xml.dom import minidom;
regex_dateString = re.compile("\\d{4}-\\d{2}-\\d{2}");
 
URL_MAIN = 'http://www.br-online.de'
URL_CENTAURI = 'http://www.br-online.de/br-alpha/alpha-centauri/alpha-centauri-harald-lesch-videothek-ID1207836664586.xml'
URL_DARWIN = 'http://www.br-online.de/br-alpha/charles-darwin/charles-darwin-evolution-videothek-ID1256655423519.xml'
URL_DENKER = 'http://www.br-online.de/br-alpha/denker-des-abendlandes/denker-lesch-vossenkuhl-ID1221136938708.xml'
URL_GEISTundGEHIRN = 'http://www.br-online.de/br-alpha/geist-und-gehirn/index.xml'
URL_KANT = 'http://www.br-online.de/br-alpha/kant-fuer-anfaenger/'
URL_KANT1 = 'http://www.br-online.de/br-alpha/kant-fuer-anfaenger/kant-reine-vernunft-philosophie-ID661188595418.xml'
URL_KANT2 = 'http://www.br-online.de/br-alpha/kant-fuer-anfaenger/kant-kategorischer-imperativ-philosophie-ID661188595399.xml'
URL_MATHE = 'http://www.br-online.de/br-alpha/mathematik-zum-anfassen/index.xml'
URL_MYTHEN = 'http://www.br-online.de/br-alpha/mythen/index.xml'
URL_PHYSIK_EINSTEIN = 'http://www.br-online.de/br-alpha/die-physik-albert-einsteins/die-physik-albert-einsteins-lesch-einstein-ID1221487435226.xml'
URL_ELEMENTE = 'http://www.br-online.de/br-alpha/die-4-elemente/die-4-elemente-elemente-harald-lesch-ID1225290580446.xml'
 
 
class BRAlphaMediathek(Mediathek):
  def __init__(self, simpleXbmcGui):
    self.gui = simpleXbmcGui;
    if (self.gui.preferedStreamTyp == 1):  
      self.baseType = "flash"
    else:
      self.baseType ="wmv";
      
    self.rootLink = URL_MAIN
    self.menuTree = (
                      TreeNode("0","Alpha-Centauri",URL_CENTAURI,True),
                      TreeNode("1","Charles Darwin",URL_DARWIN,True),
                      TreeNode("2","Denker des Abendlandes",URL_DENKER,True),
                      TreeNode("3","Geist und Gehirn",URL_GEISTundGEHIRN,True),
                      TreeNode("4",u"Kant fuer Anfaenger - Die Kritik der reinen Vernunft",URL_KANT1,True),
                      TreeNode("5","Kant fuer Anfaenger - Der kategorische Imperativ",URL_KANT2,True),
                      TreeNode("6","Mathematik zum Anfassen",URL_MATHE,True),
                      TreeNode("7","Mythen",URL_MYTHEN,True),
                      TreeNode("8","Die Physik Albert Einsteins",URL_PHYSIK_EINSTEIN,True),                         
                      TreeNode("9","Die 4 Elemente",URL_ELEMENTE,True),
                    )
                    
 
                                                  
    self._regex_extractVideothekItem = re.compile('<h3 class="teaserHead">.*?<a href="[^"]+".*?<img src="[^"]+".*?<span class="versteckt">.*?</span>', re.DOTALL);
    self._regex_extractVideothekItemURL = re.compile('<h3 class="teaserHead">.*?<a href="([^"]+)".*?<img src="[^"]+".*?<span class="versteckt">.*?</span>', re.DOTALL);
    self._regex_extractVideothekItemIMAGE = re.compile('<h3 class="teaserHead">.*?<a href="[^"]+".*?<img src="([^"]+)".*?<span class="versteckt">.*?</span>', re.DOTALL);
    self._regex_extractVideothekItemTITLE = re.compile('<h3 class="teaserHead">.*?<a href="[^"]+".*?<img src="[^"]+".*?<span class="versteckt">(.*?)</span>', re.DOTALL);
    
    self._regex_extractMoviePage = re.compile('<h3 class="teaserHead">.*?<a href="([^"]+)".*?<span class="versteckt">(.*?)</span>', re.DOTALL);
    self._regex_extractMovieLinkPage = re.compile('<h3 class="linkPkt">.*?<a href="([^"]+)".*?<span class="versteckt">(.*?)</span>', re.DOTALL);
    
    self.replace_html = re.compile("<.*?>");
    self.replace_tag = re.compile("(<meta name=\".*?\" content=\"|<link rel=\"image_src\" href=\"|\" />)");
    
    self._regex_wmv_low = re.compile("player.avaible_url\['microsoftmedia'\]\['1'\] = \"([^\"]+)\"",re.DOTALL);
    self._regex_wmv_high = re.compile("player.avaible_url\['microsoftmedia'\]\['2'\] = \"(.*?)\"",re.DOTALL);
    self._regex_flash_low = re.compile("player.avaible_url\['flashmedia'\]\['1'\] = \"(.*?)\"",re.DOTALL);
    self._regex_flash_high = re.compile("player.avaible_url\['flashmedia'\]\['2'\] = \"(.*?)\"",re.DOTALL);
    
  @classmethod
  def name(self):
    return "BR-Alpha";
    
  def isSearchable(self):
    return False;
    
  def searchVideo(self, searchText):
    pass;   
    
  def buildPageMenu(self, link, initCount, subLink = False):
    self.gui.log(link);
    mainPage = self.loadPage(link);
    if (link == URL_CENTAURI):
        self.showVideothek(mainPage)
    elif (link == URL_KANT1 or link == URL_KANT2):
        self.showKant(mainPage)
    elif (link == URL_GEISTundGEHIRN or link == URL_MATHE or link == URL_MYTHEN):
        self.showVideothekSeasons(mainPage)
    else:
        self.showMovies(mainPage)
   
  def showVideothekSeasons(self, htmlPage):
    sPattern = re.compile('<ul class="ebene1">(.*?)</ul>', re.DOTALL)
    aResult = sPattern.findall(htmlPage)
    if aResult:
        htmlPage = aResult[0]
        sPattern = re.compile('<li><a href="([^"]+)">(.*?)</a>', re.DOTALL)
        aResult = sPattern.findall(htmlPage)
        if aResult:
            for aEntry in aResult:
                title = aEntry[1]
                if title != 'Videothek':
                    self.gui.buildVideoLink(DisplayObject(title,"","","",self.rootLink + aEntry[0],False),self,0);
 
  
  def showVideothek(self, htmlPage):
    pageLinks = list(self._regex_extractVideothekItem.finditer(htmlPage));
    for element in pageLinks:
      element = element.group()
      pictureLink = self.rootLink + self._regex_extractVideothekItemIMAGE.findall(element)[0];
      videoPageLink = self.rootLink + self._regex_extractVideothekItemURL.findall(element)[0];
      titles = [];
      for title in self._regex_extractVideothekItemTITLE.findall(element):
        title = unicode(title,'ISO-8859-1');
        title = self.replace_html.sub("", title); #outerhtml wegschneiden
        title = title.replace("&nbsp;", ""); #sinnlose "steuerzeichen wegschneiden"
        titles.append(title);
      while len(titles) < 2:
        titles.append("");      
      self.gui.buildVideoLink(DisplayObject(titles[0],titles[1],pictureLink,"",videoPageLink,False),self,0);
 
      
  def showKant(self, htmlPage):
    
    sPattern = re.compile('<ul class="visualFormat">(.*?)</ul>', re.DOTALL)
    aResult = sPattern.findall(htmlPage)
    if aResult:
        htmlPage = aResult[0]
        sPattern = re.compile('<li><strong>([^<]+)</strong>.*?<a.*?href="([^"]+)"\s*>([^<]+)</a></li>', re.DOTALL)
        aResult = list(sPattern.findall(htmlPage))
        if aResult:
            for aEntry in aResult:                
                title = aEntry[0] + " " + aEntry[2]
                
                url = aEntry[1]
                if not url.startswith('http'):
                    if url.startswith('/'):
                        url = URL_MAIN + url
                    else:
                        url = URL_KANT + url
 
                newPage = self.loadPage(url)
 
                newPattern = re.compile('class="avKastenHead">.*?<a href="([^"]+)"', re.DOTALL)
                newResult = newPattern.findall(newPage)
                if newResult:
                    url = newResult[0]
                    if not url.startswith('http'):
                        if url.startswith('/'):
                            url = URL_MAIN + url
                        else:
                            url = URL_KANT + url
                    movieLinks = self.getMovieLink(url);
                    self.gui.buildVideoLink(DisplayObject(title,"","","",movieLinks,True),self,len(aResult));
                          
                
  def showMovies(self, htmlPage):
    
    moviePages = list(self._regex_extractMoviePage.findall(htmlPage))
    links = list(self._regex_extractMovieLinkPage.findall(htmlPage))
    itemCount = len(moviePages)+len(links)
    
    for element in moviePages:
      videoPageLink = self.rootLink + element[0];
      title = unicode(element[1],'ISO-8859-1').strip('\'').strip();
      videoLinks = self.getMovieLink(videoPageLink)
      self.gui.buildVideoLink(DisplayObject(title,"","","",videoLinks,True),self,itemCount);
    
    for element in links:
      videoPageLink = self.rootLink + element[0];
      title = unicode(element[1],'ISO-8859-1').strip('\'').strip();
      videoLinks = self.getMovieLink(videoPageLink)
      self.gui.buildVideoLink(DisplayObject(title,"","","",videoLinks,True),self,itemCount);
 
  def getMovieTitle(self, sHtmlContent):
    sPattern = re.compile('<div class="videoText"><p><strong>(.*?)<span>', re.DOTALL)
    aResult = sPattern.findall(sHtmlContent)
    title = unicode(aResult[0], 'UTF-8')
    return title
      
  def getMovieLink(self, sourceUrl):
    links = {};
    htmlPage = self.loadPage(sourceUrl);
    if(self.baseType=="wmv"):
      self.buildLink(htmlPage, self._regex_wmv_low, links,0);
      self.buildLink(htmlPage, self._regex_wmv_high, links,1);
    else:
      self.buildLink(htmlPage, self._regex_flash_low, links,0);
      self.buildLink(htmlPage, self._regex_flash_high, links,1);
    return links
 
  def buildLink(self, htmlPage, sPattern, links, quality):
    aResult = sPattern.findall(htmlPage)
    if aResult:
        for aEntry in aResult:
            links[quality] = SimpleLink(aEntry, 0);
