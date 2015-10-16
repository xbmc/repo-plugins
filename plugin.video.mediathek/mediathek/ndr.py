# -*- coding: utf-8 -*-
# -------------LicenseHeader--------------
# plugin.video.Mediathek - Gives access to most video-platforms from German public service broadcasters
# Copyright (C) 2010  Raptor 2101 [raptor2101@gmx.de]
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import re
import datetime
import time
import calendar
from mediathek import *
from xml.dom import minidom


class NDRMediathek(Mediathek):
    @classmethod
    def name(self):
        return "NDR"

    def isSearchable(self):
        return True

    def __init__(self, simpleXbmcGui):
        self.gui = simpleXbmcGui

        self.rootLink = "http://www.ndr.de"

        # self.searchLink = self.rootLink+"/mediathek/mediatheksuche101.html?pagenumber=1&search_video=true&"
        self.searchLink = self.rootLink+"/suche10.html?search_mediathek=1&"

        # Hauptmenue
        tmp_menu = []
        extractBroadcasts = re.compile("<a href=\"/mediathek/mediatheksuche105_broadcast-(.*?).html\" class=\"link_arrow\">(.*?)</a>")
        htmlPage = self.loadPage("http://www.ndr.de/mediathek/sendungen_a-z/index.html").decode('utf-8')

        x = 0
        for menuNode in extractBroadcasts.finditer(htmlPage):
            menuId = menuNode.group(1)
            menuItem = menuNode.group(2)
            menuLink = self.rootLink+"/mediatheksuche105_broadcast-"+menuId+"_format-video_page-1.html"
            tmp_menu.append(TreeNode("0."+str(x), menuItem, menuLink, True))
            x = x+1

        self.menuTree = [
            TreeNode("0", "Sendungen von A-Z", "", False, tmp_menu),
            TreeNode("1", "Sendung verpasst?", "sendungverpasst", True),
            TreeNode("2","Live","livestream",True),#Livestream ruckelt zu stark :-(
        ]

    def buildPageMenuSendungVerpasst(self, action):
        # Bis 2008
        # htmlPage = self.loadPage("http://www.ndr.de/mediathek/dropdown105-extapponly.html")
        htmlPage = self.loadPage("http://www.ndr.de/mediathek/sendung_verpasst/epg1490_display-onlyvideo.html")

        # regex_verpasstNow = re.compile("<input type=\"hidden\" name=\"verpasstNow\" id =\"verpasstNow\" value=\"(\\d{2}\.\\d{2}\.\\d{4})\" />")
        regex_verpasstNow = re.compile(
            '<h1 class="viewdate">\n.*?(\\d{2})\.(\\d{2})<span class="notbelow30em">\.(\\d{4})</span>'
        )
        verpasstNow = ".".join(regex_verpasstNow.search(htmlPage).groups())
        try:
            dateTimeTmp = datetime.datetime.strptime(verpasstNow, "%d.%m.%Y")
        except TypeError:
            dateTimeTmp = datetime.datetime(*(time.strptime(verpasstNow, "%d.%m.%Y")[0:6]))

        nodeCount = 0

        if action == "":
            verpasstHeute = dateTimeTmp.strftime("%Y-%m-%d")
            dateTimeTmp = dateTimeTmp-datetime.timedelta(1)
            verpasstGestern = dateTimeTmp.strftime("%Y-%m-%d")
            dateTimeTmp = dateTimeTmp-datetime.timedelta(1)
            verpasstVorGestern = dateTimeTmp.strftime("%Y-%m-%d")

            # self.gui.buildVideoLink(DisplayObject("Heute", "", "", "description", self.rootLink + "/mediathek/verpasst109-extapponly_date-" + verpasstHeute + "_branding-ndrtv.html", False), self, 1)
            self.gui.buildVideoLink(DisplayObject("Heute", "", "", "description", self.rootLink + "/mediathek/sendung_verpasst/epg1490_date-" + verpasstHeute + "_display-onlyvideo.html", False), self, 1)
            self.gui.buildVideoLink(DisplayObject("Gestern", "", "", "description", self.rootLink + "/mediathek/sendung_verpasst/epg1490_date-" + verpasstGestern + "_display-onlyvideo.html", False), self, 2)
            self.gui.buildVideoLink(DisplayObject("Vorgestern", "", "", "description", self.rootLink + "/mediathek/sendung_verpasst/epg1490_date-" + verpasstVorGestern + "_display-onlyvideo.html", False), self, 3)
            self.gui.buildVideoLink(DisplayObject("Datum waehlen", "", "", "description", "sendungverpasstselect", False), self, 4)
        elif action == "select":
            dateTimeTmp = dateTimeTmp-datetime.timedelta(3)
            verpasstStartYear = int(dateTimeTmp.strftime("%Y"))
            for verpasstStart in reversed(range(1, int(dateTimeTmp.strftime("%m")))):
                menu_title = str(verpasstStart)+"."+str(verpasstStartYear)
                menu_action = "sendungverpasstselectmonth" + str(verpasstStartYear) + str(verpasstStart)
                self.gui.buildVideoLink(DisplayObject(menu_title, "", "", "description", menu_action, False), self, nodeCount)
                verpasstStart = verpasstStart - 1
                nodeCount = nodeCount + 1

            while verpasstStartYear > 2008:
                verpasstStartYear = verpasstStartYear - 1
                menu_title = str(verpasstStartYear)
                self.gui.buildVideoLink(DisplayObject(menu_title, "", "", "description", "sendungverpasstselectyear" + str(verpasstStartYear), False), self, nodeCount)
        elif action[0:11] == "selectmonth":
            action = action[11:]
            action_year = action[0:4]
            action_month = action[4:]

            try:
                dateTimeTmp2 = datetime.datetime.strptime(action_year+action_month, "%Y%m")
            except TypeError:
                dateTimeTmp2 = datetime.datetime(*(time.strptime(action_year+action_month, "%Y%m")[0:6]))

            if dateTimeTmp.strftime("%Y%m") == dateTimeTmp2.strftime("%Y%m"):
                startDay = int(dateTimeTmp2.strftime("%d"))
            else:
                startDay = calendar.monthrange(int(action_year), int(action_month))[1]

            try:
                dateTimeTmp2 = datetime.datetime.strptime(action_year + action_month + str(startDay), "%Y%m%d")
            except TypeError:
                dateTimeTmp2 = datetime.datetime(*(time.strptime(action_year + action_month + str(startDay), "%Y%m%d")[0:6]))

            for i in reversed(range(1, startDay)):
                verpasstDatum = dateTimeTmp2.strftime("%Y-%m-%d")
                menu_title = dateTimeTmp2.strftime("%d.%m.%Y")
                menu_action = self.rootLink + "/mediathek/sendung_verpasst/epg1490_date-" + verpasstDatum + "_display-onlyvideo.html"
                self.gui.buildVideoLink(DisplayObject(menu_title, "", "", "description", menu_action, False), self, nodeCount)
                nodeCount = nodeCount + 1
                dateTimeTmp2 = dateTimeTmp2-datetime.timedelta(1)
        elif action[0:10] == "selectyear":
            action = action[10:]
            action_year = action[0:4]
            for startMonth in reversed(range(1, 12)):
                menu_title = str(startMonth) + "." + action_year
                menu_action = "sendungverpasstselectmonth" + action_year + str(startMonth)
                self.gui.buildVideoLink(DisplayObject(menu_title, "", "", "description", menu_action, False), self, nodeCount)
                nodeCount = nodeCount + 1

    def buildPageMenuLivestream(self):
            nodeCount = 0

            # Hamburg
            nodeCount = nodeCount+1
            links = {}
            links[0] = SimpleLink("http://ndr_fs-lh.akamaihd.net/i/ndrfs_hh@119223/master.m3u8", 0)
            self.gui.buildVideoLink(DisplayObject("Hamburg", "", "", "", links, True), self, nodeCount)

            # Mecklenburg-Vorpommern
            nodeCount = nodeCount+1
            links = {}
            links[0] = SimpleLink("http://ndr_fs-lh.akamaihd.net/i/ndrfs_mv@119226/master.m3u8", 0)
            self.gui.buildVideoLink(DisplayObject("Mecklenburg-Vorpommern", "", "", "", links, True), self, nodeCount)

            # Niedersachsen
            nodeCount = nodeCount+1
            links = {}
            links[0] = SimpleLink("http://ndr_fs-lh.akamaihd.net/i/ndrfs_nds@119224/master.m3u8", 0)
            self.gui.buildVideoLink(DisplayObject("Niedersachsen", "", "", "", links, True), self, nodeCount)

            # Schleswig-Holstein
            nodeCount = nodeCount+1
            links = {}
            links[0] = SimpleLink("http://ndr_fs-lh.akamaihd.net/i/ndrfs_sh@119225/master.m3u8", 0)
            self.gui.buildVideoLink(DisplayObject("Schleswig-Holstein", "", "", "", links, True), self, nodeCount)

    def buildPageMenuVideoListVerpasst(self, link, initCount):
        self.gui.log("buildPageMenuVerpasst: " + link)

        htmlPage = self.loadPage(link)

        re_video_item = re.compile(
            '<div class="videolinks"><a href="(.*?)" title=".*?" class=\'button epgbutton\' >'
        )
        # won't parse "Beiträge", they are only cutted parts of the main
        # program
        video_items = re.findall(re_video_item, htmlPage)
        nodeCount = initCount + len(video_items)
        for video_link in video_items:
            if not re.compile("http://www.n-joy.de/.*").search(video_link):
                print video_link
                self.extractVideoInformation(video_link, None, nodeCount)


    def buildPageMenuVideoList(self, link, initCount):
        self.gui.log("buildPageMenu: " + link)

        htmlPage = self.loadPage(link)

        regex_extractVideoItems = re.compile(
            "<div class=\"teaserpadding\">"
            "(.*?)"
            "(</p>\n</div>\n</div>|\n</div>\n</div>\n</li>)", re.DOTALL)
        regex_extractVideoItemHref = re.compile("<a title=\".*?\" href=\"(.*?/[^/]*?\.html)\".*?>", re.DOTALL)
        regex_extractVideoItemDate = re.compile("<div class=\"subline\" style=\"cursor: pointer;\">.*?(\\d{2}\.\\d{2}\.\\d{4} \\d{2}:\\d{2})</div>")

        videoItems = regex_extractVideoItems.findall(htmlPage)
        nodeCount = initCount + len(videoItems)

        for videoItem in videoItems:
            print "link: {0}".format(link)
            print "videoItem: {0}".format(videoItem[0])
            if "<div class=\"subline\">" not in videoItem[0]:
                continue
            videoLink = regex_extractVideoItemHref.search(videoItem[0]).group(1)
            try:
                dateString = regex_extractVideoItemDate.search(videoItem[0]).group(1)
                dateTime = time.strptime(dateString, "%d.%m.%Y %H:%M")
            except:
                dateTime = None
            # TODO: Some videos from Extra 3 are located on http://www.n-joy.de/
            #       which cannot be parsed by this script, yet.
            if not re.compile("http://www.n-joy.de/.*").search(videoLink):
                self.extractVideoInformation(videoLink, dateTime, nodeCount)

        # Pagination (weiter)
        regex_extractNextPage = re.compile(
            "<a class=\"square button\" href=\"(.*?)\" title=\"(.*?)\".*?>"
        )
        for nextPageHref in regex_extractNextPage.finditer(htmlPage):
            menuItemName = nextPageHref.group(2).decode("UTF-8")
            link = self.rootLink+nextPageHref.group(1)
            self.gui.buildVideoLink(DisplayObject(menuItemName, "", "", "description", link, False), self, nodeCount)

    def buildPageMenu(self, link, initCount):

        print link
        if link[0:15] == "sendungverpasst":
            self.buildPageMenuSendungVerpasst(link[15:])
        elif link == "livestream":
            self.buildPageMenuLivestream()
        elif "/sendung_verpasst/" in link:
            self.buildPageMenuVideoListVerpasst(link, initCount)
        else:
            self.buildPageMenuVideoList(link, initCount)

    def searchVideo(self, searchText):
        searchText = searchText.encode("UTF-8")
        searchText = urllib.urlencode({"query": searchText})
        self.buildPageMenu(self.searchLink+searchText, 0)

