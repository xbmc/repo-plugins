# -*- coding: utf-8 -*-
#-------------LicenseHeader--------------
# plugin.video.Mediathek - Gives access to most video-platforms from German public service broadcasters
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
# -*- coding: utf-8 -*-
import urllib, sys, os, threading, time;
from simplexml import XmlWriter
from mediathek.factory import MediathekFactory
from xml.dom import minidom;

try:
  __ThreadCount__ = int(sys.argv[2]);
except:
  __ThreadCount__ = 1;
  
__MultiThreading__ = __ThreadCount__ > 1;
def fetchData(mediathek, archivePath, link = None):
  if(link == None):
    xmlWriter = XmlWriter(archivePath,"index",configXml);
    xmlWriter.log("IndexPage");
    mediathekInstance = mediathek(xmlWriter);
    mediathekInstance.displayCategories();
    xmlWriter.closeMenuContext();
    for displayObject in xmlWriter.pastedObjects:
      if(__MultiThreading__ and threading.activeCount() < __ThreadCount__):
	thread = threading.Thread(None, fetchData, None, (mediathek, archivePath, displayObject.path));
	thread.start();
      else:
	fetchData(mediathek, archivePath, displayObject.path);
      
  else:
    xmlWriter = XmlWriter(archivePath, link, configXml);
    mediathekInstance = mediathek(xmlWriter);
    xmlWriter.log("Link: "+link);
    if(link.startswith("http://")):
      mediathekInstance.buildPageMenu(link);
    else:
      mediathekInstance.buildMenu(link.split('.'))
    
    for displayObject in xmlWriter.pastedObjects:
      if(__MultiThreading__ and threading.activeCount() < __ThreadCount__):
	thread = threading.Thread(None, fetchData,None,(mediathek, archivePath, displayObject.path));
	thread.start();
      else:
	fetchData(mediathek, archivePath, displayObject.path);
    
    for linkObject in xmlWriter.pastedLinks:
      if(__MultiThreading__ and threading.activeCount() < __ThreadCount__):
	thread = threading.Thread(None, fetchData, None, (mediathek, archivePath, linkObject.link));
	thread.start();
      else:
	fetchData(mediathek, archivePath, linkObject.link);
      
    xmlWriter.closeMenuContext();
baseDirectory = sys.argv[1]

configPath = os.path.join(baseDirectory, "settings.xml");
baseDirectory=os.path.join(baseDirectory, "archives");

print configPath;
if(os.path.exists(configPath)):
  configXml = minidom.parse(configPath);
else:
  print "cannot find settings.xml";
  sys.exit(-1);
  
factory = MediathekFactory();

for mediathek in factory.avaibleMediathekes.itervalues():
  if(mediathek.name() is not "ARTE"):
    continue;
  archiveDirectory = os.path.join(baseDirectory, mediathek.name())
  if not os.path.exists(archiveDirectory):
    os.mkdir(archiveDirectory);
  if(__MultiThreading__):
    thread = threading.Thread(None, fetchData,None, (mediathek, archiveDirectory));
    thread.start();
  else:
    fetchData(mediathek,archiveDirectory);