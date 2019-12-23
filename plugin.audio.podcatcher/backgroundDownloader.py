# -*- coding: utf-8 -*-
import sys,os
from feedreader.opml import OpmlFile
from feedreader.archivefile import ArchiveFile
#!This script is called by batch - not by xbmc!#


DIR_HOME = sys.argv[1];

DIR_ARCHIVES = os.path.join(DIR_HOME, 'archives')
if not os.path.exists(DIR_ARCHIVES):
  os.mkdir(DIR_ARCHIVES);
ArchiveFile.setArchivePath(DIR_ARCHIVES);

class ConsoleGui(object):
  @staticmethod
  def log(message):
    print message;
try:
  PATH_FILE_OPML = sys.argv[2];
except IndexError:
  PATH_FILE_OPML = "";

if (PATH_FILE_OPML == ""):
  PATH_FILE_OPML = os.path.join(DIR_HOME,"opml.xml");

opmlFile = OpmlFile(PATH_FILE_OPML, DIR_HOME, ConsoleGui());
opmlFile.load();
