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

import re
import json
import inputstreamhelper
from bs4 import BeautifulSoup
from os.path import join
from distutils.version import StrictVersion
try:
    from urllib import URLopener, quote_plus
except ImportError:
    from urllib.request import URLopener
    from urllib.parse import quote_plus

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

from . import api
from . import view


def searchHub(args):
    """Search function for community hubs
    """
    # ask for search string
    d = xbmcgui.Dialog().input(args._addon.getLocalizedString(30040), type=xbmcgui.INPUT_ALPHANUM)
    if not d:
        return

    # get website
    html = api.getPage(args, "https://steamcommunity.com/actions/SearchApps/" + quote_plus(d))
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30061)})
        view.endofdirectory(args)
        return

    # parse json
    json_obj = json.loads(html)

    # for every list entry
    for item in json_obj:
        # add to view
        view.add_item(args,
                      {"mode":        "viewhub",
                       "title":       item["name"],
                       "tvshowtitle": item["name"],
                       "appid":       item["appid"],
                       "thumb":       item["logo"],
                       "fanart":      item["logo"]},
                      isFolder=True, mediatype="video")

    view.endofdirectory(args)


def viewScreenshots(args, appid = None):
    """Show all screenshots
    """
    # get website
    page = str(getattr(args, "offset", 1))
    if not appid:
        html = api.getPage(args, "https://steamcommunity.com/apps/allcontenthome/?l=" + args._lang + "&browsefilter=" + args._filter + "&appHubSubSection=2&forceanon=1&userreviewsoffset=0&p=" + page + "&workshopitemspage=" + page + "&readytouseitemspage=" + page + "&mtxitemspage=" + page + "&itemspage=" + page + "&screenshotspage=" + page + "&videospage=" + page + "&artpage=" + page + "&allguidepage=" + page + "&webguidepage=" + page + "&integratedguidepage=" + page + "&discussionspage=" + page + "&numperpage=10&appid=0")
    else:
        html = api.getPage(args, "https://steamcommunity.com/app/" + appid + "/homecontent/?userreviewsoffset=0&p=" + page + "&workshopitemspage=" + page + "&readytouseitemspage=" + page + "&mtxitemspage=" + page + "&itemspage=" + page + "&screenshotspage=" + page + "&videospage=" + page + "&artpage=" + page + "&allguidepage=" + page + "&webguidepage=" + page + "&integratedguidepage=" + page + "&discussionspage=" + page + "&numperpage=10&browsefilter=" + args._filter + "&l=" + args._lang + "&appHubSubSection=2&filterLanguage=default&searchText=&forceanon=1")
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30061)})
        view.endofdirectory(args)
        return

    # parse html
    xbmcplugin.setContent(int(args._argv[1]), "images")
    soup = BeautifulSoup(html, "html.parser")

    # for every list entry
    for div in soup.find_all("div", {"class": "modalContentLink"}):
        # get values
        sText  = div.find("div", {"class": "apphub_CardContentTitle"}).string.strip()
        sGame = div.find("div", {"class": "apphub_CardContentType"}).string.strip()
        sRating = div.find("div", {"class": "apphub_CardRating"}).string.strip()
        sThumb  = div.find("img", {"class": "apphub_CardContentPreviewImage"})["src"]
        try:
            sURL = re.findall(r", (.*?) ", div.find("img", {"class": "apphub_CardContentPreviewImage"})["srcset"])[-1]
        except IndexError:
            sURL = div.find("img", {"class": "apphub_CardContentPreviewImage"})["srcset"].split(" ")[0]
        try:
            sAuthor = div.find("div", {"class": "apphub_CardContentAuthorName"}).a.string.strip()
        except AttributeError:
            sAuthor = div.find("div", {"class": "apphub_CardContentAppName"}).a.string.strip()

        # add to view
        view.add_item(args,
                      {"url":         sURL,
                       "mode":        "imageplay",
                       "title":       sAuthor + " - " + sText,
                       "tvshowtitle": sAuthor + " - " + sText,
                       "plot":        sAuthor + "\n" + sText + "\n" + sGame + "\nLikes " + sRating,
                       "plotoutline": sAuthor + "\n" + sText + "\n" + sGame + "\nLikes " + sRating,
                       "thumb":       sThumb,
                       "fanart":      sThumb,
                       "credits":     sAuthor},
                      isFolder=False, mediatype="video")

    # next page
    view.add_item(args,
                  {"title":  args._addon.getLocalizedString(30042),
                   "url":    getattr(args, "url", ""),
                   "offset": str(int(getattr(args, "offset", 1)) + 1),
                   "appid":  appid,
                   "mode":   args.mode})
    view.endofdirectory(args)


