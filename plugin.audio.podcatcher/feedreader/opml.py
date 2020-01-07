# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
# plugin.audio.PodCatcher - A plugin to play Podcasts
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

import os;
from xml.dom import minidom;
from xml.dom import Node;
from feedfactory import FeedFactory;
from html import transformHtmlCodes;
from archivefile import OpmlArchiveFile;

class OpmlFolder(object):
  def loadFromNode(self, rootNode, gui):
    self.gui = gui;
    self.elements = [];
    self.title = transformHtmlCodes(rootNode.getAttribute('text'));
    self.picture = rootNode.getAttribute("image");

    for node in rootNode.childNodes:
      if node.hasChildNodes() and node.firstChild.tagName == "outline":
        element = OpmlFolder();
        element.loadFromNode(node, self.gui);
      else:
        element = FeedFactory.getFeedFromNode(node, self.gui)
      self.elements.append(element);

  def loadFromState(self, stateObject, gui):
    self.gui = gui;
    self.elements = [];
    self.title = stateObject.title;

    self.picture = stateObject.picture;

    for stateElement in stateObject.elements:
      if(type(stateElement).__name__ == "OpmlFolderState"):
        element = OpmlFolder()
        element.loadFromState(stateElement,self.gui);
      else:
        element = FeedFactory.getFeedFromState(stateElement, self.gui)
      self.elements.append(element);

  def displayMenu(self, path):
    if len(path) > 0:
      index = int(path.pop(0));
      element = self.elements[index];
      element.displayMenu(path);
    else:
      for element in self.elements:
        self.gui.buildMenuEntry(element,len(self.elements));

  def play(self, path):
    if len(path) > 0:
      index = int(path.pop(0));
      element = self.elements[index];
      element.play(path);
    else:
      self.gui.play(self);
      self.markRead();

  def markRead(self, path = None):
    path = path or [];
    if len(path) > 0:
      index = int(path.pop(0));
      self.gui.log("MarkRead: %d"%index);
      element = self.elements[index];
      element.markRead(path);
    else:
      self.gui.log("Mark Elements Read");
      for element in self.elements:
        element.markRead();

  def reload(self, path = None):
    path = path or [];
    if len(path) > 0:
      index = int(path.pop(0));
      self.gui.log("Reload: %d"%index);
      element = self.elements[index];
      element.reload(path);
    else:
      for element in self.elements:
        element.reload();

  def load(self):
    for element in self.elements:
      if(type(element).__name__ == "OpmlFolder"):
        element.load();
      else:
        element.loadFeed();

  def hasUnreadItems(self):
    for element in self.elements:
      if(element.hasUnreadItems()):
        return True;
    return False;

  def getAllUnreadItems(self, items):
    for element in self.elements:
      element.getAllItems(items);

class OpmlFile:
  def __init__(self, opmlFile, archivePath, gui):
    self.gui = gui;
    self.opmlFolder = OpmlFolder();
    archiveFile = os.path.join(archivePath,"opml.archive");
    if(OpmlArchiveFile.updateNeeded(opmlFile, archiveFile)):
      self.xmlDoc = minidom.parse(opmlFile)
      self.cleanupNodes(self.xmlDoc.documentElement);
      self.xmlDoc.documentElement.normalize();

      for bodyNode in  self.xmlDoc.getElementsByTagName('body'):
        self.opmlFolder.loadFromNode(bodyNode, self.gui )

      OpmlArchiveFile.save(self.opmlFolder, archiveFile);
    else:
      state = OpmlArchiveFile.load(archiveFile);
      self.opmlFolder.loadFromState(state,self.gui);

  def cleanupNodes(self, rootNode):
    for node in rootNode.childNodes:
      if node.nodeType == Node.TEXT_NODE:
        node.data = node.data.strip()
      else:
        self.cleanupNodes(node);

  def displayMenu(self, path):
    self.opmlFolder.displayMenu(path);

  def getItem(self, path):
    return self.opmlFolder.getItem(path);

  def play(self, path):
    self.opmlFolder.play(path);

  def markRead(self, path):
    self.opmlFolder.markRead(path);

  def reload(self, path):
    self.opmlFolder.reload(path);

  def load(self):
    self.opmlFolder.load();
