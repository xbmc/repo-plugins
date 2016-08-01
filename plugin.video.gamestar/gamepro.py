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
import urllib, re, time,traceback;
from ui import *;

class GameproWeb(object):
  def __init__(self, gui):
    self.gui = gui;
    self.rootLink = "http://www.gamepro.de/";
    self.shortName = "GP";

    ##setup regular expressions
    self._regEx_extractVideoID = re.compile("/videos/.*,(\\d*)\\.html");
    self._regEx_extractVideoLink = re.compile("http.*(mp4|flv)");
    self._regEx_extractPictureLink = re.compile("(http://|//).*.jpg");
    self._regEx_extractTitle = re.compile("<videoname>\\d*?\\.(.*)\\.embed</videoname>");
    ##end setup
    
    linkRoot = self.rootLink+"videos/video-kanaele/";
    imageRoot = "http://images.gamestar.de/images/idgwpgsgp/bdb/";    

    ##setup categories
    self.categories = {
      30001:GalleryObject(linkRoot+"latest/", imageRoot+"/2018270/b144x81.jpg"),
      30002:GalleryObject(linkRoot+"tests,17/",imageRoot+"2018272/b144x81.jpg"),
      30003:GalleryObject(linkRoot+"previews,18/",imageRoot+"bdb/2018269/b144x81.jpg"),
      30004:GalleryObject(linkRoot+"specials,20/",imageRoot+"2018270/b144x81.jpg"),
      30011:GalleryObject(linkRoot+"trailer,3","http://images.cgames.de/images/idgwpgsgp/bdb/2017073/b144x81.jpg"),
      30009:GalleryObject(linkRoot+"candyland,102/","http://images.cgames.de/images/idgwpgsgp/bdb/2557236/b144x81.jpg"),
      30010:GalleryObject(linkRoot+"boxenstop,2",imageRoot+"2018274/b144x81.jpg"),
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
      
      videoIds = set();
      for match in self._regEx_extractVideoID.finditer(rootDocument):       
        videoId = match.group(1);
        if(videoId not in videoIds):
          
          videoIds.add(videoId);
          
      for videoId in sorted(videoIds, reverse=True):        
        try:
          videoObjects.append(self.loadVideoPage(videoId));
        except:
          self.gui.log("something goes wrong while processing "+videoId);
          self.gui.log("Exception: ");
          traceback.print_exc();
          self.gui.log("Stacktrace: ");
          traceback.print_stack();
    return videoObjects;


  def loadVideoPage(self, videoID):
    self.gui.log(self.rootLink+"/emb/getVideoData.cfm?vid="+videoID);
    configDoc = self.loadPage(self.rootLink+"/emb/getVideoData.cfm?vid="+videoID).decode('utf-8');
    videoLink = self._regEx_extractVideoLink.search(configDoc).group();
    videoLink = self.replaceXmlEntities(videoLink);
    thumbnailLink = self._regEx_extractPictureLink.search(configDoc).group();
    title = self._regEx_extractTitle.search(configDoc).group(1);
    title = self.transformHtmlCodes(title);
    
    if(not thumbnailLink.startswith('http://')):
      thumbnailLink = thumbnailLink.replace("//",'http://');
    thumbnailLink = thumbnailLink;
    
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
