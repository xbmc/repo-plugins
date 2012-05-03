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
import urllib, re, time;
from ui import *;

class GamestarWeb(object):
  def __init__(self, gui):
    self.gui = gui;
    self.rootLink = "http://www.gamestar.de/";
    self.shortName = "GS";

    ##setup regular expressions
    self.imageRegex = "<img src=\".*\" width=\"\\d*\" height=\"\\d*\" alt=\".*\" title=\".*\" />"
    self.linkRegex =  "/index.cfm\\?pid=\\d*?(&amp;|&)pk=\\d*?"
    self.simpleLinkRegex = "<a href=\""+self.linkRegex+"\" .+?>.+?</a>";
    self.hrefRegex = "<a.*? href=\""+self.linkRegex+"\">"
    self.headerRegex ="<strong>.+</strong>\\s*.*\\s*</a>"
    self.titleRegex = "<a.*?>(.*?)</a>"

    self._regEx_extractVideoThumbnail = re.compile("<div class=\"videoPreview\">\\s*"+self.hrefRegex+"\\s*"+self.imageRegex+"\\s*</a>\\s*<span>\\s*"+self.hrefRegex+"\\s*"+self.headerRegex);
    self._regEx_extractTargetLink = re.compile(self.linkRegex);
    self._regEx_extractVideoID = re.compile("pk=\\d*");
    self._regEx_extractVideoLink = re.compile("http.*(mp4|flv)");
    self._regEx_extractPictureLink = re.compile("http://.*.jpg");
    self._regEx_extractHeader = re.compile(self.headerRegex);
    self._regEx_extractSimpleLink = re.compile(self.simpleLinkRegex);
    self._regEx_extractTitle = re.compile(self.titleRegex);
    ##end setup
    
    linkRoot = self.rootLink+"index.cfm?pid=1589&ci=";
    imageRoot = "http://images.gamestar.de/images/idgwpgsgp/bdb/";    

    ##setup categories
    self.categories = {
      30001:GalleryObject(linkRoot+"latest", imageRoot+"/2018270/b144x81.jpg"),
      30002:GalleryObject(linkRoot+"17",imageRoot+"2018272/b144x81.jpg"),
      30003:GalleryObject(linkRoot+"18",imageRoot+"bdb/2018269/b144x81.jpg"),
      30004:GalleryObject(linkRoot+"20",imageRoot+"2018270/b144x81.jpg"),
      30005:GalleryObject(linkRoot+"9",imageRoot+"bdb/2016676/b144x81.jpg"),
      30006:GalleryObject(linkRoot+"22",imageRoot+"2016431/b144x81.jpg"),
      30007:GalleryObject(linkRoot+"15",imageRoot+"2018271/b144x81.jpg"),
      30008:GalleryObject(linkRoot+"37",imageRoot+"2121485/b144x81.jpg"),
      30009:GalleryObject(linkRoot+"32",imageRoot+"2018270/b144x81.jpg"),
      30010:GalleryObject(linkRoot+"2",imageRoot+"2018274/b144x81.jpg"),
      }
    ##endregion
    
  def getCategories(self):
    categories={};
    for key in self.categories.keys():
      categories[key]=self.categories[key].pictureLink;
    return categories;
  
  def getVideoLinkObjects(self, categorie):
    videoObjects = [];
    if categorie in self.categories:
      categorie = self.categories[categorie];
      self.gui.log(categorie.url);
      rootDocument = self.loadPage(categorie.url);
      for videoThumbnail in self._regEx_extractVideoThumbnail.finditer(rootDocument):       
        videoThumbnail = videoThumbnail.group()
        videoID = self._regEx_extractVideoID.search(videoThumbnail).group().replace("pk=","");
        
        header = self._regEx_extractHeader.search(videoThumbnail).group();
        header = re.sub("(<strong>)|(</strong>)|(</a>)", "", header);
        header = re.sub("\\s+", " ", header);
        
        try:
          videoObjects.append(self.loadVideoPage(header, videoID));
        except:
          pass;
    return videoObjects;


  def loadVideoPage(self, title, videoID):
    self.gui.log(self.rootLink+"/emb/getVideoData.cfm?vid="+videoID);
    configDoc = self.loadPage(self.rootLink+"/emb/getVideoData.cfm?vid="+videoID);
    videoLink = unicode(self._regEx_extractVideoLink.search(configDoc).group());
    videoLink = self.replaceXmlEntities(videoLink);
    thumbnailLink =unicode(self._regEx_extractPictureLink.search(configDoc).group());
    
    return VideoObject(title, videoLink, thumbnailLink, self.shortName);
  
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
