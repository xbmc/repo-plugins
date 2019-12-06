# -*- coding: utf-8 -*-
# Wakanim - Watch videos from the german anime platform Wakanim.tv on Kodi.
# Copyright (C) 2017 MrKrabat
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

import inputstreamhelper

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

from . import api
from . import view
from . import model
from . import controller


def main(argv):
    """Main function for the addon
    """
    args = model.parse(argv)

    # inputstream adaptive settings
    if hasattr(args, "mode") and args.mode == "mpd":
        is_helper = inputstreamhelper.Helper("mpd", drm="com.widevine.alpha")
        if is_helper.check_inputstream():
            xbmcaddon.Addon(id="inputstream.adaptive").openSettings()
        return True

    # get account informations
    username = args._addon.getSetting("wakanim_username")
    password = args._addon.getSetting("wakanim_password")

    # set country
    args._country = args._addon.getSetting("country")
    if args._country == "0":
        args._country = "de"
    elif args._country == "1":
        args._country = "fr"
    elif args._country == "2":
        args._country = "sc"
    elif args._country == "3":
        args._country = "ru"
    else:
        args._country = "de"

    if not (username and password):
        # open addon settings
        view.add_item(args, {"title": args._addon.getLocalizedString(30040)})
        view.endofdirectory(args)
        args._addon.openSettings()
        return False
    else:
        # list menue
        api.start(args)
        xbmcplugin.setContent(int(args._argv[1]), "tvshows")
        check_mode(args)
        api.close(args)


def check_mode(args):
    """Run mode-specific functions
    """
    if hasattr(args, "mode"):
        mode = args.mode
    elif hasattr(args, "id"):
        # call from other plugin
        mode = "videoplay"
        args.url = "/" + args._country + "/v2/catalogue/episode/" + args.id
    elif hasattr(args, "url"):
        # call from other plugin
        mode = "videoplay"
        args.url = args.url[22:]
    else:
        mode = None

    if not mode:
        showMainMenue(args)
    elif mode == "catalog":
        controller.showCatalog(args)
    elif mode == "last_episodes":
        controller.listLastEpisodes(args)
    elif mode == "last_simulcasts":
        controller.listLastSimulcasts(args)
    elif mode == "search":
        controller.searchAnime(args)
    elif mode == "watchlist":
        controller.myWatchlist(args)
    elif mode == "downloads":
        controller.myDownloads(args)
    elif mode == "collection":
        controller.myCollection(args)
    elif mode == "list_season":
        controller.listSeason(args)
    elif mode == "list_episodes":
        controller.listEpisodes(args)
    elif mode == "videoplay":
        controller.startplayback(args)
    elif mode == "trailer":
        item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"), path=args.url)
        xbmcplugin.setResolvedUrl(int(args._argv[1]), True, item)
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
    view.endofdirectory(args)