def viewArtwork(args, appid = None):
    """Show all artwork
    """
    # get website
    page = str(getattr(args, "offset", 1))
    if not appid:
        html = api.getPage(args, "https://steamcommunity.com/apps/allcontenthome/?l=" + args._lang + "&browsefilter=" + args._filter + "&appHubSubSection=4&forceanon=1&userreviewsoffset=0&p=" + page + "&workshopitemspage=" + page + "&readytouseitemspage=" + page + "&mtxitemspage=" + page + "&itemspage=" + page + "&screenshotspage=" + page + "&videospage=" + page + "&artpage=" + page + "&allguidepage=" + page + "&webguidepage=" + page + "&integratedguidepage=" + page + "&discussionspage=" + page + "&numperpage=10&appid=0")
    else:
        html = api.getPage(args, "https://steamcommunity.com/app/" + appid + "/homecontent/?userreviewsoffset=0&p=" + page + "&workshopitemspage=" + page + "&readytouseitemspage=" + page + "&mtxitemspage=" + page + "&itemspage=" + page + "&screenshotspage=" + page + "&videospage=" + page + "&artpage=" + page + "&allguidepage=" + page + "&webguidepage=" + page + "&integratedguidepage=" + page + "&discussionspage=" + page + "&numperpage=10&browsefilter=" + args._filter + "&l=" + args._lang + "&appHubSubSection=4&filterLanguage=default&searchText=&forceanon=1")
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30061)})
        view.endofdirectory(args)
        return

    # parse html
    xbmcplugin.setContent(int(args._argv[1]), "images")
    soup = BeautifulSoup(html, "html.parser")

    # for every list entry
    for div in soup.find_all("div", {"class": "modalContentLink"}):
        # get values
        sText  = div.find("div", {"class": "apphub_CardContentTitle"}).string.strip()
        sGame = div.find("div", {"class": "apphub_CardContentType"}).string.strip()
        sRating = div.find("div", {"class": "apphub_CardRating"}).string.strip()
        sThumb  = div.find("img", {"class": "apphub_CardContentPreviewImage"})["src"]
        try:
            sURL = re.findall(r", (.*?) ", div.find("img", {"class": "apphub_CardContentPreviewImage"})["srcset"])[-1]
        except IndexError:
            sURL = div.find("img", {"class": "apphub_CardContentPreviewImage"})["srcset"].split(" ")[0]
        try:
            sAuthor = div.find("div", {"class": "apphub_CardContentAuthorName"}).a.string.strip()
        except AttributeError:
            sAuthor = div.find("div", {"class": "apphub_CardContentAppName"}).a.string.strip()

        # add to view
        view.add_item(args,
                      {"url":         sURL,
                       "mode":        "imageplay",
                       "title":       sAuthor + " - " + sText,
                       "tvshowtitle": sAuthor + " - " + sText,
                       "plot":        sAuthor + "\n" + sText + "\n" + sGame + "\nLikes " + sRating,
                       "plotoutline": sAuthor + "\n" + sText + "\n" + sGame + "\nLikes " + sRating,
                       "thumb":       sThumb,
                       "fanart":      sThumb,
                       "credits":     sAuthor},
                      isFolder=False, mediatype="video")

    # next page
    view.add_item(args,
                  {"title":  args._addon.getLocalizedString(30042),
                   "url":    getattr(args, "url", ""),
                   "offset": str(int(getattr(args, "offset", 1)) + 1),
                   "appid":  appid,
                   "mode":   args.mode})
    view.endofdirectory(args)


