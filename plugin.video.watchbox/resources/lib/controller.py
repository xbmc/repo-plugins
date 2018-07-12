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

import re
import json
from bs4 import BeautifulSoup
try:
    from urllib import quote_plus
except ImportError:
    from urllib.parse import quote_plus

import xbmc
import xbmcgui
import xbmcplugin

from . import api
from . import view


def genres_show(args):
    """Show all genres
    """
    # get website
    html = api.getPage(args, "https://www.watchbox.de/genres/")
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30040)})
        view.endofdirectory(args)
        return

    # parse html
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", {"class": "grid_genres_b"})

    # for every list entry
    for item in div.find_all("section"):
        # add to view
        view.add_item(args,
                      {"url":   item.a["href"],
                       "title": item.find("div", {"class": "text_browse-teaser-title"}).string.strip(),
                       "mode":  "genre_list",
                       "genre": item.find("div", {"class": "text_browse-teaser-title"}).string.strip(),
                       "plot":  item.find("div", {"class": "text_browse-teaser-subtitle"}).string.strip()},
                      isFolder=True, mediatype="video")

    view.endofdirectory(args)


def genre_list(args):
    """List options for gernre
    """
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30022),
                   "url":   args.url,
                   "mode":  "genre_all"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30023),
                   "url":   args.url,
                   "mode":  "genre_movie"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30024),
                   "url":   args.url,
                   "mode":  "genre_tvshows"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30030),
                   "url":   args.url,
                   "mode":  "genre_all"})
    view.add_item(args,
                  {"title": args._addon.getLocalizedString(30031),
                   "url":   args.url,
                   "mode":  "genre_new"})
    view.endofdirectory(args)


