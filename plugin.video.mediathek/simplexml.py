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
import sys,os
from xml.dom import minidom
from html import transformHtmlCodes
from mediathek import *

class XmlWriter(object):
  def __init__(self, path, link, xmlSettings):
    fileName = link.replace("http://","").replace("/","_");
    self.filePath = os.path.join(path, fileName);
    xmlImplementation = minidom.getDOMImplementation();
    self.xmlDocument = xmlImplementation.createDocument(None, "DirectoryListing", None)
    self.rootNode = self.xmlDocument.documentElement
    self.pastedObjects = [];
    self.pastedLinks = [];
    for node in xmlSettings.getElementsByTagName("setting"):
      id = node.getAttribute("id");
      if (id == "quality"):
	self.quality = int(node.getAttribute("value"));
      elif (id == "mode"):
	self.directAccess = node.getAttribute("value");
      elif (id == "preferedStreamType"):
	self.preferedStreamTyp = int(node.getAttribute("value"));
  
  def log(self, msg):
    if type(msg) not in (str, unicode):
      print(type(msg));
    else:
      try: 
	print(msg.encode('utf8'));
      except:
	print(msg);
  
  def createLinkNode(self, links):
    rootNode = self.xmlDocument.createElement('Link');
    for quality in links.iterkeys():
      link = links[quality];
      linkNode = self.xmlDocument.createElement(type(link).__name__);
      qualityAttr = self.xmlDocument.createAttribute("quality");
      linkNode.setAttributeNode(qualityAttr);
      linkNode.setAttribute("quality",unicode(quality));
      
      if(type(link).__name__ == "ComplexLink"):
	basePath = self.xmlDocument.createElement('BasePath');
	value = self.xmlDocument.createTextNode(link.basePath);
	basePath.appendChild(value);
	playPath = self.xmlDocument.createElement('PlayPath');
	value = self.xmlDocument.createTextNode(link.playPath);
	playPath.appendChild(value);
	
	linkNode.appendChild(basePath);
	linkNode.appendChild(playPath);
      else:
	value = self.xmlDocument.createTextNode(link.basePath);
	linkNode.appendChild(value);
	
      rootNode.appendChild(linkNode);
    return rootNode;
  
  def buildVideoLink(self, displayObject, mediathek):
    if(displayObject.subTitle == ""):
      title = transformHtmlCodes(displayObject.title);
    else:
      title = transformHtmlCodes(displayObject.title +" - "+ displayObject.subTitle);
      
    displayNode = self.xmlDocument.createElement('DisplayNode');
    titleNode = self.xmlDocument.createElement('Title');
    text = self.xmlDocument.createTextNode(title);
    titleNode.appendChild(text);
    
    pictureNode = self.xmlDocument.createElement('Picture');
    text = self.xmlDocument.createTextNode(displayObject.picture);
    pictureNode.appendChild(text);
    
    playableNode = self.xmlDocument.createElement('IsPlayable');
    if(displayObject.isPlayable):
      text = self.xmlDocument.createTextNode("True");
      linkNode = self.createLinkNode(displayObject.link);
    else:
      text = self.xmlDocument.createTextNode("False");
      linkNode = self.xmlDocument.createElement('Link');
      value = self.xmlDocument.createTextNode(displayObject.link);
      linkNode.appendChild(value);
      self.pastedLinks.append(displayObject);
      
    playableNode.appendChild(text);
    
    displayNode.appendChild(titleNode);
    displayNode.appendChild(pictureNode);
    displayNode.appendChild(playableNode);
    displayNode.appendChild(linkNode);
    
    self.rootNode.appendChild(displayNode);
    
  def buildMenuLink(self, menuObject, mediathek):
    #self.log(menuObject.name +" "+menuObject.path);
    menuNode = self.xmlDocument.createElement('MenuNode');
    
    titleNode = self.xmlDocument.createElement('Title');
    text = self.xmlDocument.createTextNode(menuObject.name);
    titleNode.appendChild(text);
    textNode = self.xmlDocument.createElement('Url');
    text = self.xmlDocument.createTextNode(menuObject.path);
    textNode.appendChild(text);
    
    menuNode.appendChild(titleNode);
    menuNode.appendChild(textNode);
    
    self.rootNode.appendChild(menuNode);
    self.pastedObjects.append(menuObject);
    
  def openMenuContext(self):
    pass;
    
  def closeMenuContext(self):
    content = self.xmlDocument.toxml(encoding='utf-8');
    xmlFile = open(self.filePath,"w");
    xmlFile.write(content);
    xmlFile.close();
    self.xmlDocument.unlink();
    
