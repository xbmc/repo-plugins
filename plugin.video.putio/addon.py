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

import json
import time

import requests

import sys
import xbmcaddon as xa
import xbmcgui
from resources.lib.common import PutioApiHandler
from resources.lib.exceptions import PutioAuthFailureException
from resources.lib.gui import play, populateDir

PLUGIN_ID = "plugin.video.putio"

pluginUrl = sys.argv[0]
pluginId = int(sys.argv[1])
itemId = sys.argv[2].lstrip("?")
addon = xa.Addon(PLUGIN_ID)


# Main program
def main():
    putio = PutioApiHandler(addon.getAddonInfo("id"))

    if itemId:
        item = putio.getItem(itemId)

        if item.content_type:
            if item.content_type == "application/x-directory":
                populateDir(pluginUrl, pluginId, putio.getFolderListing(itemId))
            else:
                play(item, putio.getSubtitle(item))
    else:
        populateDir(pluginUrl, pluginId, putio.getRootListing())

try:
    main()
except PutioAuthFailureException as e:
    addonid = addon.getAddonInfo("id")
    addon = xa.Addon(addonid)
    r = requests.get("https://put.io/xbmc/getuniqueid")
    o = json.loads(r.content)
    uniqueid = o['id']
    oauthtoken = addon.getSetting('oauthkey')

    if not oauthtoken:
        dialog = xbmcgui.Dialog()
        dialog.ok(
            "Oauth2 Key Required",
            "Visit put.io/xbmc and enter this code: %s\nthen press OK." % uniqueid
        )

    while not oauthtoken:
        try:
            # now we'll try getting oauth key by giving our uniqueid
            r = requests.get("http://put.io/xbmc/k/%s" % uniqueid)
            o = json.loads(r.content)
            oauthtoken = o['oauthtoken']

            if oauthtoken:
                addon.setSetting("oauthkey", str(oauthtoken))
                main()
        except Exception as e:
            dialog = xbmcgui.Dialog()
            dialog.ok("Oauth Key Error", str(e))

            raise e

        time.sleep(1)