def genre_view(mode, args):
    """Show all tv shows / movies
    """
    # item offset
    url = ""
    if hasattr(args, "offset"):
        url = "?page=" + str(args.offset)

    # get website
    if mode == 1:
        html = api.getPage(args, "https://www.watchbox.de" + args.url + "filme/" + url)
    elif mode == 2:
        html = api.getPage(args, "https://www.watchbox.de" + args.url + "serien/" + url)
    elif mode == 3:
        html = api.getPage(args, "https://www.watchbox.de/beste/" + url)
    elif mode == 4:
        html = api.getPage(args, "https://www.watchbox.de/neu/" + url)
    elif mode == 5:
        html = api.getPage(args, "https://www.watchbox.de" + args.url + "neu/" + url)
    else:
        html = api.getPage(args, "https://www.watchbox.de" + args.url + "beste/" + url)

    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30040)})
        view.endofdirectory(args)
        return

    # parse html
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", {"class": "teaser-pagination__page"})

    # for every list entry
    for item in div.find_all("section"):
        # get values
        try:
            meta = item.find("div", {"class": "text_teaser-portrait-meta"}).string.strip()
            duration, _, year, _ = meta.split("|")
            duration = duration.strip()[:-5]
            duration = str(int(duration) * 60)
            year = year.strip()
        except (TypeError, ValueError):
            duration = ""
            year = ""
        thumb = item.img["src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        if (mode == 1) or (".html" in item.a["href"]):
            # add movie to view
            view.add_item(args,
                          {"url":      item.a["href"],
                           "title":    item.find("div", {"class": "text_teaser-portrait-title"}).string.strip(),
                           "mode":     "videoplay",
                           "thumb":    thumb,
                           "fanart":   thumb,
                           "year":     year,
                           "duration": duration,
                           "plot":     item.find("div", {"class": "text_teaser-portrait-description"}).string.strip()},
                          isFolder=False, mediatype="video")
        else:
            # add series to view
            view.add_item(args,
                          {"url":      item.a["href"],
                           "title":    item.find("div", {"class": "text_teaser-portrait-title"}).string.strip(),
                           "mode":     "season_list",
                           "thumb":    thumb,
                           "fanart":   thumb,
                           "year":     year,
                           "duration": duration,
                           "plot":     item.find("div", {"class": "text_teaser-portrait-description"}).string.strip()},
                          isFolder=True, mediatype="video")

    # show me more
    if u"<span>Zeig mir mehr</span>" in html:
        view.add_item(args,
                      {"title":  args._addon.getLocalizedString(30025),
                       "url":    getattr(args, "url", ""),
                       "offset": str(int(getattr(args, "offset", 0)) + 1),
                       "mode":   args.mode})

    view.endofdirectory(args)


def mylist(args):
    """Show my list
    """
    # get website
    html = api.getPage(args, "https://www.watchbox.de/meine-liste")
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30040)})
        view.endofdirectory(args)
        return

    # parse html
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", {"class": "grid"})

    # for every list entry
    for item in div.find_all("section"):
        # get values
        try:
            meta = item.find("div", {"class": "text_teaser-portrait-meta"}).string.strip()
            _, year, _ = meta.split("|")
            year = year.strip()
        except (TypeError, ValueError):
            year = ""
        thumb = item.img["src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        if ".html" in item.a["href"]:
            # add movie to view
            view.add_item(args,
                          {"url":    item.a["href"],
                           "title":  item.find("div", {"class": "text_teaser-portrait-title"}).string.strip(),
                           "mode":   "videoplay",
                           "thumb":  thumb,
                           "fanart": thumb,
                           "year":   year,
                           "plot":   item.find("div", {"class": "text_teaser-portrait-description"}).string.strip()},
                          isFolder=False, mediatype="video")
        else:
            # add series to view
            view.add_item(args,
                          {"url":    item.a["href"],
                           "title":  item.find("div", {"class": "text_teaser-portrait-title"}).string.strip(),
                           "mode":   "season_list",
                           "thumb":  thumb,
                           "fanart": thumb,
                           "year":   year,
                           "plot":   item.find("div", {"class": "text_teaser-portrait-description"}).string.strip()},
                          isFolder=True, mediatype="video")

    view.endofdirectory(args)


def season_list(args):
    """Show all seasons
    """
    # get website
    html = api.getPage(args, "https://www.watchbox.de" + args.url)
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30040)})
        view.endofdirectory(args)
        return

    # parse html
    soup = BeautifulSoup(html, "html.parser")
    ul = soup.find("ul", {"class": "season-panel"})
    if not ul:
        view.add_item(args, {"title": args._addon.getLocalizedString(30040)})
        view.endofdirectory(args)
        return

    # get values
    try:
        plot = soup.find("p", {"class": "more-text"})
        plot.span.decompose()
    except AttributeError:
        pass

    # for every list entry
    for item in ul.find_all("li"):
        # add to view
        view.add_item(args,
                      {"url":         item.a["href"],
                       "title":       item.a.string.strip(),
                       "thumb":       args.thumb,
                       "fanart":      args.fanart,
                       "plot":        plot.get_text().strip(),
                       "plotoutline": args.plot,
                       "mode":        "episode_list"},
                      isFolder=True, mediatype="video")

    view.endofdirectory(args)


