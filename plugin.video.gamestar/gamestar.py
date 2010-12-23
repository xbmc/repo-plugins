# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
# plugin.video.gamestar - Downloads/view videos from gamestar.de
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
import urllib, re
from ui import *;

class GamestarWeb(object):
  def __init__(self, gui):
    self.gui = gui;
    self.rootLinkGS = "http://www.gamestar.de";
    self.rootLinkGP = "http://www.gamepro.de";
    
    ##setup regular expressions
    self.imageRegex = "<img src=\".*\" width=\"\\d*\" height=\"\\d*\" alt=\".*\" title=\".*\" />"
    self.linkRegex =  "/index.cfm\\?pid=\\d*?(&amp;|&)pk=\\d*?"
    self.simpleLinkRegex = "<a href=\""+self.linkRegex+"\" .+?>.+?</a>";
    self.hrefRegex = "<a href=\""+self.linkRegex+"\">"
    self.headerRegex ="<strong>.+</strong>\\s*.*\\s*</a>"
    self.titleRegex = "<a.*?>(.*?)</a>"
    self._regEx_extractVideoThumbnail = re.compile("<div class=\"videoPreview\">\\s*"+self.hrefRegex+"\\s*"+self.imageRegex+"\\s*</a>\\s*<span>\\s*"+self.hrefRegex+"\\s*"+self.headerRegex)
    self._regEx_extractTargetLink = re.compile(self.linkRegex);
    self._regEx_extractVideoID = re.compile("pk=\\d*");
    self._regEx_extractVideoLink = re.compile("http.*(mp4|flv)");
    self._regEx_extractPictureLink = re.compile("http://.*.jpg");
    self._regEx_extractHeader = re.compile(self.headerRegex);
    self._regEx_extractSimpleLink = re.compile(self.simpleLinkRegex);
    self._regEx_extractTitle = re.compile(self.titleRegex);
    ##end setup
    
    ##setup categories
    self.categories = (
      GalleryObject(0,30001,"http://www.gamestar.de/index.cfm?pid=1589&ci=latest","http://images.gamestar.de/images/idgwpgsgp/bdb/2018270/b144x81.jpg", self.rootLinkGS),
      GalleryObject(1,30002,"http://www.gamestar.de/index.cfm?pid=1589&ci=17","http://images.gamestar.de/images/idgwpgsgp/bdb/2018272/b144x81.jpg", self.rootLinkGS),
      GalleryObject(2,30003,"http://www.gamestar.de/index.cfm?pid=1589&ci=18","http://images.gamestar.de/images/idgwpgsgp/bdb/2018269/b144x81.jpg", self.rootLinkGS),
      GalleryObject(3,30004,"http://www.gamestar.de/index.cfm?pid=1589&ci=20","http://images.gamestar.de/images/idgwpgsgp/bdb/2018270/b144x81.jpg", self.rootLinkGS),
      GalleryObject(4,30005,"http://www.gamestar.de/index.cfm?pid=1589&ci=19","http://images.gamestar.de/images/idgwpgsgp/bdb/2016676/b144x81.jpg", self.rootLinkGS),
      GalleryObject(5,30006,"http://www.gamestar.de/index.cfm?pid=1589&ci=22","http://images.gamestar.de/images/idgwpgsgp/bdb/2016431/b144x81.jpg", self.rootLinkGS),
      GalleryObject(6,30007,"http://www.gamestar.de/index.cfm?pid=1589&ci=15","http://images.gamestar.de/images/idgwpgsgp/bdb/2018271/b144x81.jpg", self.rootLinkGS),
      GalleryObject(7,30008,"http://www.gamestar.de/index.cfm?pid=1589&ci=37","http://images.idgentertainment.de/images/idgwpgsgp/bdb/2121485/b144x81.jpg", self.rootLinkGS),
      GalleryObject(8,30009,"http://www.gamestar.de/index.cfm?pid=1589&ci=32","http://images.gamestar.de/images/idgwpgsgp/bdb/2018270/b144x81.jpg", self.rootLinkGS),
      GalleryObject(9,30010,"http://www.gamestar.de/index.cfm?pid=1589&ci=2","http://images.gamestar.de/images/idgwpgsgp/bdb/2018274/b144x81.jpg", self.rootLinkGS),
      GalleryObject(10,30011,"http://www.gamestar.de/index.cfm?pid=1589&ci=1","http://images.gamestar.de/images/idgwpgsgp/bdb/2016821/b144x81.jpg", self.rootLinkGS),
      GalleryObject(11,30012,"http://www.gamepro.de/videos/","", self.rootLinkGP)
      )
    ##endregion
    
  def buildCategoryMenu(self):
    for categorie in self.categories:
      self.gui.buildCategoryLink(categorie);
  
  def builCategoryMenu(self, categorie, forcePrecaching):
    rootDocument = self.loadPage(categorie.url)
    if(len(self._regEx_extractVideoThumbnail.findall(rootDocument)) > 0):
      for videoThumbnail in self._regEx_extractVideoThumbnail.finditer(rootDocument):
        try:
          videoThumbnail = videoThumbnail.group()
          videoID = self._regEx_extractVideoID.search(videoThumbnail).group().replace("pk=","");
          header = self._regEx_extractHeader.search(videoThumbnail).group();
          header = re.sub("(<strong>)|(</strong>)|(</a>)", "", header);
          header = re.sub("\\s+", " ", header);
          
          self.loadVideoPage(categorie.rootLink, header, videoID, forcePrecaching);
        except:
          pass;
    else:
      for simpleLink in self._regEx_extractSimpleLink.finditer(rootDocument):
        simpleLink = unicode(simpleLink.group().decode('UTF-8'));
        self.gui.log(simpleLink);
        videoID = self._regEx_extractVideoID.search(simpleLink).group().replace("pk=","");
        title = self._regEx_extractTitle.findall(simpleLink)[0];
        title = self.transformHtmlCodes(title);
        self.loadVideoPage(categorie.rootLink, title, videoID, forcePrecaching);


  def loadVideoPage(self,rootLink,title,videoID,forcePrecaching):
    self.gui.log(rootLink+"/emb/getVideoData.cfm?vid="+videoID);
    configDoc = self.loadPage(rootLink+"/emb/getVideoData.cfm?vid="+videoID);
    videoLink = unicode(self._regEx_extractVideoLink.search(configDoc).group());
    videoLink = self.replaceXmlEntities(videoLink);
    thumbnailLink =unicode(self._regEx_extractPictureLink.search(configDoc).group());
    
    self.gui.buildVideoLink(VideoObject(title,videoLink,thumbnailLink),forcePrecaching);
  
  def replaceXmlEntities(self, link):
    entities = (
        ("%3A",":"),("%2F","/"),("%3D","="),("%3F","?"),("%26","&")
      );
    for entity in entities:
       link = link.replace(entity[0],entity[1]);
    return link;
  def transformHtmlCodes(self,string):
    replacements = (
      (u'Ä', u'&Auml;'),
      (u'Ü', u'&Uuml;'),
      (u'Ö', u'&Ouml;'),
      (u'ä', u'&auml;'),
      (u'ü', u'&uuml;'),
      (u'ö', u'&ouml;'),
      (u'ß', u'&szlig;'),
      (u'\"',u'&#034;'),
      (u'\"',u'&quot;'),
      (u'\'',u'&#039;'),
      (u'&', u'&amp;'),
      (u' ', u'&nbsp;')
    )
    for replacement in replacements:
      string = string.replace(replacement[1],replacement[0]);
    return string;
  def loadPage(self,url):
    try:
      safe_url = url.replace( " ", "%20" ).replace("&amp;","&")
      sock = urllib.urlopen( safe_url )
      doc = sock.read()
      if doc:
        return doc
      else:
        return ''
    except:
      return ''
