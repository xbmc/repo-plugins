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
from builtins import str
import json
import re
import time

from bs4 import BeautifulSoup

from mediathek import *

regex_dateString = re.compile("\\d{1,2} ((\\w{3})|(\\d{2})) \\d{4}")
month_replacements = {
    "Jan": "01",
    "Feb": "02",
    "Mar": "03",
    "Apr": "04",
    "May": "05",
    "Jun": "06",
    "Jul": "07",
    "Aug": "08",
    "Sep": "09",
    "Oct": "10",
    "Nov": "11",
    "Dec": "12",
}


class ARTEMediathek(Mediathek):

    @classmethod
    def name(cls):
        return "ARTE"

    @classmethod
    def isSearchable(cls):
        return True

    def __init__(self, simpleXbmcGui):
        self.gui = simpleXbmcGui
        self.rootLink = "http://www.arte.tv"
        self.basePage = self.rootLink + "/de/"
        self.jsonLink = "https://api.arte.tv/api/player/v1/config/de/%s?lifeCycle=1"
        self.serachLink = self.rootLink + "/de/search/?q=%s"
        self.menuTree = (
            TreeNode("0", "Arte+7", "mainPage", True),
            TreeNode("1", "Sendungen von A-Z", "showCluster", True),
            TreeNode("2", "Kategorien", "showCategories", True),
        )

        self.selector_videoPages = "li.video > a"

        self.regex_findVideoIds = re.compile("(\d{6}-\d{3})(-A)")
        self.regex_JSONPageLink = re.compile("http://arte.tv/papi/tvguide/videos/stream/player/D/\d{6}-\d{3}.+?/ALL/ALL.json")
        self.regex_JSON_VideoLink = re.compile("\"HTTP_MP4_.+?\":{.*?\"bitrate\":(\d+),.*?\"url\":\"(http://.*?.mp4)\".*?\"versionShortLibelle\":\"([a-zA-Z]{2})\".*?}")
        self.regex_JSON_ImageLink = re.compile("\"IUR\":\"(http://.*?\\.arte\\.tv/papi/tvguide/images/.*?\\..{3})\"")
        self.regex_JSON_Detail = re.compile("\"VDE\":\"(.*?)\"")
        self.regex_JSON_Titel = re.compile("\"VTI\":\"(.*?)\"")

        regexSourceString = "%s=\"([\[{].*?[}\]])\""

        self.regex_cluster = re.compile("\"kind\":\"MAGAZINE\",\"programId\":\"RC-\d+\",\"language\":\"\w{2}\",\"url\":\"(http.*?)\",\"title\":\"(.*?)\",\"subtitle\":(\"(.*?)\"|null),\"images\"")
        self.regex_categories = re.compile("\"link\":{\"page\":\"\w{3}\",\"title\":\"(.*?)\",\"url\":\"(http.*?)\"}")
        self.regex_playlists = re.compile(regexSourceString % "data-highlightedPlaylists")

        self.searchContent = re.compile(regexSourceString % "data-results")

        self.regex_ExtractJson = re.compile("__INITIAL_STATE__ = ({.*});")

    def searchVideo(self, searchText):
        link = self.serachLink % searchText
        pageContent = self.loadPage(link).decode('UTF-8')
        self.extractVideoLinks(pageContent, 0)

    def buildPageMenu(self, link, initCount):
        if link == "showCluster":
            self.showCluster()
        elif link == "mainPage":
            self.showMainPage()
        elif link == "showCategories":
            self.showCategories()
        else:
            if not link.startswith("http"):
                link = self.rootLink + link
            self.parsePage(link)

    def extractJsonFromPage(self, link):
        pageContent = self.loadPage(link).decode('UTF-8')
        content = self.regex_ExtractJson.search(pageContent).group(1)
        pageContent = BeautifulSoup(content, "html.parser")
        jsonContent = pageContent.prettify(formatter=None)
        return json.loads(jsonContent)

    def parsePage(self, link):
        jsonContent = self.extractJsonFromPage(link)
        page = jsonContent["pages"]
        currentCode = page["currentCode"]
        for zone in page["list"][currentCode]["zones"]:
            if "videos" in zone["code"]["name"]:
                for teaser in zone["data"]:
                    self.buildVideoEntry(teaser)

    def showMainPage(self):
        self.gui.log("buildPageMenu: " + self.basePage)
        jsonContent = self.extractJsonFromPage(self.basePage)
        zones = jsonContent["pages"]["list"]["HOME_de_{}"]["zones"]
        for zone in zones:
            if "highlights" in zone["code"]["name"] or "playlists" in zone["code"]["name"]:
                for teaser in zone["data"]:
                    self.buildVideoEntry(teaser)

    def buildJsonMenu(self, path, callhash, initCount):
        jsonContent = self.gui.loadJsonFile(callhash)
        for teaser in jsonContent["data"]:
            self.buildVideoEntry(teaser)

    def buildJsonLink(self, name, jsonContent):
        callhash = self.gui.storeJsonFile(jsonContent, name)
        self.gui.buildJsonLink(self, name, "init", callhash, 0)

    def extractVideoLinksFromHtml(self, htmlPage):
        someMatch = False
        for regex in self.regex_extractVideoSources:
            match = regex.search(htmlPage)
            if match is not None:
                someMatch = True
                content = BeautifulSoup(match.group(1), "html.parser")
                jsonContent = json.loads(content.prettify(formatter=None))
                self.extractVideoLinksFromJson(jsonContent)
        return someMatch

    def extractVideoLinksFromJson(self, jsonContent):
        for jsonObject in jsonContent["videos"]:
            self.buildVideoEntry(jsonObject)

    def showCategories(self):
        jsonContent = self.extractJsonFromPage(self.basePage)
        for zone in jsonContent["pages"]["list"]["HOME_de_{}"]["zones"]:
            if zone["link"] and "title" in zone:
                title = zone["title"]
                if isinstance(title, str):
                    title = title.encode('utf8')
                self.buildJsonLink(title, zone)

    def showCluster(self):
        jsonContent = self.extractJsonFromPage(self.basePage)
        for zone in jsonContent["pages"]["list"]["HOME_de_{}"]["zones"]:
            if ("magazine" in zone["code"]["name"]):
                for teaser in zone["data"]:
                    self.buildVideoEntry(teaser)

    def buildMenuEntry(self, menuItem):
        title = menuItem["title"]
        subTitle = menuItem["subtitle"]
        link = menuItem["permalink"]
        self.gui.buildVideoLink(DisplayObject(title, subTitle, "", "", link, False, None), self, 0)

    def buildVideoEntry(self, jsonObject):
        title = str(jsonObject["title"])
        if jsonObject["subtitle"] is not None:
            subTitle = str(jsonObject["subtitle"])
        else:
            subTitle = None
        if "teaser" in jsonObject:
            detail = str(jsonObject["teaser"])
        else:
            detail = ""

        pictures = None
        pictureUrl = None
        if "thumbnails" in jsonObject:
            pictures = jsonObject["thumbnails"]
        if "images" in jsonObject:
            square = jsonObject["images"]["square"]
            landscape = jsonObject["images"]["landscape"]
            if square is not None:
                pictures = square["resolutions"]
            else:
                pictures = landscape["resolutions"]
        if pictures is not None:
            picture = None
            for pictureItem in pictures:
                if picture is None or picture["w"] < pictureItem["w"]:
                    picture = pictureItem
            pictureUrl = picture["url"]
        if pictureUrl is None and "mainImage" in jsonObject:
            pictureUrl = jsonObject["mainImage"]["url"]

        pubDate = None
        if "scheduled_on" in jsonObject:
            pubDate = time.strptime(jsonObject["scheduled_on"], "%Y-%m-%d")
        if "publicationBegin" in jsonObject:
            pubDate = time.strptime(jsonObject["publicationBegin"], "%Y-%m-%dT%H:%M:%SZ")
        if "availability" in jsonObject and jsonObject["availability"] is not None and jsonObject["availability"]["start"] is not None:
            pubDate = time.strptime(jsonObject["availability"]["start"], "%Y-%m-%dT%H:%M:%SZ")

        duration = None
        if "duration" in jsonObject and jsonObject["duration"] is not None:
            duration = int(jsonObject["duration"])
        if "durationSeconds" in jsonObject and jsonObject["durationSeconds"] is not None:
            duration = int(jsonObject["durationSeconds"])
        if duration is None:
            duration = 0

        kind = jsonObject["kind"]
        if kind is not None and kind["code"] in ("SHOW", "MANUAL_CLIP"):
            link = self.jsonLink % jsonObject["programId"]

            self.gui.buildVideoLink(
                DisplayObject(title, subTitle, pictureUrl, detail, link, "JsonLink", pubDate, duration), self, 0)
        else:
            link = jsonObject["url"]
            self.gui.buildVideoLink(DisplayObject(title, subTitle, pictureUrl, detail, link, False, pubDate, duration), self, 0)

    def playVideoFromJsonLink(self, link):
        jsonObject = json.loads(self.loadPage(link))
        links = self.extractLinks(jsonObject["videoJsonPlayer"])
        self.gui.play(links)

    def extractLinks(self, jsonObject):
        links = {}

        vsrObjects = jsonObject["VSR"]
        if not isinstance(vsrObjects, dict):
            return links

        for videoObject in list(jsonObject["VSR"].values()):
            if videoObject["versionShortLibelle"] != "DE" and videoObject["versionShortLibelle"] != "OmU":
                continue
            if videoObject["mediaType"] == "mp4":
                url = videoObject["url"]
                quality = videoObject["quality"]
                self.gui.log("%s %s" % (quality, url))
                if quality == "MQ":
                    links[0] = SimpleLink(url, -1)
                if quality == "HQ":
                    links[1] = SimpleLink(url, -1)
                if quality == "EQ":
                    links[2] = SimpleLink(url, -1)
                if quality == "SQ":
                    links[3] = SimpleLink(url, -1)
        return links

    def extractVideoLinks(self, htmlPage, initCount):
        links = set()
        jsonLinks = set()
        for videoPageLink in self.regex_findVideoIds.finditer(htmlPage):
            link = self.jsonLink % videoPageLink.group(1)
            if link not in jsonLinks:
                jsonLinks.add(link)

        linkCount = initCount + len(links)
        for link in links:
            if not link.startswith(self.rootLink):
                videoPage = self.loadPage(self.rootLink + link)
            else:
                videoPage = self.loadPage(link)
            match = self.regex_JSONPageLink.search(videoPage)
            if match is not None:
                jsonLinks.add(match.group(0))

        linkCount = linkCount + len(jsonLinks)

        self.gui.log("Found %s unique links" % len(jsonLinks))
        displayObjects = list()
        for link in jsonLinks:
            jsonPage = json.loads(self.loadPage(link))
            displayObject = self.extractVideoLinksFromJSONPage(jsonPage["videoJsonPlayer"])
            if displayObject is not None:
                self.gui.buildVideoLink(displayObject, self, linkCount)

    def extractVideoLinksFromJSONPage(self, jsonPage):
        videoLinks = self.extractLinks(jsonPage)
        if len(videoLinks) == 0:
            return

        picture = jsonPage["VTU"]["IUR"]
        title = jsonPage["VTI"]

        subTitle = ""
        if "subtitle" in jsonPage:
            subTitle = jsonPage["subtitle"]

        detail = ""
        if "V7T" in jsonPage:
            detail = self.gui.transformHtmlCodes(jsonPage["V7T"])

        duration = None
        if "videoDurationSeconds" in jsonPage:
            duration = jsonPage["videoDurationSeconds"]

        if "VRA" in jsonPage:
            pubDate = time.strptime(jsonPage["VRA"], "%d/%m/%Y %H:%M:%S +0000")
        else:
            pubDate = time.gmtime()
        return DisplayObject(title, subTitle, picture, detail, videoLinks, True, pubDate, duration)
