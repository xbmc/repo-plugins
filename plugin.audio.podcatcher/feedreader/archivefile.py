# -*- coding: utf-8 -*-
import xbmcaddon, os, pickle;
from xml.dom import minidom


class ArchiveFile(object):
  def __init__(self, itemId):
    global __archiveDir__;
    
    self.feedItems = [];
    self.lastLoad = 0;
    
    self.archiveFile = os.path.join(__archiveDir__,itemId);
    
    if os.path.exists(self.archiveFile):
      input = open(self.archiveFile, 'r')
      unsortedObject = pickle.load(input);
      self.feedItems = sorted(unsortedObject, key = lambda item:item.date, reverse=True);
      self.lastLoad = stats = os.stat(self.archiveFile)[8];
  
  @classmethod
  def setArchivePath(self, path):
    global __archiveDir__;
    __archiveDir__ = path;
  
  def save(self):
    output = open(self.archiveFile, 'w')
    pickle.dump(self.feedItems, output);