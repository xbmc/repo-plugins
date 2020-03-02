# -*- coding: utf-8 -*-
# -------------LicenseHeader--------------
# plugin.video.mediathek - display german mediathekes
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
import os
import re
import sys
import time
import urllib
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin


from bs4 import BeautifulSoup
import json
import hashlib
from mediathek import ComplexLink
from mediathek.factory import MediathekFactory

regex_findLink = re.compile("mms://[^\"]*wmv")

__plugin__ = "Mediathek"

settings = xbmcaddon.Addon(id='plugin.video.mediathek')
translation = settings.getLocalizedString


class SimpleXbmcGui(object):
    def __init__(self, settings):
        self.__addon_handle = int(sys.argv[1])
        self.__addon_name = 'plugin.video.mediathek'
        xbmcplugin.setContent(self.__addon_handle, 'tvshows')
        self.settings = xbmcaddon.Addon(id='plugin.video.mediathek')
        self.quality = int(xbmcplugin.getSetting(int(sys.argv[1]), "quality"))
        self.preferedStreamTyp = int(xbmcplugin.getSetting(int(sys.argv[1]), "preferedStreamType"))
        self.log("quality: %s" % self.quality)
        self.plugin_profile_dir = xbmc.translatePath(settings.getAddonInfo("profile"))
        if not os.path.exists(self.plugin_profile_dir):
            os.mkdir(self.plugin_profile_dir)

    def log(self, msg):
        if not isinstance(msg, (bytes, str)):
            xbmc.log("[%s]: %s" % (__plugin__, type(msg)))
        else:
            xbmc.log("[%s]: %s" % (__plugin__, msg.encode('utf8')))

    def buildVideoLink(self, displayObject, mediathek, objectCount):
        metaData = self.BuildMetaData(displayObject)
        if displayObject.picture is not None:
            listItem = xbmcgui.ListItem(metaData["title"], iconImage="DefaultFolder.png", thumbnailImage=displayObject.picture)
        else:
            listItem = xbmcgui.ListItem(metaData["title"], iconImage="DefaultFolder.png")
        listItem.setInfo("Video", metaData)
        listItem.setInfo("video", metaData)

        if displayObject.isPlayable:
            if displayObject.isPlayable == "PlayList":
                link = displayObject.link[0]
                url = "%s?type=%s&action=openPlayList&link=%s" % (sys.argv[0], mediathek.name(), urllib.parse.quote_plus(link.basePath))
                listItem.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listItem, False, objectCount)
            elif displayObject.isPlayable == "JsonLink":
                link = displayObject.link
                url = "%s?type=%s&action=openJsonLink&link=%s" % (sys.argv[0], mediathek.name(), urllib.parse.quote_plus(link))
                listItem.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listItem, False, objectCount)
            else:
                if(len(displayObject.link) > 0):
                  link = self.extractLink(displayObject.link)
                  if isinstance(link, ComplexLink):
                      self.log("PlayPath:" + link.playPath)
                      listItem.setProperty("PlayPath", link.playPath)
                  listItem.setProperty('IsPlayable', 'true')
                  xbmcplugin.addDirectoryItem(int(sys.argv[1]), link.basePath, listItem, False, objectCount)
        else:
            listItem.setIsFolder(True)
            try:
                url = "%s?type=%s&action=openTopicPage&link=%s" % (sys.argv[0], mediathek.name(), urllib.parse.quote_plus(displayObject.link))
            except:
                url = "%s?type=%s&action=openTopicPage&link=%s" % (sys.argv[0], mediathek.name(), urllib.parse.quote_plus(displayObject.link.encode('utf-8')))
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listItem, True, objectCount)

    def BuildMetaData(self, displayObject):
        if displayObject.subTitle is None or displayObject.subTitle == "" or displayObject.subTitle == displayObject.title:
            title = self.transformHtmlCodes(displayObject.title.rstrip())
        else:
            title = self.transformHtmlCodes(displayObject.title.rstrip() + " - " + displayObject.subTitle.rstrip())
        if displayObject.date is not None:
            title = "(%s) %s" % (time.strftime("%d.%m", displayObject.date), title.rstrip())

        metaData = {
            "mediatype": "video",
            "title": title,
            "plotoutline": self.transformHtmlCodes(displayObject.description)
        }

        if displayObject.duration is not None:
            metaData["duration"] = int(displayObject.duration)

        if displayObject.date is not None:
            metaData["date"] = time.strftime("%Y-%m-%d", displayObject.date)
            metaData["year"] = int(time.strftime("%Y", displayObject.date))
        return metaData

    def transformHtmlCodes(self, content):
        return BeautifulSoup(content, "html.parser").prettify(formatter=None)

    def buildMenuLink(self, menuObject, mediathek, objectCount):
        title = menuObject.name
        listItem = xbmcgui.ListItem(title, iconImage="DefaultFolder.png")
        url = "%s?type=%s&action=openMenu&path=%s" % (sys.argv[0], mediathek.name(), menuObject.path)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listItem, isFolder=True, totalItems=objectCount)

    def storeJsonFile(self, jsonObject, additionalIdentifier=None):
        hashGenerator = hashlib.md5()
        hashGenerator.update(str(sys.argv[2]).encode('utf-8'))
        if additionalIdentifier is not None:
            hashGenerator.update(additionalIdentifier)
        callhash = hashGenerator.hexdigest()
        storedJsonFile = os.path.join(self.plugin_profile_dir, "%s.json" % callhash)
        with open(storedJsonFile, 'w') as output:
            json.dump(jsonObject, output)
        return callhash

    def loadJsonFile(self, callhash):
        storedJsonFile = os.path.join(self.plugin_profile_dir, "%s.json" % callhash)
        with open(storedJsonFile, "rb") as input:
            return json.load(input)

    def buildJsonLink(self, mediathek, title, jsonPath, callhash, objectCount):
        listItem = xbmcgui.ListItem(title, iconImage="DefaultFolder.png")
        url = "%s?type=%s&action=openJsonPath&path=%s&callhash=%s" % (sys.argv[0], mediathek.name(), jsonPath, callhash)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listItem, isFolder=True, totalItems=objectCount)

    def listAvailableMediathekes(self, mediathekNames):
        rootPath = os.path.join(self.settings.getAddonInfo('path'), "resources/logos/png/")
        for name in mediathekNames:
            listItem = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=os.path.join(rootPath, name + ".png"))
            url = "%s?type=%s" % (sys.argv[0], name)
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listItem, isFolder=True)

    def getParams(self):
        paramDict = {}
        try:
            if sys.argv[2]:
                paramPairs = sys.argv[2][1:].split("&")
                for paramsPair in paramPairs:
                    paramSplits = paramsPair.split('=')
                    if (len(paramSplits)) == 2:
                        paramDict[paramSplits[0]] = paramSplits[1]
        except:
            errorOK()
        return paramDict

    def renderMenu(self):
        progress = xbmcgui.DialogProgress()
        params = self.getParams();
        mediathekName = params.get("type", "")
        action = params.get("action", "")



        self.log("Quality: %s" % self.quality)
        self.log("argv[0]: %s" % sys.argv[0])
        self.log("argv[1]: %s" % sys.argv[1])
        factory = MediathekFactory()

        if mediathekName == "":
            if action == "":
                self.addSearchButton(None)
                self.listAvailableMediathekes(factory.getAvaibleMediathekTypes())
            else:
                result = self.keyboardInput()
                if result.isConfirmed():
                    searchText = str(result.getText())
                    for name in factory.getAvaibleMediathekTypes():
                        mediathek = factory.getMediathek(name, self)
                        if mediathek.isSearchable():
                            mediathek.searchVideo(searchText)
                else:
                    self.back()

        else:
            cat = int(params.get("cat", 0))
            mediathek = factory.getMediathek(mediathekName, self)

            if action == "openTopicPage":
                link = urllib.parse.unquote_plus(params.get("link", ""))
                self.log(link)
                mediathek.buildPageMenu(link, 0)
            elif action == "openPlayList":
                link = urllib.parse.unquote_plus(params.get("link", ""))
                self.log(link)
                remotePlaylist = mediathek.loadPage(link)
                self.playPlaylist(remotePlaylist)
            elif action == "openMenu":
                path = params.get("path", "0")
                mediathek.buildMenu(path)
            elif action == "search":
                result = self.keyboardInput()
                if result.isConfirmed():
                    searchText = str(result.getText())
                    mediathek.searchVideo(searchText)
                else:
                    self.back()
            elif action == "openJsonPath":
                path = params.get("path", "0")
                callhash = params.get("callhash", "0")
                mediathek.buildJsonMenu(path, callhash, 0)
            elif action == "openJsonLink":
                link = urllib.parse.unquote_plus(params.get("link", ""))
                mediathek.playVideoFromJsonLink(link)
            else:
                if mediathek.isSearchable():
                    self.addSearchButton(mediathek)
                mediathek.displayCategories()
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def getHomeDir(self):
        return self.settings.getAddonInfo("profile")

    def back(self):
        xbmc.executebuiltin("Action(PreviousMenu)")

    def keyboardInput(self):
        keyboard = xbmc.Keyboard("")
        keyboard.doModal()
        return keyboard

    def addSearchButton(self, mediathek):
        title = translation(30100)
        listItem = xbmcgui.ListItem(title, iconImage="DefaultFolder.png")
        if mediathek is not None:
            url = "%s?type=%s&action=search" % (sys.argv[0], mediathek.name())
        else:
            url = "%s?action=search" % (sys.argv[0])
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listItem, isFolder=True)

    def readText(self, node, textNode):
        try:
            node = node.getElementsByTagName(textNode)[0].firstChild
            return str(node.data)
        except:
            return ""

    def playPlaylist(self, remotePlaylist):
        player = xbmc.Player()

        playerItem = xbmcgui.ListItem(remotePlaylist)
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        for link in regex_findLink.findall(remotePlaylist):
            listItem = xbmcgui.ListItem(link)
            listItem.setProperty("PlayPath", link)
            playlist.add(url=link, listitem=listItem)

        player.play(playlist, playerItem, False)

    def errorOK(self, title="", msg=""):
        e = str(sys.exc_info()[1])
        self.log(e)
        if not title:
            title = __plugin__
        if not msg:
            msg = "ERROR!"
        if e is None:
            xbmcgui.Dialog().ok(title, msg, e)
        else:
            xbmcgui.Dialog().ok(title, msg)

    def play(self, links):
        link = self.extractLink(links)
        listItem = xbmcgui.ListItem(path=link.basePath)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=listItem)

    def extractLink(self, links):
        if self.quality in links:
            return links[self.quality]
        else:
            selectedKey = -1
            keys = list(links.keys())
            for key in keys:
                if self.quality > key > selectedKey:
                    selectedKey = key
            if selectedKey > -1:
                return links[selectedKey]
            else:
                selectedKey = keys[0]
                for key in keys:
                    if key < selectedKey:
                        selectedKey = key
                return links[selectedKey]