class XmlReader (object):
  def __init__(self, mediathekName, gui):
    self.mediathek = FakeMediathek(mediathekName);
    self.gui = gui;
    path = os.path.join(gui.getHomeDir(),"archives");
    self.basePath = os.path.join(path, self.mediathek.name());
    
  def buildPageMenu(self, link):
    filePath = os.path.join(self.basePath,link.replace("http://","").replace("/","_"));
    if not os.path.exists(filePath):
      self.gui.errorOK("CacheError","Local cache is incomplete");
    else:
      xmlDoc = minidom.parse(filePath);
      
      self.displayMenuNodes(xmlDoc);
      self.displayLinkNodes(xmlDoc);
    
  def buildMenu(self,path):
    filePath = os.path.join(self.basePath,path);
    if not os.path.exists(filePath):
      self.gui.errorOK("CacheError","Local cache is incomplete");
    else:
      xmlDoc = minidom.parse(filePath);
      self.gui.log(xmlDoc.toxml());
      
      self.displayMenuNodes(xmlDoc);
      self.displayLinkNodes(xmlDoc);
  
  def displayCategories(self):
    filePath = os.path.join(self.basePath,"index");
    if not os.path.exists(filePath):
      self.gui.errorOK("CacheError","Local cache is incomplete");
    else:
      xmlDoc = minidom.parse(filePath);
      self.gui.log(xmlDoc.toxml());
      self.displayMenuNodes(xmlDoc);
  
  def displayLinkNodes(self,rootNode):
    for menuNode in rootNode.getElementsByTagName('DisplayNode'):
      title = menuNode.getElementsByTagName('Title')[0].childNodes[0].data;
      picture = menuNode.getElementsByTagName('Picture')[0].childNodes[0].data;
      isPlayable = menuNode.getElementsByTagName('IsPlayable')[0].childNodes[0].data;
      
      if(isPlayable=="True"):
	link = self.readLinkNode(menuNode.getElementsByTagName('Link')[0]);
	displayObject = DisplayObject(title,"",picture,"",link,True);
      else:
	link = menuNode.getElementsByTagName('Link')[0].childNodes[0].data;
	displayObject = DisplayObject(title,"",picture,"",link,False);
      self.gui.buildVideoLink(displayObject, self.mediathek);
      
  def readLinkNode(self, rootNode):
    links = {};
    for linkNode in rootNode.childNodes:
      quality = int(linkNode.getAttribute("quality"));
      if(linkNode.tagName == "ComplexLink"):
	basePath = linkNode.getElementsByTagName('BasePath')[0].childNodes[0].data
	playPath = linkNode.getElementsByTagName('PlayPath')[0].childNodes[0].data
	link = ComplexLink(basePath,playPath);
      else:
	basePath = linkNode.childNodes[0].data
	link = SimpleLink(basePath);
      links[quality] = link;
    return links;
  def displayMenuNodes(self,rootNode):
    for menuNode in rootNode.getElementsByTagName('MenuNode'):
      title = menuNode.getElementsByTagName('Title')[0].childNodes[0].data;
      path = menuNode.getElementsByTagName('Url')[0].childNodes[0].data;
      
      menuObject = TreeNode(path,title,"",False);
      self.gui.buildMenuLink(menuObject, self.mediathek);
    
class FakeMediathek:
  def __init__(self, name):
    self.__name = name;
  def name(self):
    return self.__name;