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
import re
import time
from xml.dom import minidom

from mediathek import *

regex_dateString = re.compile("\\d{2}\\.((\\w{3})|(\\d{2}))\\.\\d{4}")
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


class DreiSatMediathek(Mediathek):
    @classmethod
    def name(self):
        return "3Sat"

    def isSearchable(self):
        return True

    def __init__(self, simpleXbmcGui):
        self.gui = simpleXbmcGui
        if self.gui.preferedStreamTyp == 0:
            self.baseType = "video/x-ms-asf"
        elif self.gui.preferedStreamTyp == 1:
            self.baseType = "video/x-ms-asf"
        elif self.gui.preferedStreamTyp == 2:
            self.baseType = "video/x-ms-asf"
        else:
            self.baseType = "video/quicktime"
        self.webEmType = "video/webm"
        self.menuTree = (
            TreeNode("0", "Hauptseite", "http://www.3sat.de/mediathek/", True),
            TreeNode("1", "Sendungen von A-Z", "", False, (
                TreeNode("1.0", "Kulturzeit", "http://www.3sat.de/mediathek/?red=kulturzeit", True),
                TreeNode("1.1", "Nano", "http://www.3sat.de/mediathek/?red=nano", True),
                TreeNode("1.2", "marko", "http://www.3sat.de/mediathek/?red=makro", True),
                TreeNode("1.3", "scobel", "http://www.3sat.de/mediathek/?red=scobel", True),
                TreeNode("1.4", "Wissenschaftsdoku", "http://www.3sat.de/mediathek/?red=wido", True),
                TreeNode("1.5", "3satbuchzeit", "http://www.3sat.de/mediathek/?red=buchzeit", True),
                TreeNode("1.6", "Ab 18!", "http://www.3sat.de/mediathek/?red=ab18", True),
                TreeNode("1.7", "auslandsjournal extra", "http://www.3sat.de/mediathek/?red=ajextra", True),
                TreeNode("1.8", "Bauerfeind", "http://www.3sat.de/mediathek/?red=bauerfeind", True),
                TreeNode("1.9", "Besonders normal", "http://www.3sat.de/mediathek/?red=besondersnormal", True),
                TreeNode("1.10", "Close up", "http://www.3sat.de/mediathek/?red=closeup", True),
                TreeNode("1.11", "Film", "http://www.3sat.de/mediathek/?red=film", True),
                TreeNode("1.12", "hitec", "http://www.3sat.de/mediathek/?red=hitec", True),
                TreeNode("1.13", "Kabarett / Comedy", "http://www.3sat.de/mediathek/?red=kabarett", True),
                TreeNode("1.14", "Kennwort Kino", "http://www.3sat.de/mediathek/?red=kennwortkino", True),
                TreeNode("1.15", "Kulturpalast", "http://www.3sat.de/mediathek/?red=kulturpalast", True),
                TreeNode("1.16", "Museumscheck", "http://www.3sat.de/mediathek/?red=museumscheck", True),
                TreeNode("1.17", "Musik", "http://www.3sat.de/mediathek/?red=musik", True),
                TreeNode("1.18", u"Peter Voß fragt", "http://www.3sat.de/mediathek/?red=begegnungen", True),
                TreeNode("1.19", "Philosophie", "http://www.3sat.de/mediathek/?red=philosophie", True),
                TreeNode("1.20", "Pixelmacher", "http://www.3sat.de/mediathek/?red=pxl", True),
                TreeNode("1.21", "SCHWEIZWEIT", "http://www.3sat.de/mediathek/?red=schweizweit", True)
            )),
        )

        self.rootLink = "http://www.3sat.de"
        self.searchLink = 'http://www.3sat.de/mediathek/?mode=suche&query=%s'

        self.history_counter = re.compile("verpasst(\\d+)")
        self.regex_nextLink = re.compile("(\\/\\/www.3sat.de\\/mediathek\\/\\?mode=verpasst(\\d+)&amp;red=.*?)\"")
        self.regex_objectLink = re.compile("obj=(\\d+)")
        self.regex_dimensions = re.compile("(\\d)+x(\\d+)")
        self.xmlService_Link = "http://www.3sat.de/mediathek/xmlservice.php/v3/web/beitragsDetails?id=%s"
        self.jsonService_Link = "http://tmd.3sat.de/tmd/2/ngplayer_2_3/vod/ptmd/3sat/%s"

    def buildPageMenu(self, link, initCount):
        self.gui.log("buildPageMenu: " + link)
        match = self.history_counter.search(link)
        if match is not None:
            history_counter = int(match.group(1))
        else:
            history_counter = 0
        mainPage = self.loadPage(link)
        matches = self.regex_objectLink.finditer(mainPage);
        matches = list(matches)
        counter = len(matches) + initCount

        objectIds = []
        for match in matches:
            objectId = match.group(1)
            if objectId not in objectIds:
                objectIds.append(objectId)

        for objectId in objectIds:
            self.buildVideoLink(objectId, counter)

        for match in self.regex_nextLink.finditer(mainPage):
            if int(match.group(2)) == history_counter + 1:
                link = "http:" + match.group(1)
                self.gui.buildVideoLink(DisplayObject("Weiter", match.group(2), "", "", link, False, None, None), self, counter)
                break

    def buildVideoLink(self, objectId, counter):
        xmlPage = self.loadPage(self.xmlService_Link % objectId)
        xmlPage = minidom.parseString(xmlPage)
        videoNode = xmlPage.getElementsByTagName("video")[0]
        informationNode = xmlPage.getElementsByTagName("information")[0]
        detailsNode = xmlPage.getElementsByTagName("details")[0]
        title = str(self.readText(informationNode, "title"))
        description = str(self.readText(informationNode, "detail"))
        basename = self.readText(detailsNode, "basename")
        length = self.readText(detailsNode, "lengthSec")
        date = self.parseDate(self.readText(detailsNode, "airtime"))
        maxSize = 0
        for imageNode in xmlPage.getElementsByTagName("teaserimages")[0].getElementsByTagName("teaserimage"):
            match = self.regex_dimensions.search(imageNode.getAttribute("key"))
            size = int(match.group(1)) * int(match.group(2))
            if size > maxSize:
                maxSize = size
                imageLink = "http:" + imageNode.firstChild.data

        basenameLink = self.jsonService_Link % basename
        displayObject = DisplayObject(title, "", imageLink, description, basenameLink, "JsonLink", date, length)
        self.gui.buildVideoLink(displayObject, self, counter)

    def playVideoFromJsonLink(self, link):
        page = self.loadPage(link)
        jsonObject = json.loads(page)
        links = self.extractLinks(jsonObject["priorityList"])
        self.gui.play(links)

    def extractLinks(self, jsonList):
        links = {}
        for jsonListObject in jsonList:
            for formitaete in jsonListObject["formitaeten"]:
                for jsonObject in formitaete["qualities"]:
                    quality = jsonObject["quality"]
                    hd = jsonObject["hd"]
                    url = jsonObject["audio"]["tracks"][0]["uri"]
                    if "manifest.f4m" in url:
                        continue
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

    def searchVideo(self, searchText):
        self.buildPageMenu(self.searchLink % searchText, 0)

    def readText(self, node, textNode):
        try:
            node = node.getElementsByTagName(textNode)[0].firstChild
            return str(node.data)
        except:
            return ""

    def loadConfigXml(self, link):
        self.gui.log("load:" + link)
        xmlPage = self.loadPage(link)
        return minidom.parseString(xmlPage)

    def extractVideoObjects(self, rssFeed, initCount):
        nodes = rssFeed.getElementsByTagName("item")
        nodeCount = initCount + len(nodes)
        for itemNode in nodes:
            try:
                self.extractVideoInformation(itemNode, nodeCount)
            except:
                pass

    def parseDate(self, dateString):
        dateString = regex_dateString.search(dateString).group()
        for month in list(month_replacements.keys()):
            dateString = dateString.replace(month, month_replacements[month])
        return time.strptime(dateString, "%d.%m.%Y")

    def extractVideoInformation(self, itemNode, nodeCount):
        title = self.readText(itemNode, "title")
        self.gui.log(title)
        dateString = self.readText(itemNode, "pubDate")
        pubDate = self.parseDate(dateString)
        descriptionNode = itemNode.getElementsByTagName("description")[0].firstChild.data
        description = str(descriptionNode)
        picture = ""
        pictureNodes = itemNode.getElementsByTagName("media:thumbnail")
        if len(pictureNodes) > 0:
            picture = pictureNodes[0].getAttribute("url")
        links = {}
        for contentNode in itemNode.getElementsByTagName("media:content"):
            height = int(contentNode.getAttribute("height"))
            url = contentNode.getAttribute("url")
            size = int(contentNode.getAttribute("fileSize"))
            if height < 300:
                links[0] = SimpleLink(url, size)
            elif height < 480:
                links[1] = SimpleLink(url, size)
            else:
                links[2] = SimpleLink(url, size)
        if links:
            self.gui.buildVideoLink(DisplayObject(title, "", picture, description, links, True, pubDate), self, nodeCount)
