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
import sys
import json
import urllib
import urllib2
from bs4 import BeautifulSoup

import xbmc
import xbmcgui
import xbmcplugin

import login
import view


def genres_show(args):
    """Show all genres
    """
    response = urllib2.urlopen("https://www.watchbox.de/genres/")
    html = response.read()

    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", {"class": "grid_genres_b"})

    for item in div.find_all("section"):
        view.add_item(args,
                      {"url":   item.a["href"],
                       "title": item.find("div", {"class": "text_browse-teaser-title"}).string.strip().encode("utf-8"),
                       "mode":  "genre_list",
                       "genre": item.find("div", {"class": "text_browse-teaser-title"}).string.strip().encode("utf-8"),
                       "plot":  item.find("div", {"class": "text_browse-teaser-subtitle"}).string.strip().encode("utf-8")},
                      isFolder=True, mediatype="video")

    view.endofdirectory()


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
    view.endofdirectory()


def genre_view(mode, args):
    """Show all tv shows / movies
    """
    url = ""
    if hasattr(args, "offset"):
        url = "?page=" + str(args.offset)

    if mode == 1:
        response = urllib2.urlopen("https://www.watchbox.de" + args.url + "filme/" + url)
    elif mode == 2:
        response = urllib2.urlopen("https://www.watchbox.de" + args.url + "serien/" + url)
    elif mode == 3:
        response = urllib2.urlopen("https://www.watchbox.de/beste/" + url)
    elif mode == 4:
        response = urllib2.urlopen("https://www.watchbox.de/neu/" + url)
    elif mode == 5:
        response = urllib2.urlopen("https://www.watchbox.de" + args.url + "neu/" + url)
    else:
        response = urllib2.urlopen("https://www.watchbox.de" + args.url + "beste/" + url)

    html = response.read()

    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", {"class": "teaser-pagination__page"})

    for item in div.find_all("section"):
        try:
            meta = item.find("div", {"class": "text_teaser-portrait-meta"}).string.strip().encode("utf-8")
            duration, country, year, fsk = meta.split("|")
            duration = duration.strip()[:-5]
            duration = str(int(duration) * 60)
            year = year.strip()
        except TypeError:
            duration = ""
            year = ""
        thumb = item.img["src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        if (mode == 1) or (".html" in item.a["href"]):
            view.add_item(args,
                          {"url":      item.a["href"],
                           "title":    item.find("div", {"class": "text_teaser-portrait-title"}).string.strip().encode("utf-8"),
                           "mode":     "videoplay",
                           "thumb":    thumb,
                           "fanart":   thumb,
                           "year":     year,
                           "duration": duration,
                           "plot":     item.find("div", {"class": "text_teaser-portrait-description"}).string.strip().encode("utf-8")},
                          isFolder=False, mediatype="video")
        else:
            view.add_item(args,
                          {"url":      item.a["href"],
                           "title":    item.find("div", {"class": "text_teaser-portrait-title"}).string.strip().encode("utf-8"),
                           "mode":     "season_list",
                           "thumb":    thumb,
                           "fanart":   thumb,
                           "year":     year,
                           "duration": duration,
                           "plot":     item.find("div", {"class": "text_teaser-portrait-description"}).string.strip().encode("utf-8")},
                          isFolder=True, mediatype="video")

    if "<span>Zeig mir mehr</span>" in html:
        view.add_item(args,
                      {"title":  args._addon.getLocalizedString(30025).encode("utf-8"),
                       "url":    getattr(args, "url", ""),
                       "offset": str(int(getattr(args, "offset", 0)) + 1),
                       "mode":   args.mode})

    view.endofdirectory()


def mylist(args):
    """Show my list
    """
    response = urllib2.urlopen("https://www.watchbox.de/meine-liste")
    html = response.read()

    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", {"class": "grid"})

    for item in div.find_all("section"):
        try:
            meta = item.find("div", {"class": "text_teaser-portrait-meta"}).string.strip().encode("utf-8")
            country, year, fsk = meta.split("|")
            year = year.strip()
        except TypeError:
            year = ""
        thumb = item.img["src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        if ".html" in item.a["href"]:
            view.add_item(args,
                          {"url":    item.a["href"],
                           "title":  item.find("div", {"class": "text_teaser-portrait-title"}).string.strip().encode("utf-8"),
                           "mode":   "videoplay",
                           "thumb":  thumb,
                           "fanart": thumb,
                           "year":   year,
                           "plot":   item.find("div", {"class": "text_teaser-portrait-description"}).string.strip().encode("utf-8")},
                          isFolder=False, mediatype="video")
        else:
            view.add_item(args,
                          {"url":    item.a["href"],
                           "title":  item.find("div", {"class": "text_teaser-portrait-title"}).string.strip().encode("utf-8"),
                           "mode":   "season_list",
                           "thumb":  thumb,
                           "fanart": thumb,
                           "year":   year,
                           "plot":   item.find("div", {"class": "text_teaser-portrait-description"}).string.strip().encode("utf-8")},
                          isFolder=True, mediatype="video")

    view.endofdirectory()


def season_list(args):
    """Show all seasons
    """
    response = urllib2.urlopen("https://www.watchbox.de" + args.url)
    html = response.read()

    soup = BeautifulSoup(html, "html.parser")
    ul = soup.find("ul", {"class": "season-panel"})
    if not ul:
        view.endofdirectory()
        return
    try:
        plot = soup.find("p", {"class": "more-text"})
        plot.span.decompose()
    except AttributeError:
        pass

    for item in ul.find_all("li"):
        view.add_item(args,
                      {"url":         item.a["href"],
                       "title":       item.a.string.strip().encode("utf-8"),
                       "thumb":       args.thumb,
                       "fanart":      args.fanart,
                       "plot":        plot.get_text().strip().encode("utf-8"),
                       "plotoutline": args.plot,
                       "mode":        "episode_list"},
                      isFolder=True, mediatype="video")

    view.endofdirectory()


def episode_list(args):
    """Show all episodes
    """
    response = urllib2.urlopen("https://www.watchbox.de" + args.url)
    html = response.read()

    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", {"class": "swiper-wrapper"})
    if not div:
        view.endofdirectory()
        return

    for item in div.find_all("section"):
        episode = item.find("div", {"class": "teaser__season-info"}).string.strip().encode("utf-8")
        matches = re.findall(r"([0-9]{1,3})", episode)
        thumb = item.img["data-src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        if not len(matches) == 2:
            view.add_item(args,
                          {"url":      item.a["href"],
                           "title":    item.find("div", {"class": "text_teaser-landscape-title"}).string.strip().encode("utf-8"),
                           "thumb":    thumb,
                           "fanart":   args.fanart,
                           "duration": getattr(args, "duration", ""),
                           "mode":     "videoplay"},
                          isFolder=False, mediatype="video")
        else:
            view.add_item(args,
                          {"url":      item.a["href"],
                           "title":    matches[1] + " - " + item.find("div", {"class": "text_teaser-landscape-title"}).string.strip().encode("utf-8"),
                           "thumb":    thumb,
                           "fanart":   args.fanart,
                           "episode":  matches[1],
                           "season":   matches[0],
                           "duration": getattr(args, "duration", ""),
                           "mode":     "videoplay"},
                          isFolder=False, mediatype="video")

    view.endofdirectory()


def search(args):
    """Search function
    """
    d = xbmcgui.Dialog().input(args._addon.getLocalizedString(30021), type=xbmcgui.INPUT_ALPHANUM)
    if not d or len(d) < 2:
        return

    response = urllib2.urlopen("https://api.watchbox.de/v1/search/?page=1&maxPerPage=28&active=true&term=" + urllib.quote_plus(d))
    html = response.read()

    # parse json
    json_obj = json.loads(html)

    for item in json_obj["items"]:
        if str(item["type"]) == "film":
            view.add_item(args,
                          {"url":         "/serien/test-" + str(item["entityId"]) + "/",
                           "title":       item["headline"].encode("utf-8"),
                           "mode":        "videoplay",
                           "thumb":       "https://aiswatchbox-a.akamaihd.net/watchbox/format/" + str(item["entityId"]) + "_dvdcover/600x840/test.jpg",
                           "fanart":      "https://aiswatchbox-a.akamaihd.net/watchbox/format/" + str(item["entityId"]) + "_dvdcover/600x840/test.jpg",
                           "year":        item["productionYear"].encode("utf-8"),
                           "genre":       item["genres"][0].encode("utf-8"),
                           "plot":        item["description"].encode("utf-8"),
                           "plotoutline": item["infoTextShort"].encode("utf-8")},
                          isFolder=False, mediatype="video")
        else:
            view.add_item(args,
                          {"url":         "/serien/test-" + str(item["entityId"]) + "/",
                           "title":       item["headline"].encode("utf-8"),
                           "mode":        "season_list",
                           "thumb":       "https://aiswatchbox-a.akamaihd.net/watchbox/format/" + str(item["entityId"]) + "_dvdcover/600x840/test.jpg",
                           "fanart":      "https://aiswatchbox-a.akamaihd.net/watchbox/format/" + str(item["entityId"]) + "_dvdcover/600x840/test.jpg",
                           "year":        item["productionYear"].encode("utf-8"),
                           "genre":       item["genres"][0].encode("utf-8"),
                           "plot":        item["description"].encode("utf-8"),
                           "plotoutline": item["infoTextShort"].encode("utf-8")},
                          isFolder=True, mediatype="video")

    view.endofdirectory()


def startplayback(args):
    """Plays a video
    """
    response = urllib2.urlopen("https://www.watchbox.de" + args.url)
    html = response.read()

    regex = r"hls\: '(.*?)',"
    matches = re.search(regex, html).group(1)

    if matches:
        # play stream
        item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"), path=matches + login.getCookie(args))
        item.setMimeType("application/vnd.apple.mpegurl")
        item.setContentLookup(False)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    else:
        xbmc.log("[PLUGIN] %s: Failed to play stream" % args._addonname, xbmc.LOGERROR)
        xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30044))
