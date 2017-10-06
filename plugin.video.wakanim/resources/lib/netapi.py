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
import urllib
import urllib2
from bs4 import BeautifulSoup

import xbmc
import xbmcgui

import login
import view


def showCatalog(args):
    """Show all animes
    """
    response = urllib2.urlopen("https://www.wakanim.tv/" + args._country + "/v2/catalogue")
    html = response.read()

    soup = BeautifulSoup(html, "html.parser")
    ul = soup.find("ul", {"class": "catalog_list"})

    for li in ul.find_all("li"):
        plot  = li.find("p", {"class": "tooltip_text"})
        stars = li.find("div", {"class": "stars"})
        star  = stars.find_all("span", {"class": "-no"})
        thumb = li.img["src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        view.add_item(args,
                      {"url":          li.a["href"],
                       "title":        li.find("div", {"class": "slider_item_description"}).span.strong.string.encode("utf-8"),
                       "mode":         "list_season",
                       "thumb":        thumb,
                       "fanart_image": thumb,
                       "episode":      li.find("p", {"class": "tooltip_text"}).strong.string.split(" ")[0],
                       "season":       li.find("span", {"class": "tooltip_season"}).string.split(" ")[0],
                       "rating":       str(10 - len(star) * 2),
                       "plot":         plot.contents[3].string.strip().encode("utf-8"),
                       "year":         li.time.string},
                      isFolder=True, mediatype="video")


    view.endofdirectory()


def searchAnime(args):
    """Search for animes
    """
    d = xbmcgui.Dialog().input(args._addon.getLocalizedString(30021), type=xbmcgui.INPUT_ALPHANUM)
    if not d:
        return

    post_data = urllib.urlencode({"search": d})
    response = urllib2.urlopen("https://www.wakanim.tv/" + args._country + "/v2/catalogue/search", post_data)
    html = response.read()

    soup = BeautifulSoup(html, "html.parser")
    ul = soup.find("ul", {"class": "catalog_list"})
    if not ul:
        view.endofdirectory()
        return

    for li in ul.find_all("li"):
        plot  = li.find("p", {"class": "tooltip_text"})
        stars = li.find("div", {"class": "stars"})
        star  = stars.find_all("span", {"class": "-no"})
        thumb = li.img["src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        view.add_item(args,
                      {"url":          li.a["href"],
                       "title":        li.find("div", {"class": "slider_item_description"}).span.strong.string.encode("utf-8"),
                       "mode":         "list_season",
                       "thumb":        thumb,
                       "fanart_image": thumb,
                       "episode":      li.find("p", {"class": "tooltip_text"}).strong.string.split(" ")[0],
                       "season":       li.find("span", {"class": "tooltip_season"}).string.split(" ")[0],
                       "rating":       str(10 - len(star)*2),
                       "plot":         plot.contents[3].string.strip().encode("utf-8"),
                       "year":         li.time.string},
                      isFolder=True, mediatype="video")


    view.endofdirectory()


def myDownloads(args):
    """View download able animes
    May not every episode is download able.
    """
    response = urllib2.urlopen("https://www.wakanim.tv/" + args._country + "/v2/mydownloads")
    html = response.read()

    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", {"class": "big-item-list"})
    if not container:
        view.endofdirectory()
        return

    for div in container.find_all("div", {"class": "big-item-list_item"}):
        thumb = div.img["src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        view.add_item(args,
                      {"url":          div.a["href"].replace("mydownloads/detail", "catalogue/show"),
                       "title":        div.find("h3", {"class": "big-item_title"}).string.strip().encode("utf-8"),
                       "mode":         "list_season",
                       "thumb":        thumb,
                       "fanart_image": thumb},
                      isFolder=True, mediatype="video")


    view.endofdirectory()


def myCollection(args):
    """View collection
    """
    response = urllib2.urlopen("https://www.wakanim.tv/" + args._country + "/v2/collection")
    html = response.read()

    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", {"class": "big-item-list"})
    if not container:
        view.endofdirectory()
        return

    for div in container.find_all("div", {"class": "big-item-list_item"}):
        thumb = div.img["src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        view.add_item(args,
                      {"url":          div.a["href"].replace("collection/detail", "catalogue/show"),
                       "title":        div.find("h3", {"class": "big-item_title"}).string.strip().encode("utf-8"),
                       "mode":         "list_season",
                       "thumb":        thumb,
                       "fanart_image": thumb},
                      isFolder=True, mediatype="video")


    view.endofdirectory()


