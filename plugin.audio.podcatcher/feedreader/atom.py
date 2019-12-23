# -*- coding: utf-8 -*-

import re;
from xml.dom import minidom
from feedreader import *;
findPicLink = re.compile("src=\".*?\"");


class AtomFeed (Feed):
  def updateFeed(self):
    self.gui.log("Load: "+self.feedUrl);
    xmlPage = self.loadPage(self.feedUrl);

    if(xmlPage is None):
      return;

    xmlDocument = minidom.parseString(xmlPage);

    counter = 0;
    for itemNode in xmlDocument.getElementsByTagName("entry"):
      feedItem = FeedItem();
      feedItem.guid = self.readText(itemNode,"id");
      feedItem.title = self.readText(itemNode,"title");

      dateString = self.readText(itemNode,"updated");
      feedItem.date = self.parseDate(dateString);

      if(not self.checkArticleAge(feedItem.date)):
        break;

      eject = False;
      for i in range(counter,len(self.feedItems)):
        storedItem = self.feedItems[i];
        if(not storedItem.date < feedItem.date):
          eject =True;
          break;

      if(eject == True):
        break;

      authorNodes = itemNode.getElementsByTagName("author");
      if(len(authorNodes)>0):
         feedItem.author = self.readText(authorNodes[0],"name");
      else:
        feedItem.author="";

      feedItem.link = None;
      for enclosureNode in itemNode.getElementsByTagName("link"):
        self.gui.log("rel=%s type=[%s]"%(enclosureNode.getAttribute("rel"),enclosureNode.getAttribute("type")));
        self.gui.log("first:%d second:%d"%(enclosureNode.getAttribute("rel") is not "enclosure",enclosureNode.getAttribute("type").find("audio")));
        if(enclosureNode.getAttribute("rel") != "enclosure" or enclosureNode.getAttribute("type").find("audio") is not 0):
          continue;
        feedItem.link = enclosureNode.getAttribute("href");
        try:
          feedItem.size = int(enclosureNode.getAttribute("length"));
        except ValueError:
          feedItem.size = 0;
        self.gui.log("Link %s Size: %d"%(feedItem.size,feedItem.size));

      if(feedItem.link == None):
        continue

      descriptionNode = itemNode.getElementsByTagName("summary")[0];
      feedItem.description = descriptionNode.firstChild.data;

      link = findPicLink.search(feedItem.description)
      if(link is not None):
        link = link.group().replace("src=","").replace("\"","");
        feedItem.picture = link;
      else:
        feedItem.picture = "";

      feedItem.readed = False;

      self.insertFeedItem(feedItem);
      counter += 1;
      if(counter>self.maxArticleNumber):
        break;
    self.shrinkFeedItems();
