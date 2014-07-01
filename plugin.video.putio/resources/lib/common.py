# coding: utf-8
#
# put.io xbmc addon
# Copyright (C) 2009  Alper Kanat <tunix@raptiye.org>
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import os

import putio
import xbmc
import xbmcaddon as xa
from exceptions import PutioAuthFailureException


class PutioApiHandler(object):
    """
    Class to handle putio api calls for XBMC actions

    """

    subtitleTypes = ("srt", "sub")

    def __init__(self, pluginId):
        self.addon = xa.Addon(pluginId)
        self.oauthkey = self.addon.getSetting("oauthkey").replace('-', '')

        if not self.oauthkey:
            raise PutioAuthFailureException(
                self.addon.getLocalizedString(30001),
                self.addon.getLocalizedString(30002)
            )

        self.apiclient = putio.Client(self.oauthkey)

    def getItem(self, itemId):
        return self.apiclient.File.GET(itemId)

    def getRootListing(self):
        items = []

        for item in self.apiclient.File.list(parent_id=0):
            items.append(item)

        return items

    def getFolderListing(self, folderId):
        items = []

        for item in self.apiclient.File.list(parent_id=folderId):
            items.append(item)

        return items

    def getSubtitle(self, item):
        subtitles = item.subtitle
        default = subtitles.get("default")

        if not default:
            print "Couldn't find any subtitles for: %s" % item.name
            return

        print "Found subtitle for %s, retrieving.." % item.name

        r = item.client.request(
            '/files/%s/subtitles/%s' % (
                item.id,
                default
            ),
            raw=True
        )
        dest = xbmc.translatePath('special://temp/%s' % item.name)

        with open(dest, 'wb') as f:
            for data in r.iter_content():
                f.write(data)

        return dest