def listSeason(args):
    """Show all seasons/arcs of an anime
    """
    response = urllib2.urlopen("https://www.wakanim.tv" + args.url)
    html = response.read()

    soup = BeautifulSoup(html, "html.parser")

    for section in soup.find_all("h2", {"class": "slider-section_title"}):
        if not section.span:
            continue
        title = section.get_text()[6:].strip()

        view.add_item(args,
                      {"url":          args.url,
                       "title":        title.encode("utf-8"),
                       "mode":         "list_episodes",
                       "season":       title.encode("utf-8"),
                       "thumb":        args.icon,
                       "fanart_image": args.fanart,
                       "episode":      args.episode,
                       "rating":       args.rating,
                       "plot":         args.plot,
                       "year":         args.year},
                      isFolder=True, mediatype="video")


    view.endofdirectory()


def listEpisodes(args):
    """Show all episodes of an season/arc
    """
    response = urllib2.urlopen("https://www.wakanim.tv" + args.url)
    html = response.read()

    soup = BeautifulSoup(html, "html.parser")

    for season in soup.findAll(text=args.season):
        parent = season.find_parent("li")
        if not parent:
            continue

        thumb = parent.img["src"].replace(" ", "%20")
        if thumb[:4] != "http":
            thumb = "https:" + thumb

        view.add_item(args,
                      {"url":          parent.a["href"],
                       "title":        parent.img["alt"].encode("utf-8"),
                       "mode":         "videoplay",
                       "thumb":        thumb,
                       "fanart_image": args.fanart,
                       "episode":      args.episode,
                       "rating":       args.rating,
                       "plot":         args.plot,
                       "year":         args.year},
                      isFolder=False, mediatype="video")


    view.endofdirectory()


def startplayback(args):
    """Plays a video
    """
    response = urllib2.urlopen("https://www.wakanim.tv" + args.url)
    html = response.read()

    soup = BeautifulSoup(html, "html.parser")

    # check if not premium
    if ("Diese Folge ist für Abonnenten reserviert" in html) or ("Cet épisode est reservé à nos abonnés" in html) or ("This episode is reserved for our subscribers" in html):
        xbmc.log("[PLUGIN] %s: You need to own this video or be a premium member '%s'" % (args._addonname, args.url), xbmc.LOGERROR)
        xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30043))
        return

    # prefer using download able videos
    if "episode_download_buttons" in html and 1==0: # TODO
        """
        div = soup.find("div", {"class": "episode_download_buttons"})
        if div:
            for file in reversed(div.find_all("a")):
                try:
                    url = "https://www.wakanim.tv" + file["href"] + login.getCookie(args)
                    item = xbmcgui.ListItem(args.name, path=url)
                    item.setInfo(type="Video", infoLabels={"Title":       args.name,
                                                            "TVShowTitle": args.name,
                                                            "episode":        args.episode,
                                                            "rating":        args.rating,
                                                            "plot":            args.plot,
                                                            "year":            args.year,
                                                            "studio":        args.studio})
                    item.setThumbnailImage(args.icon)
                    xbmc.Player().play(url, item)
                    return
                except:
                    pass
        else:
            xbmc.log("[PLUGIN] %s: Failed to play video" % args._addonname, xbmc.LOGERROR)
            xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30044))
        """

    # using stream with hls
    elif ("Unser Player ist in der Beta-Phase. Klicke hier, um den alten Player zu benutzen" in html) or ("Changer de lecteur" in html) or ("Our player is in beta, click here to go back to the old one" in html):
        # streaming is only for premium subscription
        if ("<span>Kostenlos</span>" in html) or ("<span>Gratuit</span>" in html) or ("<span>Free</span>" in html):
            xbmc.log("[PLUGIN] %s: You need to own this video or be a premium member '%s'" % (args._addonname, args.url), xbmc.LOGERROR)
            xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30043))
            return

        # get stream file
        regex = r"file: \"(.*?)\","
        matches = re.search(regex, html).group(1)

        if matches:
            # file url
            url = "https://www.wakanim.tv" + matches

            # play stream
            item = xbmcgui.ListItem(args.name, path=url + login.getCookie(args))
            item.setInfo(type="Video", infoLabels={"Title":       args.name,
                                                   "TVShowTitle": args.name,
                                                   "episode":     args.episode,
                                                   "rating":      args.rating,
                                                   "plot":        args.plot,
                                                   "year":        args.year})
            item.setThumbnailImage(args.icon)
            xbmc.Player().play(url + login.getCookie(args), item)
        else:
            xbmc.log("[PLUGIN] %s: Failed to play stream" % args._addonname, xbmc.LOGERROR)
            xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30044))

    else:
        xbmc.log("[PLUGIN] %s: You need to own this video or be a premium member '%s'" % (args._addonname, args.url), xbmc.LOGERROR)
        xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30043))
