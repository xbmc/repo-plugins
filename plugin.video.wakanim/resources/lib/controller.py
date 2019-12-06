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

import re
import sys
import ssl
import time
import json
from bs4 import BeautifulSoup

PY3 = sys.version_info.major >= 3
if PY3:
    from urllib.parse import quote_plus
    from urllib.request import urlopen, Request
    from urllib.error import URLError
else:
    from urllib import quote_plus
    from urllib2 import urlopen, Request, URLError

import xbmc
import xbmcgui
import xbmcplugin

from . import api
from . import view
from .streamparams import getStreamParams


def showCatalog(args):
    """Show all animes
    """
    # get website
    html = api.getPage(args, "https://www.wakanim.tv/" + args._country + "/v2/catalogue")
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30041)})
        view.endofdirectory(args)
        return

    # parse html
    soup = BeautifulSoup(html, "html.parser")
    ul = soup.find("ul", {"class": "catalog_list"})

    # for every list entry
    for li in ul.find_all("li"):
        # get values
        plot  = li.find("p", {"class": "tooltip_text"})
        stars = li.find("div", {"class": "stars"})
        star  = stars.find_all("span", {"class": "-no"})
        thumb = li.img["src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        # add to view
        view.add_item(args,
                      {"url":         li.a["href"],
                       "title":       li.find("div", {"class": "slider_item_description"}).span.strong.string.strip(),
                       "tvshowtitle": li.find("div", {"class": "slider_item_description"}).span.strong.string.strip(),
                       "mode":        "list_season",
                       "thumb":       thumb,
                       "fanart":      thumb,
                       "rating":      str(10 - len(star) * 2),
                       "plot":        plot.contents[3].string.strip(),
                       "year":        li.time.string.strip()},
                      isFolder=True, mediatype="video")

    view.endofdirectory(args)


def listLastEpisodes(args):
    """Show last aired episodes
    """
    # get website
    html = api.getPage(args, "https://www.wakanim.tv/" + args._country + "/v2")
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30041)})
        view.endofdirectory(args)
        return

    # parse html
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", {"class": "js-slider-lastEp"})
    if not container:
        view.add_item(args, {"title": args._addon.getLocalizedString(30041)})
        view.endofdirectory(args)
        return

    # for every list entry
    for li in container.find_all("li"):
        # get values
        progress = int(li.find("div", {"class": "ProgressBar"}).get("data-progress"))
        thumb = li.img["src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        # add to view
        view.add_item(args,
                      {"url":       li.a["href"],
                       "title":     li.img["alt"],
                       "mode":      "videoplay",
                       "thumb":     thumb,
                       "fanart":    thumb,
                       "plot":      li.find("a", {"class": "slider_item_season"}).string.strip(),
                       "playcount": "1" if progress > 90 else "0",
                       "progress":  str(progress)},
                      isFolder=False, mediatype="video")

    view.endofdirectory(args)


def listLastSimulcasts(args):
    """Show last simulcasts
    """
    # get website
    html = api.getPage(args, "https://www.wakanim.tv/" + args._country + "/v2")
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30041)})
        view.endofdirectory(args)
        return

    # parse html
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", {"class": "js-slider-lastShow"})
    if not container:
        view.add_item(args, {"title": args._addon.getLocalizedString(30041)})
        view.endofdirectory(args)
        return

    # for every list entry
    for li in container.find_all("li"):
        # get values
        plot  = li.find("p", {"class": "tooltip_text"})
        stars = li.find("div", {"class": "stars"})
        star  = stars.find_all("span", {"class": "-no"})
        thumb = li.img["src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        # add to view
        view.add_item(args,
                      {"url":         li.a["href"],
                       "title":       li.find("div", {"class": "slider_item_description"}).span.strong.string.strip(),
                       "tvshowtitle": li.find("div", {"class": "slider_item_description"}).span.strong.string.strip(),
                       "mode":        "list_season",
                       "thumb":       thumb,
                       "fanart":      thumb,
                       "rating":      str(10 - len(star) * 2),
                       "plot":        plot.contents[-1].string.strip(),
                       "year":        li.time.string.strip()},
                      isFolder=True, mediatype="video")

    view.endofdirectory(args)


def searchAnime(args):
    """Search for animes
    """
    # ask for search string
    d = xbmcgui.Dialog().input(args._addon.getLocalizedString(30021), type=xbmcgui.INPUT_ALPHANUM)
    if not d:
        return

    # get website
    html = api.getPage(args, "https://www.wakanim.tv/" + args._country + "/v2/catalogue/search", {"search": d})

    # get JWT token
    regex = r"var token = '(.*?)';"
    matches = re.search(regex, html)
    token = matches.group(1)

    # get search results
    req = urlopen("https://apiwaka.azure-api.net/search/v2/?search=" + quote_plus(d) + "&token=" + quote_plus(token))
    search = json.loads(req.read())

    # for every list entry
    for item in search["value"]:
        # add to view
        view.add_item(args,
                      {"url":           "/" + args._country + "/v2/catalogue/show/" + item["IdShowItem"],
                       "title":         item["Name"],
                       "tvshowtitle":   item["Name"],
                       "originaltitle": item["OriginalName"],
                       "mode":          "list_season",
                       "thumb":         item["Image"],
                       "fanart":        item["Image"],
                       "rating":        item["RatingNote"],
                       "plot":          item["Synopsis"],
                       "plotoutline":   item["SmallSummary"],
                       "premiered":     item["StartDate"],
                       "credits":       item["Copyright"],
                       "year":          item["YearStartBroadcasting"]},
                      isFolder=True, mediatype="video")

    view.endofdirectory(args)


def myDownloads(args):
    """View download able animes
    May not every episode is download able.
    """
    # get website
    html = api.getPage(args, "https://www.wakanim.tv/" + args._country + "/v2/mydownloads")
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30041)})
        view.endofdirectory(args)
        return

    # parse html
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", {"class": "big-item-list"})
    if not container:
        view.add_item(args, {"title": args._addon.getLocalizedString(30041)})
        view.endofdirectory(args)
        return

    # for every list entry
    for div in container.find_all("div", {"class": "big-item-list_item"}):
        # get values
        thumb = div.img["src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        # add to view
        view.add_item(args,
                      {"url":    div.a["href"].replace("mydownloads/detail", "catalogue/show"),
                       "title":  div.find("h3", {"class": "big-item_title"}).string.strip(),
                       "mode":   "list_season",
                       "thumb":  thumb,
                       "fanart": thumb},
                      isFolder=True, mediatype="video")

    view.endofdirectory(args)


def listSeason(args):
    """Show all seasons/arcs of an anime
    """
    # get showid
    regex = r"\/show\/([0-9]*)"
    matches = re.search(regex, args.url)
    showid = matches.group(1)

    # get website
    html = api.getPage(args, "https://www.wakanim.tv/" + args._country + "/v2/catalogue/show/" + showid)
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30041)})
        view.endofdirectory(args)
        return

    # check if redirected
    matches = re.search(regex, html)
    if not matches.group(1) == showid:
        # get website
        showid = matches.group(1)
        html = api.getPage(args, "https://www.wakanim.tv/" + args._country + "/v2/catalogue/show/" + showid)
        if not html:
            view.add_item(args, {"title": args._addon.getLocalizedString(30041)})
            view.endofdirectory(args)
            return

    # parse html
    soup = BeautifulSoup(html, "html.parser")

    # get values
    date = soup.find_all("span", {"class": "border-list_text"})[1].find_all("span")
    year = date[2].string.strip()
    date = year + "-" + date[1].string.strip() + "-" + date[0].string.strip()
    originaltitle = soup.find_all("span", {"class": "border-list_text"})[2].string.strip()
    try:
        plot = soup.find_all("span", {"class": "border-list_text"})[0].string.strip()
    except AttributeError:
        plot = str(soup.find_all("span", {"class": "border-list_text"})[0])
    credit = soup.find_all("span", {"class": "border-list_text"})[6].string.strip()
    trailer = soup.find("a", {"class": "trailer"})
    if trailer:
        # get YouTube trailer
        trailer = "plugin://plugin.video.youtube/play/?video_id=" + re.search(r"(?:\.be/|/embed)/?([^&=%:/\?]{11})", trailer["href"]).group(1)
        view.add_item(args,
                      {"url":    trailer,
                       "mode":   "trailer",
                       "thumb":  args.thumb.replace(" ", "%20"),
                       "fanart": args.fanart.replace(" ", "%20"),
                       "title":  args._addon.getLocalizedString(30024)},
                      isFolder=False, mediatype="video")
    else:
        trailer = ""

    # get season infos
    newURL = soup.find_all("a", {"class": "SerieNav-btn"})[1]["href"]

    # get website
    html = api.getPage(args, "https://www.wakanim.tv" + newURL)
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30041)})
        view.endofdirectory(args)
        return

    # parse html
    soup = BeautifulSoup(html, "html.parser")

    # for every list entry
    container = soup.find("div", {"id": "list-season-container"})
    for option in container.find_all("option"):
        # get values
        if not option["value"]:
            continue

        # add to view
        view.add_item(args,
                      {"url":           option["value"],
                       "title":         option.string.strip(),
                       "mode":          "list_episodes",
                       "thumb":         args.thumb.replace(" ", "%20"),
                       "fanart":        args.fanart.replace(" ", "%20"),
                       "season":        option.string.strip(),
                       "plot":          plot,
                       "plotoutline":   getattr(args, "plot", ""),
                       "year":          year,
                       "premiered":     date,
                       "trailer":       trailer,
                       "originaltitle": originaltitle,
                       "credits":       credit},
                      isFolder=True, mediatype="video")

    view.endofdirectory(args)