def viewBroadcasts(args, appid = None):
    """Show all broadcasts
    """
    # check inputstream adaptive version
    if StrictVersion(xbmcaddon.Addon(id="inputstream.adaptive").getAddonInfo("version")) < StrictVersion("2.2.19"):
        xbmc.log("[PLUGIN] %s: inputstream.adaptive is too old for broadcasting 2.2.19 is required" % args._addonname, xbmc.LOGERROR)
        xbmcgui.Dialog().ok(args._addonname, args._addon.getLocalizedString(30065))
        return

    # get website
    page = str(getattr(args, "offset", 1))
    if not appid:
        html = api.getPage(args, "https://steamcommunity.com/apps/allcontenthome/?l=" + args._lang + "&browsefilter=" + args._filter + "&appHubSubSection=13&forceanon=1&userreviewsoffset=0&broadcastsoffset=10&p=" + page + "&workshopitemspage=" + page + "&readytouseitemspage=" + page + "&mtxitemspage=" + page + "&itemspage=" + page + "&screenshotspage=" + page + "&videospage=" + page + "&artpage=" + page + "&allguidepage=" + page + "&webguidepage=" + page + "&integratedguidepage=" + page + "&discussionspage=" + page + "&numperpage=10&appid=0")
    else:
        html = api.getPage(args, "https://steamcommunity.com/app/" + appid + "/homecontent/?userreviewsoffset=0&broadcastsoffset=12&p=" + page + "&workshopitemspage=" + page + "&readytouseitemspage=" + page + "&mtxitemspage=" + page + "&itemspage=" + page + "&screenshotspage=" + page + "&videospage=" + page + "&artpage=" + page + "&allguidepage=" + page + "&webguidepage=" + page + "&integratedguidepage=" + page + "&discussionspage=" + page + "&numperpage=12&browsefilter=" + args._filter + "&l=" + args._lang + "&appHubSubSection=13&filterLanguage=default&searchText=&forceanon=1")
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30061)})
        view.endofdirectory(args)
        return

    # parse html
    soup = BeautifulSoup(html, "html.parser")

    # for every list entry
    for div in soup.find_all("div", {"class": "Broadcast_Card"}):
        # get values
        sTitle  = div.find("div", {"class": "apphub_CardContentTitle"}).string.strip()
        sAuthor = div.find("div", {"class": "apphub_CardContentAuthorName"}).a.string.strip()
        sViewer = div.find("div", {"class": "apphub_CardContentViewers"}).string.strip()
        sThumb  = div.find("img", {"class": "apphub_CardContentPreviewImage"})["src"]

        # add to view
        view.add_item(args,
                      {"url":         div.a["href"],
                       "mode":        "videoplay_broadcast",
                       "title":       sAuthor + " - " + sTitle,
                       "tvshowtitle": sAuthor + " - " + sTitle,
                       "plot":        sAuthor + "\n" + sTitle + "\n" + sViewer,
                       "plotoutline": sAuthor + "\n" + sTitle + "\n" + sViewer,
                       "thumb":       sThumb,
                       "fanart":      sThumb,
                       "credits":     sAuthor},
                      isFolder=False, mediatype="video")

    # next page
    view.add_item(args,
                  {"title":  args._addon.getLocalizedString(30042),
                   "url":    getattr(args, "url", ""),
                   "offset": str(int(getattr(args, "offset", 1)) + 1),
                   "appid":  appid,
                   "mode":   args.mode})
    view.endofdirectory(args)


