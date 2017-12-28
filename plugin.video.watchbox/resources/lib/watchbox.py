# -*- coding: utf-8 -*-
# Watchbox
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
    username = args._addon.getSetting("watchbox_username")
    password = args._addon.getSetting("watchbox_password")

    if not (username and password):
        xbmcplugin.setContent(int(sys.argv[1]), "tvshows")
        check_mode(args)
    else:
        # login
        success = login.login(username, password, args)
        if success:
            # list menue
            args._login = True
            xbmcplugin.setContent(int(sys.argv[1]), "tvshows")
            check_mode(args)
        else:
            # login failed
            xbmc.log("[PLUGIN] %s: Login failed" % args._addonname, xbmc.LOGERROR)
            xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30042))

            xbmcplugin.setContent(int(sys.argv[1]), "tvshows")
            check_mode(args)


def check_mode(args):
    """Run mode-specific functions
    """
    if hasattr(args, "mode"):
        mode = args.mode
    elif hasattr(args, "id"):
        # call from other plugin
        mode = "videoplay"
        args.url = "https://www.watchbox.de/serien/test-" + args.id + "/"
    elif hasattr(args, "url"):
        # call from other plugin
        mode = "videoplay"
        args.url = args.url[23:]
    else:
        mode = None

    if not mode:
        showMainMenue(args)
    elif mode == "popular":
        netapi.genre_view(3, args)
    elif mode == "new":
        netapi.genre_view(4, args)
    elif mode == "genres":
        netapi.genres_show(args)
    elif mode == "genre_list":
        netapi.genre_list(args)
    elif mode == "genre_all":
        netapi.genre_view(0, args)
    elif mode == "genre_movie":
        netapi.genre_view(1, args)
    elif mode == "genre_tvshows":
        netapi.genre_view(2, args)
    elif mode == "genre_new":
        netapi.genre_view(5, args)
    elif mode == "season_list":
        netapi.season_list(args)
    elif mode == "episode_list":
        netapi.episode_list(args)
    elif mode == "search":
        netapi.search(args)
    elif mode == "videoplay":
        netapi.startplayback(args)
    elif mode == "login" and not args._login:
        # open addon settings
        args._addon.openSettings()
        return False
    elif mode == "login" and args._login:
        showMainMenue(args)
    elif mode == "mylist" and args._login:
        netapi.mylist(args)
    else:
        # unkown mode
        xbmc.log("[PLUGIN] %s: Failed in check_mode '%s'" % (args._addonname, str(mode)), xbmc.LOGERROR)
        xbmcgui.Dialog().notification(args._addonname, args._addon.getLocalizedString(30041), xbmcgui.NOTIFICATION_ERROR)
        showMainMenue(args)


def showMainMenue(args):
    """Show main menu
    """
    if args._login:
        view.add_item(args,
                      {"title": args._addon.getLocalizedString(30028),
                       "mode":  "mylist"})
    else:
        view.add_item(args,
                      {"title": args._addon.getLocalizedString(30029),
                       "mode":   "login"})

    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30026),
                   "mode":  "popular"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30027),
                   "mode":  "new"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30020),
                   "mode":  "genres"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30021),
                   "mode":  "search"})
    view.endofdirectory()
