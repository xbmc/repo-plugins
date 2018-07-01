# -*- coding: utf-8 -*-
# Steam Community
# Copyright (C) 2018 MrKrabat
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
        is_helper = inputstreamhelper.Helper("mpd")
        if is_helper.check_inputstream():
            xbmcaddon.Addon(id="inputstream.adaptive").openSettings()
        return True

    # get language
    language = {"0": "arabic", "1": "bulgarian", "2": "schinese", "3": "tchinese", "4": "czech", "5": "danish", "6": "dutch", "7": "english", "8": "finnish", "9": "french",
                "10": "german", "11": "greek", "12": "hungarian", "13": "italian", "14": "japanese", "15": "koreana", "16": "norwegian", "17": "polish", "18": "portuguese", "19": "brazilian",
                "20": "romanian", "21": "russian", "22": "spanish", "23": "swedish", "24": "thai", "25": "turkish", "26": "ukrainian"}
    args._lang = language[args._addon.getSetting("language")]
    #get sortorder
    sortorder = {"0": "trend", "1": "mostrecent"}
    args._filter = sortorder[args._addon.getSetting("filter")]

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
    else:
        mode = None

    if not mode:
        showMainMenue(args)

    elif mode == "search_hub":
        controller.searchHub(args)
    elif mode == "search_user":
        pass #controller.searchUser(args)

    elif mode == "viewhub":
        showHubMenue(args)

    elif mode == "screenshots":
        controller.viewScreenshots(args, getattr(args, "appid", None))
    elif mode == "artwork":
        controller.viewArtwork(args, getattr(args, "appid", None))
    elif mode == "broadcasts":
        controller.viewBroadcasts(args, getattr(args, "appid", None))
    elif mode == "videos":
        controller.viewVideos(args, getattr(args, "appid", None))

    elif mode == "imageplay":
        controller.startplayback_images(args)
    elif mode == "videoplay_broadcast":
        controller.startplayback_broadcast(args)
    elif mode == "videoplay_youtube":
        controller.startplayback_youtube(args)
    else:
        # unkown mode
        xbmc.log("[PLUGIN] %s: Failed in check_mode '%s'" % (args._addonname, str(mode)), xbmc.LOGERROR)
        xbmcgui.Dialog().notification(args._addonname, args._addon.getLocalizedString(30061), xbmcgui.NOTIFICATION_ERROR)
        showMainMenue(args)


def showMainMenue(args):
    """Show main menu
    """
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30040),
                   "mode":  "search_hub"})
    #view.add_item(args,
                  #{"title": args._addon.getLocalizedString(30041),
                   #"mode":  "search_user"})

    #view.add_item(args,
                  #{"title": args._addon.getLocalizedString(30050),
                   #"mode":  "all"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30051),
                   "mode":  "screenshots"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30052),
                   "mode":  "artwork"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30053),
                   "mode":  "broadcasts"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30054),
                   "mode":  "videos"})
    #view.add_item(args,
                  #{"title": args._addon.getLocalizedString(30055),
                   #"mode":  "workshop"})
    #view.add_item(args,
                  #{"title": args._addon.getLocalizedString(30056),
                   #"mode":  "news"})
    #view.add_item(args,
                  #{"title": args._addon.getLocalizedString(30057),
                   #"mode":  "guides"})
    #view.add_item(args,
                  #{"title": args._addon.getLocalizedString(30058),
                   #"mode":  "reviews"})
    view.endofdirectory(args)


def showHubMenue(args):
    """Show hub menu
    """
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30051),
                   "mode":  "screenshots",
                   "appid": args.appid})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30052),
                   "mode":  "artwork",
                   "appid": args.appid})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30053),
                   "mode":  "broadcasts",
                   "appid": args.appid})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30054),
                   "mode":  "videos",
                   "appid": args.appid})
    view.endofdirectory(args)
