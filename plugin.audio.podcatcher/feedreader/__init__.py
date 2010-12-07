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
import time,urllib,re;
from archivefile import ArchiveFile
regex_dateString = re.compile("\\d{2} ((\\w{3})|(\\d{2})) \\d{4}");
month_replacements = {
    "Jan":"01",
    "Feb":"02",
    "Mar":"03",
    "Apr":"04",
    "May":"05",
    "Jun":"06",
    "Jul":"07",
    "Aug":"08",
    "Sep":"09",
    "Oct":"10",
    "Nov":"11",
    "Dec":"12",
    
  };

class FeedItem(object):
  def __init__(self):
    self.title = None;
    self.subTitle = None;
    self.link = None;
    self.description = None;
    self.date = None;
    self.duration = None;
    self.author = None;
    self.picture = None;
    self.readed = None;
    self.guid = None;
    self.size = None;
    
class Feed(object):
  def loadOpmlNode(self,opmlNode):
    self.objectId = opmlNode.getAttribute("id");
    self.archiveFile=ArchiveFile(self.objectId);
    
    self.feedItems = self.archiveFile.feedItems;
    for feedItem in self.feedItems:
      self.gui.log(feedItem.title);
    self.lastLoad = self.archiveFile.lastLoad;
    
    self.feedUrl = opmlNode.getAttribute("xmlUrl");
    self.fetchInterval = self.parseFetchInterval(opmlNode.getAttribute("fetchInterval"));
    self.title = opmlNode.getAttribute("text");
    self.maxArticleAge = int(opmlNode.getAttribute("maxArticleAge"));
    self.maxArticleNumber = int(opmlNode.getAttribute("maxArticleNumber"));
    
    
  
  def saveChanges(self):
    self.archiveFile.save();
  
  def hasUnreadItems(self):
    self.loadFeed();
    for feedItem in self.feedItems:
      if(not feedItem.readed):
        return True;
    return False;
    
  def loadFeed(self):
    if(self.updatedNeeded()):
      self.updateFeed();
      self.saveChanges();      
  
  def reload(self, path = []):
    self.updateFeed();
    self.saveChanges();
    
  def displayMenu(self, path):
    self.loadFeed();
    for feedItem in self.feedItems:
     self.gui.buildMenuEntry(feedItem);
  
  def insertFeedItem(self,newItem):
    i = 0
    for i in range(len(self.feedItems)):
      if(newItem.date > self.feedItems[i].date):
        self.feedItems.insert(i, newItem);
        return;
    self.feedItems.insert(i, newItem);
  
  def shrinkFeedItems(self):
    while(len(self.feedItems) > self.maxArticleNumber):
      delItem = self.feedItems[self.maxArticleNumber];
      self.feedItems.remove(delItem);
  
  def getAllUnreadItems(self,items):
    for feedItem in self.feedItems:
      if(not feedItem.readed):
        items.append(feedItem);
        
  def play(self, path):
    self.loadFeed();
    if len(path) > 0:
      index = int(path.pop(0));
      feedItem = self.feedItems[index];
      feedItem.readed = True;
      self.gui.play(feedItem);
      self.saveChanges();
    else:
      self.gui.play(self);
      self.markRead();
    
      
  def markRead(self, path = []):
    self.loadFeed();
    if len(path) > 0:
      self.gui.log("feed mark read")
      index = int(path.pop(0));
      feedItem = self.feedItems[index];
      feedItem.readed = True;
    else:
      self.gui.log("feed mark read item")
      for feedItem in self.feedItems:
        self.gui.log("readed set "+feedItem.title)
        feedItem.readed = True;
    self.saveChanges();
      
  def checkArticleAge(self, articleDate):
    articleAge = time.time() - time.mktime(articleDate);
    articleAge = articleAge / 86400 #to days;
    return articleAge < self.maxArticleAge;
  
  def updatedNeeded(self):
    actTime = time.time();
    diffTime = (actTime - self.lastLoad) / 60;
    return diffTime > self.fetchInterval;
  
  def parseFetchInterval(self,interval):
    if(interval.isdigit()):
      return int(interval);
    elif(interval.lower() == "hourly"):
      return 60;
    elif(interval.lower() == "daily"):
      return 1440;
    elif(interval.lower() == "weekly"):
      return 10080;
    elif(interval.lower() == "monthly"):
      return 43200;
  
  def readText(self,node,textNode):
    try:
      node = node.getElementsByTagName(textNode)[0].firstChild;
      return unicode(node.data);
    except:
      return "";
  
  def parseDate(self,dateString):
    dateString = regex_dateString.search(dateString).group();
    for month in month_replacements.keys():
      dateString = dateString.replace(month,month_replacements[month]);
    return time.strptime(dateString,"%d %m %Y");
    
  def writeDate(self, date):
    return time.strftime("%d %m %Y",date);
    
  def parseBoolean(self, boolean):
    if(boolean == "True"):
      return True;
    else:
      return False;
  
  def writeBoolean(self, boolean):
    if(boolean):
      return "True";
    else:
      return "False";
      
  def loadPage(self,url):
    try:
      safe_url = url.replace( " ", "%20" ).replace("&amp;","&")
      self.gui.log('Downloading from url=%s' % safe_url)
      sock = urllib.urlopen( safe_url )
      doc = sock.read()
      sock.close()
      if doc:
        try:
          return doc.encode('UTF-8');
        except:
          return doc;
      else:
        return ''
    except:
      return ''
      
    