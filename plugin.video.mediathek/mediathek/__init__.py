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
import socket
import requests

socket.setdefaulttimeout(1)


class SimpleLink(object):
    def __init__(self, basePath, size):
        self.basePath = basePath
        self.size = size


class ComplexLink(object):
    def __init__(self, basePath, playPath, size):
        self.basePath = basePath
        self.playPath = playPath
        self.size = size


class TreeNode(object):
    def __init__(self, path, name, link, displayElements, childNodes=None):
        if childNodes is None:
            childNodes = []
        self.name = name
        self.path = path
        self.link = link
        self.displayElements = displayElements
        self.childNodes = childNodes


class DisplayObject(object):
    def __init__(self, title, subTitle, picture, description, link=None, isPlayable=True, date=None, duration=None):
        if link is None:
            link = []
        self.title = title
        self.subTitle = subTitle
        self.link = link
        self.picture = picture
        self.isPlayable = isPlayable
        self.description = description
        self.date = date
        self.duration = duration


class Mediathek(object):
    def loadPage(self, url, values=None, maxTimeout=None):
        safe_url = url.replace(" ", "%20").replace("&amp;", "&")
        self.gui.log("download %s" % safe_url)
        content = requests.get(safe_url, allow_redirects=True)
        return content.text;
        #if content.encoding is not None:
        #    return content.text.encode(content.encoding)
        #else:
        #    return content.text

    def buildMenu(self, path, treeNode=None):
        if isinstance(path, (str, bytes)):
            path = path.split('.')
        if len(path) > 0:
            index = int(path.pop(0))

            if treeNode is None:
                treeNode = self.menuTree[index]
            else:
                treeNode = treeNode.childNodes[index]
            self.buildMenu(path, treeNode)
        else:
            if treeNode is None:
                treeNode = self.menuTree[0]
            self.gui.log(treeNode.name)
            for childNode in treeNode.childNodes:
                self.gui.buildMenuLink(childNode, self, len(treeNode.childNodes))
            if treeNode.displayElements:
                self.buildPageMenu(treeNode.link, len(treeNode.childNodes))

    def displayCategories(self):
        if len(self.menuTree) > 1 or not self.menuTree[0].displayElements:
            for treeNode in self.menuTree:
                self.gui.buildMenuLink(treeNode, self, len(self.menuTree))
        else:
            self.buildPageMenu(self.menuTree[0].link, 0)

    def walkJson(self, path, jsonObject):
        path = path.split('.')
        i = 0
        while i < len(path):
            if isinstance(jsonObject, list):
                index = int(path.pop(0))
            else:
                index = path.pop(0)
            jsonObject = jsonObject[index]

        return jsonObject