def viewVideos(args, appid = None):
    """Show all videos
    """
    # get website
    page = str(getattr(args, "offset", 1))
    if not appid:
        html = api.getPage(args, "https://steamcommunity.com/apps/allcontenthome/?l=" + args._lang + "&browsefilter=" + args._filter + "&appHubSubSection=3&forceanon=1&userreviewsoffset=0&p=" + page + "&workshopitemspage=" + page + "&readytouseitemspage=" + page + "&mtxitemspage=" + page + "&itemspage=" + page + "&screenshotspage=" + page + "&videospage=" + page + "&artpage=" + page + "&allguidepage=" + page + "&webguidepage=" + page + "&integratedguidepage=" + page + "&discussionspage=" + page + "&numperpage=10&appid=0")
    else:
        html = api.getPage(args, "https://steamcommunity.com/app/" + appid + "/homecontent/?userreviewsoffset=0&p=" + page + "&workshopitemspage=" + page + "&readytouseitemspage=" + page + "&mtxitemspage=" + page + "&itemspage=" + page + "&screenshotspage=" + page + "&videospage=" + page + "&artpage=" + page + "&allguidepage=" + page + "&webguidepage=" + page + "&integratedguidepage=" + page + "&discussionspage=" + page + "&numperpage=10&browsefilter=" + args._filter + "&l=" + args._lang + "&appHubSubSection=3&filterLanguage=default&searchText=&forceanon=1")
    if not html:
        view.add_item(args, {"title": args._addon.getLocalizedString(30061)})
        view.endofdirectory(args)
        return

    # parse html
    soup = BeautifulSoup(html, "html.parser")

    # for every list entry
    for div in soup.find_all("div", {"class": "modalContentLink"}):
        # get values
        sTitle  = div.find("div", {"class": "apphub_CardContentTitle"}).string.strip()
        sGame = div.find("div", {"class": "apphub_CardContentType"}).string.strip()
        sThumb  = div.find("img", {"class": "apphub_CardContentPreviewImage"})["src"]
        try:
            sAuthor = div.find("div", {"class": "apphub_CardContentAuthorName"}).a.string.strip()
        except AttributeError:
            sAuthor = div.find("div", {"class": "apphub_CardContentAppName"}).a.string.strip()

        # add to view
        view.add_item(args,
                      {"url":         re.search(r"youtube\.com\/vi\/(.*?)\/0\.jpg", sThumb).group(1),
                       "mode":        "videoplay_youtube",
                       "title":       sAuthor + " - " + sTitle,
                       "tvshowtitle": sAuthor + " - " + sTitle,
                       "plot":        sAuthor + "\n" + sTitle + "\n" + sGame,
                       "plotoutline": sAuthor + "\n" + sTitle + "\n" + sGame,
                       "thumb":       sThumb,
                       "fanart":      sThumb,
                       "credits":     sAuthor},
                      isFolder=False, mediatype="video")

    # next page
    view.add_item(args,
                  {"title":  args._addon.getLocalizedString(30042),
                   "url":    getattr(args, "url", ""),
                   "offset": str(int(getattr(args, "offset", 1)) + 1),
                   "appid":  appid,
                   "mode":   args.mode})
    view.endofdirectory(args)


def startplayback_images(args):
    """Shows an image
    """
    # cache path
    sDir = xbmc.translatePath(args._addon.getAddonInfo("profile"))
    if args.PY2:
        sPath = join(sDir.decode("utf-8"), u"image.jpg")
    else:
        sPath = join(sDir, "image.jpg")

    # download image
    file = URLopener()
    file.retrieve(args.url, sPath)

    # display image
    item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"), path=sPath)
    xbmcplugin.setResolvedUrl(int(args._argv[1]), True, item)
    xbmc.executebuiltin("SlideShow(" + sDir + ")")


def startplayback_broadcast(args):
    """Plays a broadcast stream
    """
    # start video
    if u"youtube.com" in args.url:
        item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"), path=args.url)
        xbmcplugin.setResolvedUrl(int(args._argv[1]), True, item)
        return True

    # get stream id
    streamid = re.search(r"/watch/(.*?)$", args.url).group(1)

    # get streaming file
    xbmc.log(args.url, xbmc.LOGERROR)
    html = api.getPage(args, "https://steamcommunity.com/broadcast/getbroadcastmpd/?steamid=" + streamid + "&broadcastid=0")
    if not html:
        item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"))
        xbmcplugin.setResolvedUrl(int(args._argv[1]), False, item)
        return

    # parse json
    json_obj = json.loads(html)

    # prepare playback
    item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"), path=json_obj["url"])
    item.setMimeType("application/dash+xml")
    item.setContentLookup(False)

    # inputstream adaptive
    is_helper = inputstreamhelper.Helper("mpd")
    if is_helper.check_inputstream():
        item.setProperty("inputstreamaddon", "inputstream.adaptive")
        item.setProperty("inputstream.adaptive.manifest_type", "mpd")
        # start playback
        xbmcplugin.setResolvedUrl(int(args._argv[1]), True, item)


def startplayback_youtube(args):
    """Plays a youtube video
    """
    # start video
    item = xbmcgui.ListItem(getattr(args, "title", "Title not provided"), path="plugin://plugin.video.youtube/play/?video_id=" + args.url)
    xbmcplugin.setResolvedUrl(int(args._argv[1]), True, item)
