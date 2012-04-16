import urllib, re, os, sys
from abstract import AbstractHockey

from BeautifulSoup import BeautifulSoup
import xbmcplugin, xbmcaddon, xbmcgui
import gethtml
import hs_rss

__author__ = 'longman'

hqStreams = re.compile('/live_streams/.*')
hqArchives = re.compile('/hockey_archives/0/.*/[0-9]+')
archivePlaybackTypes = re.compile('/hockey_archives/0/.*/[0-9]+/[a-z_]+')
livePlaybackTypes = re.compile('/live_streams/.*/[0-9]+/[a-z_]+')

ARCHIVE_STRIP = " hockey archives 0 "
LIVE_STRIP = " live streams "

hockeystreams = 'http://www.hockeystreams.com'
archivestreams = hockeystreams + '/hockey_archives'

iStreamLive="http://www4.hockeystreams.com/rss/roku_live.php"
# incomplete e.g.: http://www4.hockeystreams.com/rss/roku_demand.php?date=10/31/2011
iStreamDate="http://www4.hockeystreams.com/rss/roku_demand.php?date="
# incomplete e.g. http://www4.hockeystreams.com/rss/roku_demand.php?team=toronto_maple_leafs
iStreamTeam="http://www4.hockeystreams.com/rss/roku_demand.php?team="


class IStreamHockey(AbstractHockey):
    def __init__(self, hockeyUtil,  debug = False):
        super(IStreamHockey, self).__init__(hockeyUtil)
        self.__dbg__ = debug

    def CATEGORY_LIVE_GAMES(self, mode):
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
        if self.__dbg__:            print ("hockeystreams: enter live games")
        html = urllib.urlopen(iStreamLive)
        games = hs_rss.get_rss_streams(html, _debug_ = self.__dbg__)
        for gameName, url, date, real_date in sorted(games, key = lambda game: game[3]):
            if url is None or url == '':
                gameName = "N/A " + gameName
            if '-' in date:
                gameName = gameName + " " + date.split(' - ', 1)[1]
            self.util.addDir(gameName, url, mode, '', 0, gamename = gameName, fullDate = real_date)
                #self.util.addLink(gameName, gameName, real_date, url, '', 1, mode)

    def CATEGORY_LAST_15_GAMES(self, mode):
        #mode = 2001
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
        if self.__dbg__:            print ("hockeystreams: enter live games")
        urlDate = self.get_date(self.today.day, self.today.month, self.today.year, '/')
        html = urllib.urlopen(iStreamDate +  urlDate)
        games = hs_rss.get_archive_rss_streams(html, _debug_ = self.__dbg__)
        for gameName, url, date, real_date in sorted(games, key = lambda game: game[3], reverse=True):
            gameName = gameName + " " + date
            #self.util.addLink(gameName, gameName, real_date, url, '', 1, mode)
            self.util.addDir(gameName, url, mode, '', 0, gamename = gameName, fullDate = real_date)
        urlDate = self.get_date(self.today.day - 1, self.today.month, self.today.year, '/')
        html = urllib.urlopen(iStreamDate +  urlDate)
        games = hs_rss.get_archive_rss_streams(html, _debug_ = self.__dbg__)
        for gameName, url, date, real_date in sorted(games, key = lambda game: game[3], reverse=True):
            gameName = gameName + " " + date
            #self.util.addLink(gameName, gameName, real_date, url, '', 1, mode)
            self.util.addDir(gameName, url, mode, '', 0, gamename = gameName, fullDate = real_date)

    def ARCHIVE_GAMES_BY_DATE(self, year, month, day):
        #mode = 2001
        mode = 1000
        if self.__dbg__:            print ("hockeystreams: enter archive games")
        archiveDate = self.get_date(day, month, year, '/')
        dateUrl = iStreamDate + archiveDate
        html = urllib.urlopen(dateUrl)
        games = hs_rss.get_archive_rss_streams(html, _debug_ = self.__dbg__)
        for gameName, url, date, real_date in sorted(games, key = lambda game: game[3], reverse=True):
            gameName = gameName + " " + date
            self.util.addDir(gameName, url, mode, '', 0, gamename = gameName, fullDate = real_date)
#            self.util.addLink(gameName, gameName, real_date, url, '', 1, mode)

    def CATEGORY_BY_TEAM(self, mode):
        url = archivestreams
        if self.__dbg__:            print ("hockeystreams: enter team")
        teamNames = re.compile('/hockey_archives/'+ self.archiveDate + '/[a-z]+_?[a-z]?') #simplified
        foundTeams = self.util.soupIt(url + "/" + self.archiveDate, "attrs", teamNames)
        for team in foundTeams:
            if self.__dbg__:                print ("hockeystreams: \t\t soupfound team %s" % (str(team)))
            ending = str(team['href'])
            teamName = os.path.basename(ending)
            teamPage = iStreamTeam + teamName
            teamName = re.sub('_|/', ' ', teamName)
            if self.__dbg__:                print ("hockeystreams: \t\t team %s" % teamName)

            image_name = teamName[0:teamName.rfind(' ')]
            image_name = image_name.replace(' ','')
    #        teamGIF = "http://www5.hockeystreams.com/images/teams/big/" + image_name + ".gif"
            teamGIF = "http://www5.hockeystreams.com/images/teams/" + image_name + ".gif"
            if self.__dbg__: print ("hockeystreams: \t\t team %s %s" % (teamName, teamGIF))
            self.util.addDir(teamName, teamPage, mode, teamGIF, 82)

    def ARCHIVE_GAMES_BY_TEAM(self, url, mode):
        #mode = 2001
        if self.__dbg__: print ("hockeystreams: enter archive games")
        html = urllib.urlopen(url)
        games = hs_rss.get_archive_rss_streams(html, _debug_ = self.__dbg__)
        for gameName, url, date, real_date in sorted(games, key = lambda game: game[3], reverse=True):
            gameName = gameName + " " + date
            #self.util.addLink(gameName, gameName, real_date, url, '', 1, mode)
            self.util.addDir(gameName, url, mode, '', 0, gamename = gameName, fullDate = real_date)

    bandwidthMatch = re.compile("BANDWIDTH=([0-9]+),?")

    def QUALITY(self, url, gamename):
        if self.__dbg__: print "hockeystreams: enter quality"
        mode = 2001
        real_date = str(self.today) # TODO
        # add the m3u8 first
        gameName = "Live " + gamename
        self.util.addLink(gameName, gameName, real_date, url, '', 1, mode)
        # then add the composed feeds
        if self.__dbg__: print "hockeystreams reading " + url
        m3u8Outer = gethtml.get(url).splitlines()
        if "#EXTM3U" in m3u8Outer[0]:#.readline():
            bandwidthLine = True
            loops = m3u8Outer
            for line in loops[1:]:
                line = line.strip()
                if bandwidthLine:
                    bandwidth = re.search(self.bandwidthMatch, line).group(1)
                    gameName = str(int(bandwidth)/1000) + self.util.__settings__.getLocalizedString(40500) + " " + gamename
                else:
                    url = line
                    self.util.addLink(gameName, gameName, real_date, url, '', 1, mode)
                bandwidthLine = not bandwidthLine
