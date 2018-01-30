# -*- coding: utf-8 -*-
# Akibapass - Watch videos from the german anime platform Akibapass.de on Kodi.
# Copyright (C) 2016 - 2017 MrKrabat
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys

import xbmc
import xbmcgui
import xbmcplugin

import cmdargs
import login
import netapi
import view


def main():
    """Main function for the addon
    """
    args = cmdargs.parse()

    # check if account is set
    username = args._addon.getSetting("akiba_username")
    password = args._addon.getSetting("akiba_password")

    if not (username and password):
        # open addon settings
        args._addon.openSettings()
        return False
    else:
        # login
        success = login.login(username, password, args)
        if success:
            # list menue
            xbmcplugin.setContent(int(sys.argv[1]), "tvshows")
            check_mode(args)
        else:
            # login failed
            xbmc.log("[PLUGIN] %s: Login failed" % args._addonname, xbmc.LOGERROR)
            xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30040))
            return False


def check_mode(args):
    """Run mode-specific functions
    """
    if hasattr(args, "mode"):
        mode = args.mode
    elif hasattr(args, "id"):
        # call from other plugin
        mode = "videoplay"
        args.url = "/de/v2/catalogue/episode/" + args.id
    elif hasattr(args, "url"):
        # call from other plugin
        mode = "videoplay"
        args.url = args.url[24:]
    else:
        mode = None

    if not mode:
        showMainMenue(args)
    elif mode == "catalog":
        netapi.showCatalog(args)
    elif mode == "last_episodes":
        netapi.listLastEpisodes(args)
    elif mode == "last_simulcasts":
        netapi.listLastSimulcasts(args)
    elif mode == "search":
        netapi.searchAnime(args)
    elif mode == "downloads":
        netapi.myDownloads(args)
    elif mode == "collection":
        netapi.myCollection(args)
    elif mode == "list_season":
        netapi.listSeason(args)
    elif mode == "list_episodes":
        netapi.listEpisodes(args)
    elif mode == "videoplay":
        netapi.startplayback(args)
    elif mode == "trailer":
        item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"), path=args.url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    else:
        # unkown mode
        xbmc.log("[PLUGIN] %s: Failed in check_mode '%s'" % (args._addonname, str(mode)), xbmc.LOGERROR)
        xbmcgui.Dialog().notification(args._addonname, args._addon.getLocalizedString(30041), xbmcgui.NOTIFICATION_ERROR)
        showMainMenue(args)


def showMainMenue(args):
    """Show main menu
    """
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30020),
                   "mode":   "catalog"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30025),
                   "mode":   "last_episodes"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30026),
                   "mode":   "last_simulcasts"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30021),
                   "mode":   "search"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30022),
                   "mode":   "downloads"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30023),
                   "mode":   "collection"})
    view.endofdirectory()
