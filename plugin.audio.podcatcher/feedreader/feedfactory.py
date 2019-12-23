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
from rss import RssFeed;
from atom import AtomFeed;
class FeedFactory:
  @classmethod
  def getFeedFromNode(self, feedNode, gui):
    feedVersion = feedNode.getAttribute("type")
    if(feedVersion == "rss"):
      feed = RssFeed();
    if(feedVersion == "atom"):
      feed = AtomFeed();
    feed.loadFromNode(feedNode, gui);
    feed.feedVersion = feedVersion
    return feed;

  @classmethod
  def getFeedFromState(self, feedState, gui):
    feedVersion = feedState.feedVersion
    if(feedVersion == "rss"):
      feed = RssFeed();
    if(feedVersion == "atom"):
      feed = AtomFeed();
    feed.loadFromState(feedState,gui);
    feed.feedVersion = feedVersion
    return feed;