# UNUSED
#     def extractVideoInformation(self, videoInfo, pubDate, nodeCount):
#         # Basis-Infos extrahieren
#         _regex_videoInfo = re.compile("<a href=\"(.*?)\".*?>.*?<img.*?src=\"(.*?)\".*?/>.*?<span class=\"runtime\" title=\"Spieldauer\">(.*?)</span>.*?<h4><a href=\".*?\".*?>(.*?)</a>", re.DOTALL)
#         videoInfoRE = _regex_videoInfo.search(videoInfo)
#
#         if videoInfoRE is not None:
#             videoLink = self.rootLink+videoInfoRE.group(1)
#             title = videoInfoRE.group(4).decode('utf-8')
#             # unused variables
#             # duration = videoInfoRE.group(3)
#             # picture = self.rootLink+videoInfoRE.group(2)
#             description = ""
#
#             # Bei der Suche ist bei den links ein http://www.ndr.de vorangestellt
#             if videoLink[0:18] == "http://www.ndr.deh":
#                 videoLink = videoLink[17:]
#
#             # Titel Bereinigen bei Suchergebnissen
#             title = title.replace('<span class="result">', '').replace('</span>', '')
#
#             videoPage = self.loadPage(videoLink)
#
#             # Bei "Sendung verpasst" wird keine (Kurz)Beschreibung ausgegeben, deswegen wird sie von der Detailseite geladen
#             _regex_videoInfo2 = re.compile("<div class=\"mplayer_textcontent\">.*?<p>(.*?)</p>", re.DOTALL)
#             videoInfoRE2 = _regex_videoInfo2.search(videoPage)
#
#             if videoInfoRE2 is not None:
#                 description = videoInfoRE2.group(1).decode('utf-8')
#
#             # Video Link extrahieren
#             _regex_extractVideoLink = re.compile("{src:'(.*?)', type:\"video/mp4\"},")

    def extractVideoInformation(self, videoLink, pubDate, nodeCount):

        regexFindVideoLink = re.compile("http://.*(hq.mp4|hi.mp4|lo.flv)")
        regexFindImageLink = re.compile("/.*v-ardgalerie.jpg")
        regexFindMediaData = re.compile(
            "<div class=\"padding group\">\\s*?<div class=\"textinfo\">\\s*?<h2.*?>"
            "(.*?)"
            "</h2>\\s*?.*?<div class=\"subline\">.*?</div>\\s*?<p.*?>"
            "(.*?)"
            "</p>", re.DOTALL
        )
        if not videoLink.startswith(self.rootLink):
            videoLink = self.rootLink+videoLink
        videoPage = self.loadPage(videoLink)

        print "videolink: {0}".format(videoLink)
        videoLink = {}
        videoLink[0] = SimpleLink(regexFindVideoLink.search(videoPage).group(0), 0)

        try:
            pictureLink = self.rootLink+regexFindImageLink.search(videoPage).group(0)
        except:
            pictureLink = None
        if '<article class="w66 ">' not in videoPage:
            searchResult = regexFindMediaData.search(videoPage)
            title = searchResult.group(1).decode('utf-8')
            description = searchResult.group(2).decode('utf-8')
        else:
            title = re.search(
                'var trackTitle = "(.*?)"',
                videoPage
            ).group(1).decode('utf-8')
            description = re.search(
                '<meta name="description" content="(.*?)"',
                videoPage
            ).group(1).decode('utf-8')

        self.gui.buildVideoLink(DisplayObject(title, "", pictureLink, description, videoLink, True, pubDate, 0), self, nodeCount)