def episode_list(args):
    """Show all episodes
    """
    # get website
    html = api.getPage(args, "https://www.watchbox.de" + args.url)
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30040)})
        view.endofdirectory(args)
        return

    # parse html
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", {"class": "swiper-wrapper"})
    if not div:
        view.add_item(args, {"title": args._addon.getLocalizedString(30040)})
        view.endofdirectory(args)
        return

    # for every list entry
    for item in div.find_all("section"):
        # get values
        episode = item.find("div", {"class": "teaser__season-info"}).string.strip()
        matches = re.findall(r"([0-9]{1,3})", episode)
        thumb = item.img["data-src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        if not len(matches) == 2:
            # no episode informations given
            view.add_item(args,
                          {"url":      item.a["href"],
                           "title":    item.find("div", {"class": "text_teaser-landscape-title"}).string.strip(),
                           "thumb":    thumb,
                           "fanart":   args.fanart,
                           "duration": getattr(args, "duration", ""),
                           "mode":     "videoplay"},
                          isFolder=False, mediatype="video")
        else:
            # episode informations given
            view.add_item(args,
                          {"url":      item.a["href"],
                           "title":    matches[1] + " - " + item.find("div", {"class": "text_teaser-landscape-title"}).string.strip(),
                           "thumb":    thumb,
                           "fanart":   args.fanart,
                           "episode":  matches[1],
                           "season":   matches[0],
                           "duration": getattr(args, "duration", ""),
                           "mode":     "videoplay"},
                          isFolder=False, mediatype="video")

    view.endofdirectory(args)


def search(args):
    """Search function
    """
    # ask for search string
    d = xbmcgui.Dialog().input(args._addon.getLocalizedString(30021), type=xbmcgui.INPUT_ALPHANUM)
    if not d or len(d) < 2:
        return

    # get website
    html = api.getPage(args, "https://api.watchbox.de/v1/search/?page=1&maxPerPage=28&active=true&term=" + quote_plus(d))
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30040)})
        view.endofdirectory(args)
        return

    # parse json
    json_obj = json.loads(html)

    # for every list entry
    for item in json_obj["items"]:
        if str(item["type"]) == "film":
            # add movie to view
            view.add_item(args,
                          {"url":         "/serien/test-" + str(item["entityId"]) + "/",
                           "title":       item["headline"],
                           "mode":        "videoplay",
                           "thumb":       "https://aiswatchbox-a.akamaihd.net/watchbox/format/" + str(item["entityId"]) + "_dvdcover/600x840/test.jpg",
                           "fanart":      "https://aiswatchbox-a.akamaihd.net/watchbox/format/" + str(item["entityId"]) + "_dvdcover/600x840/test.jpg",
                           "year":        item["productionYear"],
                           "genre":       item["genres"][0],
                           "plot":        item["description"],
                           "plotoutline": item["infoTextShort"]},
                          isFolder=False, mediatype="video")
        else:
            # add series to view
            view.add_item(args,
                          {"url":         "/serien/test-" + str(item["entityId"]) + "/",
                           "title":       item["headline"],
                           "mode":        "season_list",
                           "thumb":       "https://aiswatchbox-a.akamaihd.net/watchbox/format/" + str(item["entityId"]) + "_dvdcover/600x840/test.jpg",
                           "fanart":      "https://aiswatchbox-a.akamaihd.net/watchbox/format/" + str(item["entityId"]) + "_dvdcover/600x840/test.jpg",
                           "year":        item["productionYear"],
                           "genre":       item["genres"][0],
                           "plot":        item["description"],
                           "plotoutline": item["infoTextShort"]},
                          isFolder=True, mediatype="video")

    view.endofdirectory(args)


def startplayback(args):
    """Plays a video
    """
    # get website
    html = api.getPage(args, "https://www.watchbox.de" + args.url)
    if not html:
        item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"))
        xbmcplugin.setResolvedUrl(int(args._argv[1]), False, item)
        return

    # parse html
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", {"id": "player"})
    if not div:
        item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"))
        xbmcplugin.setResolvedUrl(int(args._argv[1]), False, item)
        return

    # parse json
    json_obj = json.loads(div["data-player-conf"])

    if "source" in json_obj and "hls" in json_obj["source"]:
        # play stream
        item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"), path=json_obj["source"]["hls"] + api.getCookies(args))
        item.setMimeType("application/vnd.apple.mpegurl")
        item.setContentLookup(False)
        xbmcplugin.setResolvedUrl(int(args._argv[1]), True, item)
    else:
        xbmc.log("[PLUGIN] %s: Failed to play stream" % args._addonname, xbmc.LOGERROR)
        xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30041))
