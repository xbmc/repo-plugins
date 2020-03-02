# -*- coding: utf-8 -*- 
# -------------LicenseHeader--------------
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

import json
import time
from datetime import datetime, timedelta

from mediathek import *


class ZDFMediathek(Mediathek):
    def __init__(self, simpleXbmcGui):
        self.gui = simpleXbmcGui

        today = datetime.today()

        self.__mediathekUrl = "https://zdf-cdn.live.cellular.de/mediathekV2/"
        documentUrl = self.__mediathekUrl + "document/"
        mediathekUrlMissedFormat = self.__mediathekUrl + "broadcast-missed/%s"
        self.menuTree = (
            TreeNode("0", "Startseite", self.__mediathekUrl + "start-page", True),
            TreeNode("1", "Kategorien", "", False, (
                TreeNode("1.0", u"Comedy/Show", documentUrl + "comedy-und-show-100", True),
                TreeNode("1.1", u"Doku/Wissen", documentUrl + "doku-wissen-104", True),
                TreeNode("1.2", u"Filme", documentUrl + "filme-104", True),
                TreeNode("1.3", u"Geschichte", documentUrl + "geschichte-108", True),
                TreeNode("1.4", u"nachrichten", documentUrl + "nachrichten-100", True),
                TreeNode("1.5", u"Kinder/ZDFtivi", documentUrl + "kinder-100", True),
                TreeNode("1.6", u"Krimi", documentUrl + "krimi-102", True),
                TreeNode("1.7", u"Kultur", documentUrl + "kultur-104", True),
                TreeNode("1.8", u"Politik/Gesellschaft", documentUrl + "politik-gesellschaft-102", True),
                TreeNode("1.9", u"Serien", documentUrl + "serien-100", True),
                TreeNode("1.10", u"Sport", documentUrl + "sport-106", True),
                TreeNode("1.11", u"Verbraucher", documentUrl + "verbraucher-102", True),
            )),
            TreeNode("2", "Sendungen von A-Z", self.__mediathekUrl + "brands-alphabetical", True),
            TreeNode("3", "Sendung verpasst?", "", False, (
                TreeNode("3.0", "Heute", mediathekUrlMissedFormat % (today.strftime("%Y-%m-%d")), True),
                TreeNode("3.1", "Gestern", mediathekUrlMissedFormat % ((today - timedelta(days=1)).strftime("%Y-%m-%d")), True),
                TreeNode("3.2", "Vorgestern", mediathekUrlMissedFormat % ((today - timedelta(days=2)).strftime("%Y-%m-%d")), True),
                TreeNode("3.3", (today - timedelta(days=3)).strftime("%A"), mediathekUrlMissedFormat % ((today - timedelta(days=3)).strftime("%Y-%m-%d")), True),
                TreeNode("3.4", (today - timedelta(days=4)).strftime("%A"), mediathekUrlMissedFormat % ((today - timedelta(days=4)).strftime("%Y-%m-%d")), True),
                TreeNode("3.5", (today - timedelta(days=5)).strftime("%A"), mediathekUrlMissedFormat % ((today - timedelta(days=5)).strftime("%Y-%m-%d")), True),
                TreeNode("3.6", (today - timedelta(days=6)).strftime("%A"), mediathekUrlMissedFormat % ((today - timedelta(days=6)).strftime("%Y-%m-%d")), True),
                TreeNode("3.7", (today - timedelta(days=7)).strftime("%A"), mediathekUrlMissedFormat % ((today - timedelta(days=7)).strftime("%Y-%m-%d")), True),
            )),
            TreeNode("4", "Live TV", self.__mediathekUrl + "live-tv/%s" % (today.strftime("%Y-%m-%d")), True)
        )

    @classmethod
    def name(self):
        return "ZDF"

    def isSearchable(self):
        return True

    def searchVideo(self, searchText):
        self.buildPageMenu(self.__mediathekUrl + "search?q=%s" % searchText, 0)

    def buildPageMenu(self, link, initCount):
        self.gui.log("buildPageMenu: " + link)
        jsonObject = json.loads(self.loadPage(link))
        callhash = self.gui.storeJsonFile(jsonObject)

        if "stage" in jsonObject:
            for stageObject in jsonObject["stage"]:
                if stageObject["type"] == "video":
                    self.buildVideoLink(stageObject, initCount)
        if "results" in jsonObject:
            for stageObject in jsonObject["results"]:
                if stageObject["type"] == "video":
                    self.buildVideoLink(stageObject, initCount)
        if "cluster" in jsonObject:
            for counter, clusterObject in enumerate(jsonObject["cluster"]):
                if "teaser" in clusterObject and "name" in clusterObject:
                    path = "cluster.%d.teaser" % (counter)
                    self.gui.buildJsonLink(self, clusterObject["name"], path, callhash, initCount)
        if "broadcastCluster" in jsonObject:
            for counter, clusterObject in enumerate(jsonObject["broadcastCluster"]):
                if clusterObject["type"].startswith("teaser") and "name" in clusterObject:
                    path = "broadcastCluster.%d.teaser" % (counter)
                    self.gui.buildJsonLink(self, clusterObject["name"], path, callhash, initCount)
        if "epgCluster" in jsonObject:
            for epgObject in jsonObject["epgCluster"]:
                if "liveStream" in epgObject and len(epgObject["liveStream"]) > 0:
                    self.buildVideoLink(epgObject["liveStream"], initCount)

    def buildJsonMenu(self, path, callhash, initCount):
        jsonObject = self.gui.loadJsonFile(callhash)
        jsonObject = self.walkJson(path, jsonObject)
        categoriePages = []
        videoObjects = []

        for entry in jsonObject:
            if entry["type"] == "brand":
                categoriePages.append(entry)
            if entry["type"] == "video":
                videoObjects.append(entry)
        self.gui.log("CategoriePages: %d" % len(categoriePages))
        self.gui.log("VideoPages: %d" % len(videoObjects))
        for categoriePage in categoriePages:
            title = categoriePage["titel"]
            subTitle = categoriePage["beschreibung"]
            imageLink = ""
            for width, imageObject in list(categoriePage["teaserBild"].items()):
                if int(width) <= 840:
                    imageLink = imageObject["url"]
            url = categoriePage["url"]
            self.gui.buildVideoLink(DisplayObject(title, subTitle, imageLink, "", url, False), self, initCount)

        for videoObject in videoObjects:
            self.buildVideoLink(videoObject, initCount)

    def buildVideoLink(self, videoObject, counter):
        title = videoObject["headline"]
        subTitle = videoObject["titel"]

        if len(title) == 0:
            title = subTitle
            subTitle = ""
        if "beschreibung" in videoObject:
            description = videoObject["beschreibung"]
        imageLink = ""
        if "teaserBild" in videoObject:
            for width, imageObject in list(videoObject["teaserBild"].items()):
                if int(width) <= 840:
                    imageLink = imageObject["url"]
        if "visibleFrom" in videoObject:
            date = time.strptime(videoObject["visibleFrom"], "%d.%m.%Y %H:%M")
        else:
            date = time.gmtime()
        if "formitaeten" in videoObject:
            links = self.extractLinks(videoObject)
            self.gui.buildVideoLink(
                DisplayObject(title, subTitle, imageLink, description, links, True, date, videoObject.get('length')),
                self, counter)
        else:
            link = videoObject["url"]
            videoLength = videoObject.get('length')
            displayObject = DisplayObject(title, subTitle, imageLink, description, link, "JsonLink", date, videoLength)
            self.gui.buildVideoLink(displayObject, self, counter)

    def playVideoFromJsonLink(self, link):
        jsonObject = json.loads(self.loadPage(link))
        links = self.extractLinks(jsonObject["document"])
        self.gui.play(links)

    def extractLinks(self, jsonObject):
        self.gui.log(json.dumps(jsonObject, sort_keys=True));
        links = {}
        for formitaete in jsonObject["formitaeten"]:
            url = formitaete["url"]
            quality = formitaete["quality"]
            hd = formitaete["hd"]
            self.gui.log("quality:%s hd:%s url:%s" % (quality, hd, url))
            if hd is True:
                links[4] = SimpleLink(url, -1)
            else:
                if quality == "low":
                    links[0] = SimpleLink(url, -1)
                if quality == "med":
                    links[1] = SimpleLink(url, -1)
                if quality == "high":
                    links[2] = SimpleLink(url, -1)
                if quality == "veryhigh":
                    links[3] = SimpleLink(url, -1)
                if quality == "auto":
                    links[3] = SimpleLink(url, -1)
        return links
