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

import re;
from xml.dom import minidom
from feedreader import *;
findPicLink = re.compile("src=\".*?\"");


class RssFeed (Feed):
  def findImage(self, xmlDocument):
    images = xmlDocument.getElementsByTagName("image");
    if(len(images) > 0):
      return self.readText(images[0], "url");
    else:
      images = xmlDocument.getElementsByTagName("itunes:image");
      if(len(images) > 0):
        return images[0].getAttribute("href");
    return "";

  def updateFeed(self):
    feedItems = [];

    xmlPage = self.loadPage(self.feedUrl);

    if(xmlPage is None):
      return;

    try:
      xmlDocument = minidom.parseString(xmlPage);
    except Exception as error:
      self.gui.log('Error while parsing result from %s' % self.feedUrl)
      self.gui.log(error.message);
      return;
    self.picture = self.findImage(xmlDocument);

    counter = 0;
    for itemNode in xmlDocument.getElementsByTagName("item"):
      feedItem = FeedItem();
      feedItem.guid = self.readText(itemNode,"guid");
      feedItem.title = self.readText(itemNode,"title");
      feedItem.subTitle = self.readText(itemNode,"itunes:subtitle");

      dateString = self.readText(itemNode,"pubDate");
      feedItem.date = self.parseDate(dateString);

      feedItem.author = self.readText(itemNode,"itunes:author");
      feedItem.duration = self.readText(itemNode,"itunes:duration").replace("00:","");
      enclosures = itemNode.getElementsByTagName("enclosure")
      if(len(enclosures) > 0):
        enclosureNode = itemNode.getElementsByTagName("enclosure")[0];

        feedItem.link = enclosureNode.getAttribute("url");
        try:
          feedItem.size = int(enclosureNode.getAttribute("length"));
        except ValueError:
          feedItem.size = 0;
      else:
        feedItem.size = 0;
        feedItem.link = self.parseIndirectItem(self.readText(itemNode,"link"));

      descriptionNode = itemNode.getElementsByTagName("itunes:summary");
      if(len(descriptionNode)>0):
        descriptionNode = descriptionNode[0];
      else:
        descriptionNode = itemNode.getElementsByTagName("description")[0];

      if descriptionNode.firstChild is not None:
        feedItem.description = descriptionNode.firstChild.data;
      else:
        feedItem.description = "";
      link = findPicLink.search(feedItem.description)
      if(link is not None):
        link = link.group().replace("src=","").replace("\"","");
        feedItem.picture = link;
      else:
        feedItem.picture = "";

      feedItem.readed = False;
      feedItems.append(feedItem);
    sortedList = sorted(feedItems, key = lambda item:item.date, reverse=True);

    for feedItem in sortedList:
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

      self.insertFeedItem(feedItem);
      counter += 1;
      if(counter>self.maxArticleNumber):
        break;
    self.shrinkFeedItems();
