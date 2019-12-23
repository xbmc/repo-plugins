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
import time,re;
from archivefile import ArchiveFile
import socket;
import requests;
socket.setdefaulttimeout(1);

regex_mediaLink = re.compile("(http|ftp)://[^'\"]*?\\.(mp3|mpeg|asx|wmv|ogg|mov)");
regex_dateStringShortYear = re.compile("\\d{,2} ((\\w{3,})|(\\d{2})) \\d{2}");
regex_dateString = re.compile("\\d{,2} ((\\w{3,})|(\\d{2})) \\d{4}");
regex_shortdateString = re.compile("\\d{4}-(\\d{2})-\\d{2}");
regex_replaceUnusableChar = re.compile("[:/ \\.\?\\\\]")

month_replacements_long = {
    "January":"01",
    "February":"02",
    "March":"03",
    "April":"04",
    "June":"06",
    "July":"07",
    "August":"08",
    "September":"09",
    "October":"10",
    "November":"11",
    "December":"12"
    };

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
  def loadFromNode(self, opmlNode, gui):
    self.gui = gui;
    self.feedUrl = opmlNode.getAttribute("xmlUrl");
    self.objectId = opmlNode.getAttribute("id");
    if(self.objectId == ""):
      self.objectId = regex_replaceUnusableChar.sub("_",self.feedUrl);
    self.archiveFile=ArchiveFile(self.objectId);

    self.feedItems = self.archiveFile.feedItems;
    self.lastLoad = self.archiveFile.lastLoad;

    self.title = opmlNode.getAttribute("text");
    self.picture = opmlNode.getAttribute("image");

    try:
      self.fetchInterval = self.parseFetchInterval(opmlNode.getAttribute("fetchInterval"));
    except ValueError:
      self.fetchInterval = 0;

    try:
      self.maxArticleAge = int(opmlNode.getAttribute("maxArticleAge"));
    except ValueError:
      self.maxArticleAge = 99;

    try:
      self.maxArticleNumber = int(opmlNode.getAttribute("maxArticleNumber"));
    except ValueError:
      self.maxArticleNumber = 99;

  def loadFromState(self, stateObject, gui):
    self.gui = gui;
    self.feedUrl = stateObject.feedUrl
    self.objectId = stateObject.objectId
    self.archiveFile=ArchiveFile(self.objectId);

    self.feedItems = self.archiveFile.feedItems;
    self.lastLoad = self.archiveFile.lastLoad;
    self.title = stateObject.title

    self.picture = stateObject.picture;

    self.fetchInterval = stateObject.fetchInterval
    self.maxArticleAge = stateObject.maxArticleAge
    self.maxArticleNumber = stateObject.maxArticleNumber

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

  def reload(self, path = None):
    self.updateFeed();
    self.saveChanges();

  def displayMenu(self, path):
    self.loadFeed();
    for feedItem in self.feedItems:
     self.gui.buildMenuEntry(feedItem,len(self.feedItems));

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

  def markRead(self, path = None):
    path = path or [];
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

  @staticmethod
  def parseFetchInterval(interval):
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

  @staticmethod
  def readText(node,textNode):
    try:
      node = node.getElementsByTagName(textNode)[0].firstChild;
      return unicode(node.data);
    except (UnicodeDecodeError,UnicodeEncodeError,IndexError,AttributeError):
      return "";

  @staticmethod
  def parseDate(dateString):
    dateMatch = regex_dateString.search(dateString);
    if(dateMatch is not None):
      dateString = dateMatch.group();
      for month in month_replacements_long.keys():
        dateString = dateString.replace(month,month_replacements_long[month]);
      for month in month_replacements.keys():
        dateString = dateString.replace(month,month_replacements[month]);
      return time.strptime(dateString,"%d %m %Y");
    else:
     dateMatch = regex_shortdateString.search(dateString)
     if(dateMatch is not None):
       dateString = dateMatch.group();
       return time.strptime(dateString,"%Y-%m-%d");
     else:
       dateMatch = regex_dateStringShortYear.search(dateString)
       if(dateMatch is not None):
         dateString = dateMatch.group();
         for month in month_replacements_long.keys():
           dateString = dateString.replace(month,month_replacements_long[month]);
         for month in month_replacements.keys():
           dateString = dateString.replace(month,month_replacements[month]);
         return time.strptime(dateString,"%d %m %y");
    return time.localtime();

  @staticmethod
  def writeDate(date):
    return time.strftime("%d %m %Y",date);

  @staticmethod
  def parseBoolean(self, boolean):
    return bool(boolean == "True");

  def parseIndirectItem(self, targetUrl):
    self.gui.log("TargetUrl: "+targetUrl);
    htmlPage = self.loadPage(targetUrl);
    match = regex_mediaLink.search(htmlPage);
    if(match is None):
      return "";
    link = match.group();
    self.gui.log("IndirectLink: "+link);
    return link;

  @staticmethod
  def writeBoolean(boolean):
    if(boolean):
      return "True";
    else:
      return "False";

  def loadPage(self,url):
    try:
      safe_url = url.replace( " ", "%20" ).replace("&amp;","&")
      self.gui.log('Downloading from url=%s' % safe_url)
      content = requests.get(safe_url, allow_redirects=True, headers={'User-Agent': "Mozilla/5.0 (Linux; rv:68.2.0esr) Gecko/20100101 Firefox/68.2.0esr"});
      if(content.encoding is not None):
        return content.text.encode(content.encoding);
      else:
        return content.text;
    except Exception as error:
      self.gui.log("Error while downloading url=%s"%safe_url);
      self.gui.log(error.message);
      content = None;
    return content;
