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
from future import standard_library
standard_library.install_aliases()
import base64
import json
import re
import time
import urllib.request, urllib.parse, urllib.error

from mediathek import *


class ARDMediathek(Mediathek):
    def __init__(self, simpleXbmcGui):
        self.gui = simpleXbmcGui
        self.rootLink = "https://www.ardmediathek.de"
        self.menuTree = (
            TreeNode("0", "Alle", self.rootLink + "/ard/", True),
            TreeNode("1", "Das Erste", self.rootLink + "/daserste/", True),
            TreeNode("2", "BR", self.rootLink + "/br/", True),
            TreeNode("3", "HR", self.rootLink + "/hr/", True),
            TreeNode("4", "MDR", self.rootLink + "/mdr/", True),
            TreeNode("5", "NDR", self.rootLink + "/ndr/", True),
            TreeNode("6", "Radio Bremen", self.rootLink + "/radiobremen/", True),
            TreeNode("7", "RBB", self.rootLink + "/rbb/", True),
            TreeNode("8", "SR", self.rootLink + "/sr/", True),
            TreeNode("9", "SWR", self.rootLink + "/swr/", True),
            TreeNode("10", "WDR", self.rootLink + "/wdr/", True),
            TreeNode("11", "ONE", self.rootLink + "/one/", True),
            TreeNode("12", "ARD-alpha", self.rootLink + "/alpha/", True)
        )
        self.configLink = self.rootLink + "/play/media/%s?devicetype=pc&feature=flash"
        self.regex_VideoPageLink = re.compile("<a href=\".*Video\?.*?documentId=(\d+).*?\" class=\"textLink\">\s+?<p class=\"dachzeile\">(.*?)<\/p>\s+?<h4 class=\"headline\">(.*?)<\/h4>\s+?<p class=\"subtitle\">(?:(\d+.\d+.\d+) \| )?(\d*) Min.")
        self.regex_CategoryPageLink = re.compile("<a href=\"(.*(?:Sendung|Thema)\?.*?documentId=\d+.*?)\" class=\"textLink\">(?:.|\n)+?<h4 class=\"headline\">(.*?)<\/h4>")
        self.pageSelectString = "&mcontent%s=page.%s"
        self.regex_DetermineSelectedPage = re.compile("&mcontents{0,1}=page.(\d+)")

        self.regex_videoLinks = re.compile("\"_quality\":(\d).*?\"_stream\":\[?\"(.*?)\"")
        self.regex_pictureLink = re.compile("_previewImage\":\"(.*?)\"")

        self.regex_Date = re.compile("\\d{2}\\.\\d{2}\\.\\d{2}")
        self.__date_format_broadcasted_on = "%Y-%m-%dT%H:%M:%S.%fZ"
        self.__date_format_broadcasted_on_old = "%Y-%m-%dT%H:%M:%SZ"

        self.replace_html = re.compile("<.*?>")
        self.regex_DetermineClient = re.compile(self.rootLink + "/(.*)/")
        self.categoryListingKey = "$ROOT_QUERY.widget({\"client\":\"%s\",\"pageNumber\":%s,\"pageSize\":%s,\"widgetId\":\"%s\"})"
        self.playerLink = self.rootLink + "/ard/player/%s"
        self.regex_ExtractJson = re.compile("__APOLLO_STATE__ = ({.*});")
        self.tumbnail_size = "600"

        self.variables = "{\"widgetId\":\"%s\",\"client\":\"%s\",\"pageNumber\":%d,\"pageSize\":%d}"
        self.extension = "{\"persistedQuery\":{\"version\":1,\"sha256Hash\":\"915283a7f9b1fb8a5b2628aaa45aef8831f789a8ffdb31aa81fcae53945ee712\"}}"
        self.publicGateway = "https://api.ardmediathek.de/public-gateway?variables=%s&extensions=%s"

    def __getBroadcastedOnDate(self, teaserContent):
        """parse time in broadcastedOn property"""
        if teaserContent["broadcastedOn"] is not None:
            broadcasted_on = teaserContent["broadcastedOn"]
            try:
                date = time.strptime(broadcasted_on, self.__date_format_broadcasted_on)
            except ValueError:
                try:
                    # retry with old format
                    date = time.strptime(broadcasted_on, self.__date_format_broadcasted_on_old)
                except ValueError:
                    date = None
        else:
            date = None
        return date

    @classmethod
    def name(cls):
        return "ARD"

    @classmethod
    def isSearchable(cls):
        return False

    def extractJsonFromPage(self, link):
        pageContent = self.loadPage(link).decode('UTF-8')
        content = self.regex_ExtractJson.search(pageContent).group(1)
        return json.loads(content)

    def buildPageMenu(self, link, initCount):
        self.gui.log("Build Page Menu: %s" % link)
        jsonContent = self.extractJsonFromPage(link)
        callHash = self.gui.storeJsonFile(jsonContent)
        client = self.regex_DetermineClient.search(link).group(1)

        for key in jsonContent:
            if key.startswith("Widget:"):
                self.GenerateCaterogyLink(jsonContent[key], callHash, jsonContent, client)

    def GenerateCaterogyLink(self, widgetContent, callHash, jsonContent, client):
        widgetId = widgetContent["id"]
        listingKey = self.buildcategoryListingKey(client, widgetId, jsonContent)
        title = widgetContent["title"]
        if widgetContent["titleVisible"] is True:
            self.gui.buildJsonLink(self, title, "%s.%s" % (client, widgetId), callHash, 0)
        else:
            if listingKey in jsonContent:
                widgetContent = jsonContent[listingKey]
                self.GenerateCaterogyLinks(widgetContent, jsonContent)

    def buildcategoryListingKey(self, client, widgetId, jsonContent):
        # ich werd zum elch... erst noch die "dynamische" Pagesize/Number nachschlagen ...
        widgetContent = jsonContent["Widget:%s" % widgetId]
        paginationId = widgetContent["pagination"]["id"]
        paginationContent = jsonContent[paginationId]
        pageSize = paginationContent["pageSize"]
        pageNumber = paginationContent["pageNumber"]

        return self.categoryListingKey % (client, pageNumber, pageSize, widgetId)

    def buildJsonLink(self, client, widgetId, jsonContent):
        # es wird immer besser ...
        widgetContent = jsonContent["Widget:%s" % widgetId]
        paginationId = widgetContent["pagination"]["id"]
        paginationContent = jsonContent[paginationId]
        pageSize = paginationContent["pageSize"]
        pageNumber = paginationContent["pageNumber"]

        variables = urllib.parse.quote_plus(self.variables % (widgetId, client, pageNumber, pageSize))
        extension = urllib.parse.quote_plus(self.extension)
        return self.publicGateway % (variables, extension)

    def buildJsonMenu(self, path, callhash, initCount):
        jsonContent = self.gui.loadJsonFile(callhash)
        path = path.split(".")
        client = path[0]
        widgetId = path[1]

        listingKey = self.buildcategoryListingKey(client, widgetId, jsonContent)
        if listingKey in jsonContent:
            widgetContent = jsonContent[listingKey]
            self.GenerateCaterogyLinks(widgetContent, jsonContent)
        else:
            link = self.buildJsonLink(client, widgetId, jsonContent)

            pageContent = self.loadPage(link)
            jsonContent = json.loads(pageContent)

            dataObject = jsonContent["data"]
            widgetObject = dataObject["widget"]

            for jsonObject in widgetObject["teasers"]:
                self.GenerateTeaserLink(jsonObject)

    def GenerateCaterogyLinks(self, widgetContent, jsonContent):
        for teaser in widgetContent["teasers"]:
            teaserId = teaser["id"]
            self.GenerateVideoLink(jsonContent[teaserId], jsonContent)

    def GenerateTeaserLink(self, teaserContent):
        title = teaserContent["shortTitle"]
        subTitle = None
        picture = None
        images = teaserContent["images"]
        for key in images:
            imageObject = images[key]
            if type(imageObject) is dict:
                picture = imageObject["src"].replace("{width}", self.tumbnail_size)

        duration = teaserContent["duration"]
        date = self.__getBroadcastedOnDate(teaserContent)
        videoLink = base64.b64encode(self.playerLink % teaserContent["links"]["target"]["id"])
        displayObject = DisplayObject(title, subTitle, picture, "", videoLink, "JsonLink", date, duration)
        self.gui.buildVideoLink(displayObject, self, 0)

    def GenerateVideoLink(self, teaserContent, jsonContent):
        title = teaserContent["shortTitle"]
        subTitle = None
        picture = self.getPictureLink(teaserContent["images"], jsonContent)
        videoLinks = base64.b64encode(self.getVideoLinks(teaserContent["links"], jsonContent))
        date = self.__getBroadcastedOnDate(teaserContent)
        duration = teaserContent["duration"]
        if 'type' in teaserContent and teaserContent[u'type'] == u"live":
            title = u"live " + title
            date = None
        displayObject = DisplayObject(title, subTitle, picture, "", videoLinks, "JsonLink", date, duration)
        self.gui.buildVideoLink(displayObject, self, 0)

    def getVideoLinks(self, linkSource, jsonContent):
        # WTF geht es noch sinnloser?
        key = linkSource["id"]
        key = jsonContent[key]["target"]["id"]
        return self.playerLink % jsonContent[key]["id"]

    def getPictureLink(self, pictureSource, jsonContent):
        if pictureSource is not None:
            key = pictureSource["id"]
            pictureConfig = jsonContent[key]
            for key in pictureConfig:
                if key.startswith("aspect") and pictureConfig[key] is not None:
                    key = pictureConfig[key]["id"]
                    return jsonContent[key]["src"].replace("{width}", self.tumbnail_size)
        return None

    def playVideoFromJsonLink(self, link):
        link = base64.b64decode(link)
        # WTF OHHHHHHHHH JAAAAAA - es geht noch sinnloser...
        self.gui.log("Play from JSON Link %s" % link)
        jsonContent = self.extractJsonFromPage(link)

        videoLinks = {}
        for key in jsonContent:
            if "_mediaStreamArray." in key:
                streamConfig = jsonContent[key]
                if streamConfig["_quality"] == "auto":
                    quality = 3
                else:
                    quality = int(streamConfig["_quality"])
                link = streamConfig["_stream"]["json"][0]
                if not link.startswith("http"):
                    link = "https:" + link
                self.gui.log("VideoLink: " + link)
                videoLinks[quality] = SimpleLink(link, -1)
        if len(videoLinks) > 0:
            self.gui.play(videoLinks)
        else:
            self.gui.log("Nothing playable found")
