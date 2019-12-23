# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
# plugin.audio.podcatcher - A plugin to play Podcasts
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
import os, pickle;

class FeedState(object):
  def __init__(self, feed):
    self.feedUrl = feed.feedUrl;
    self.objectId = feed.objectId;
    self.title = feed.title;
    self.fetchInterval = feed.fetchInterval
    self.maxArticleAge = feed.maxArticleAge
    self.maxArticleNumber = feed.maxArticleNumber
    self.feedVersion = feed.feedVersion
    self.picture = feed.picture

class OpmlFolderState(object):
  def __init__(self, opmlFolder):
    self.title = opmlFolder.title;
    self.picture = opmlFolder.picture;
    self.elements = [];
    for subFolder in opmlFolder.elements:
      if(type(subFolder).__name__ == "OpmlFolder"):
        element = OpmlFolderState(subFolder);
      else:
        element = FeedState(subFolder);
      self.elements.append(element);

class OpmlArchiveFile(object):
  @classmethod
  def save(self, opmlFolder, filePath):
    archiveFile = open(filePath,"wb");
    state = OpmlFolderState(opmlFolder);
    pickle.dump(state, archiveFile);

  @classmethod
  def load(self,filePath):
    archiveFile = open(filePath,"rb");
    return pickle.load(archiveFile);

  @classmethod
  def updateNeeded(self, sourceFile, archiveFile):
    if(not os.path.exists(archiveFile)):
      return True;
    sourceChanged = os.stat(sourceFile)[8];
    archiveChanged = os.stat(archiveFile)[8];
    return sourceChanged>archiveChanged

class ArchiveFile(object):
  def __init__(self, itemId):
    self.feedItems = [];
    self.lastLoad = 0;
    self.archiveFile = os.path.join(self.archiveDir,itemId+".archive");

    if os.path.exists(self.archiveFile):
      filePointer = open(self.archiveFile, 'rb')
      unsortedObject = pickle.load(filePointer);
      self.feedItems = sorted(unsortedObject, key = lambda item:item.date, reverse=True);
      self.lastLoad = os.stat(self.archiveFile)[8];

  @classmethod
  def setArchivePath(cls, path):
    cls.archiveDir = path;

  def save(self):
    output = open(self.archiveFile, 'wb')
    pickle.dump(self.feedItems, output);