def listEpisodes(args):
    """Show all episodes of an season/arc
    """
    # get website
    html = api.getPage(args, "https://www.wakanim.tv" + args.url)
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30041)})
        view.endofdirectory(args)
        return

    # parse html
    soup = BeautifulSoup(html, "html.parser")

    # for every episode
    for li in soup.find_all("div", {"class": "slider_item_inner"}):
        progress = int(li.find("div", {"class": "ProgressBar"}).get("data-progress"))
        thumb = li.img["src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        # add to view
        view.add_item(args,
                      {"url":       li.a["href"],
                       "title":     li.img["alt"],
                       "mode":      "videoplay",
                       "thumb":     thumb.replace(" ", "%20"),
                       "fanart":    args.fanart.replace(" ", "%20"),
                       "playcount": "1" if progress > 90 else "0",
                       "progress":  str(progress)},
                      isFolder=False, mediatype="video")

    view.endofdirectory(args)


def startplayback(args):
    """Plays a video
    """
    # get website
    html = api.getPage(args, "https://www.wakanim.tv" + args.url)
    if not html:
        item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"))
        xbmcplugin.setResolvedUrl(int(args._argv[1]), False, item)
        return

    # check if not premium
    if (u"Diese Folge ist für Abonnenten reserviert" in html) or (u"Cet épisode est reservé à nos abonnés" in html) or (u"This episode is reserved for our subscribers" in html) or (u"Эта серия зарезервирована для наших подписчиков" in html):
        xbmc.log("[PLUGIN] %s: You need to own this video or be a premium member '%s'" % (args._addonname, args.url), xbmc.LOGERROR)
        item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"))
        xbmcplugin.setResolvedUrl(int(args._argv[1]), False, item)
        xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30043))
        return

    # check if we have to reactivate video
    if u"reactivate" in html:
        # parse html
        soup = BeautifulSoup(html, "html.parser")

        # reactivate video
        a = soup.find("div", {"id": "jwplayer-container"}).a["href"]
        html = api.getPage(args, "https://www.wakanim.tv" + a)

        # reload page
        html = api.getPage(args, "https://www.wakanim.tv" + args.url)

        # check if successfull
        if u"reactivate" in html:
            xbmc.log("[PLUGIN] %s: Reactivation failed '%s'" % (args._addonname, args.url), xbmc.LOGERROR)
            item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"))
            xbmcplugin.setResolvedUrl(int(args._argv[1]), False, item)
            xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30042))
            return

    # playing stream
    if u"jwplayer-container" in html:
        # streaming is only for premium subscription
        if ((u"<span>Kostenlos</span>" in html) or (u"<span>Gratuit</span>" in html) or (u"<span>Free</span>" in html) or (u"<span>Бесплатный аккаунт</span>" in html)) and not (u"episode_premium_title" in html):
            xbmc.log("[PLUGIN] %s: You need to own this video or be a premium member '%s'" % (args._addonname, args.url), xbmc.LOGERROR)
            item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"))
            xbmcplugin.setResolvedUrl(int(args._argv[1]), False, item)
            xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30043))
            return

        # get stream parameters
        params = getStreamParams(args, html)
        if not params:
            item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"))
            xbmcplugin.setResolvedUrl(int(args._argv[1]), False, item)
            return

        # play stream
        url = params["url"]
        item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"), path=url)
        if params["content-type"]:
            item.setMimeType(params["content-type"])
        for k,v in list(params["properties"].items()):
            item.setProperty(k, v)
        item.setProperty("IsPlayable", "true")
        item.setContentLookup(False)

        xbmcplugin.setResolvedUrl(int(args._argv[1]), True, item)

        if args._addon.getSetting("sync_playtime") == "true":
            # get required infos
            player = xbmc.Player()
            regex = r"idepisode=(.*?)&(?:.*?)&idserie=(.*?)\","
            matches = re.search(regex, html)
            episodeid = int(matches.group(1))
            showid = int(matches.group(2))

            # wait for video to begin
            timeout = time.time() + 20
            while not xbmc.getCondVisibility("Player.IsInternetStream"):
                xbmc.sleep(50)
                # timeout to prevent infinite loop
                if time.time() > timeout:
                    xbmc.log("[PLUGIN] %s: Timeout reached, video did not start in 20 seconds" % args._addonname, xbmc.LOGERROR)
                    return

            # ask if user want to continue playback
            resume = int(getattr(args, "progress", 0))
            if resume >= 5 and resume <= 90:
                player.pause()
                if xbmcgui.Dialog().yesno(args._addonname, args._addon.getLocalizedString(30045) % resume):
                    player.seekTime(player.getTotalTime() * (resume/100.0))
                player.pause()

            # update playtime at wakanim
            try:
                while url == player.getPlayingFile():
                    # wait 10 seconds
                    xbmc.sleep(10000)

                    # calculate message
                    post = {"ShowId":          showid,
                            "EpisodeId":       episodeid,
                            "PlayTime":        player.getTime(),
                            "Duration":        player.getTotalTime(),
                            "TotalPlayedTime": 4,
                            "FromSVOD":        "false"}

                    # send data
                    try:
                        req = Request("https://www.wakanim.tv/" + args._country + "/v2/svod/saveplaytimeprogress",
                                      json.dumps(post).encode("utf-8"),
                                      headers={"Content-type": "application/json"})
                        response = urlopen(req)
                        html = response.read()
                    except (ssl.SSLError, URLError):
                        # catch timeout exception
                        pass
            except RuntimeError:
                xbmc.log("[PLUGIN] %s: Playback aborted" % args._addonname, xbmc.LOGDEBUG)
    else:
        xbmc.log("[PLUGIN] %s: You need to own this video or be a premium member '%s'" % (args._addonname, args.url), xbmc.LOGERROR)
        xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30043))
