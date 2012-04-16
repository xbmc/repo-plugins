import urllib, re, os, sys
from abstract import AbstractHockey

from BeautifulSoup import BeautifulSoup
import xbmcplugin, xbmcaddon, xbmcgui
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

class LegacyHockey(AbstractHockey):
    def __init__(self, hockeyUtil,  mark_broken = False, debug = False):
        super(LegacyHockey, self).__init__(hockeyUtil)
        self.__dbg__ = debug
        self.mark_broken_cdn4_links = mark_broken

    def CATEGORY_LIVE_GAMES(self, mode):
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
        if self.__dbg__:            print ("hockeystreams: enter live games")
        html = urllib.urlopen("http://www4.hockeystreams.com/rss/streams.php")
        games = hs_rss.get_rss_streams(html, _debug_ = self.__dbg__)
        for gameName, url, date, real_date in sorted(games, key = lambda game: game[3]):
            if '-' in date:
                gameName = gameName + " " + date.split(' - ', 1)[1]
            self.util.addDir(gameName, url, mode, '', 1, gamename = gameName, fullDate = real_date)

    def CATEGORY_LAST_15_GAMES(self, mode):
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
        if self.__dbg__:            print ("hockeystreams: enter live games")
        html = urllib.urlopen("http://www6.hockeystreams.com/rss/archives.php")
        games = hs_rss.get_archive_rss_streams(html, _debug_ = self.__dbg__)
        for gameName, url, date, real_date in sorted(games, key = lambda game: game[3], reverse=True):
            gameName = gameName + " " + date
            url = hockeystreams + url
            self.util.addDir(gameName, url, mode, '', 1, gamename = gameName, fullDate = real_date)

    def ARCHIVE_GAMES_BY_DATE(self, year, month, day):
        mode = 1000
        if self.__dbg__:            print ("hockeystreams: enter archive games")
        archiveDate = self.get_date(day, month, year)
        url = archivestreams + '/' + archiveDate + '/'
        strip = ARCHIVE_STRIP
        games = self.find_hockey_game_names(url, hqArchives)
        for k, v in games.iteritems():
            gameName = k
            offset = gameName.index(strip) + len(strip)
            gameName = gameName[offset:]
            self.util.addDir(gameName, v, mode, '', 1, gamename = gameName)

    def CATEGORY_BY_TEAM(self, mode):
        url = archivestreams
        if self.__dbg__:            print ("hockeystreams: enter team")
        teamNames = re.compile('/hockey_archives/'+ self.archiveDate + '/[a-z]+_?[a-z]?') #simplified
        foundTeams = self.util.soupIt(url + "/" + self.archiveDate, "attrs", teamNames)
        for team in foundTeams:
            if self.__dbg__:                print ("hockeystreams: \t\t soupfound team %s" % (str(team)))

            ending = str(team['href'])
            teamPage = hockeystreams + ending
            teamName = os.path.basename(teamPage)
            teamName = re.sub('_|/', ' ', teamName)
            if self.__dbg__:                print ("hockeystreams: \t\t team %s" % teamName)

            image_name = teamName[0:teamName.rfind(' ')]
            image_name = image_name.replace(' ','')
    #        teamGIF = "http://www5.hockeystreams.com/images/teams/big/" + image_name + ".gif"
            teamGIF = "http://www5.hockeystreams.com/images/teams/" + image_name + ".gif"
            if self.__dbg__: print ("hockeystreams: \t\t team %s %s" % (teamName, teamGIF))
            self.util.addDir(teamName, teamPage, mode, teamGIF, 82)

    def ARCHIVE_GAMES_BY_TEAM(self, url, mode):
        if self.__dbg__:
            print ("hockeystreams: enter archive games")
        strip = ARCHIVE_STRIP
        games = self.find_hockey_game_names(url, hqArchives)
        for k, v in games.iteritems():
            gameName = k
            offset = gameName.find(strip) + len(strip)
            gameName = gameName[offset:]
            self.util.addDir(gameName, v, mode, '', 1000, gamename = gameName)

    def find_hockey_game_names(self, url, gameType):
        games = {}
        foundGames = self.util.soupIt(url, 'attrs', gameType)
        for test in foundGames:
            if self.__dbg__:
                print ("hockeystreams: \t\t foundGames %s" % str(test))
    
            ending = str(test['href'])
            gamePage = hockeystreams + ending
            gameName = os.path.dirname(gamePage)
            if "archive" in url and gameName.endswith(self.archiveDate):
                if self.__dbg__: print "\t\t\tskipping " + str(ending)
                continue
            gameName = re.sub('_|/', ' ', gameName)
    
            if self.__dbg__:
                print ("hockeystreams: \t\t gamename %s" % gameName)
            games[gameName] = gamePage
        del foundGames
        return games
    
    
    def QUALITY(self, url, gamename):
        if self.__dbg__:
            print ("hockeystreams: enter quality")
        games = self.find_qualities(url)
        if not self.mark_broken_cdn4_links:
            return self.QUALITY_quick(games, gamename)
        else:
            return self.QUALITY_slow(games, gamename)
    
    def QUALITY_slow(self, games, gamename):
        directLinks = {}
        silverLinks = {}
        for k, v in games.iteritems():
            if self.__dbg__: print "game qs: " + str(games)
            
            foundGames = self.util.soupIt(v,'input', None, True)
            for test in foundGames:
                if self.__dbg__: print("hockeystreams: \t\t soupfound directs %s" % test)
                if 'direct_link' in test.get('id',''):
                    directLink = test['value']
                    directLinks[k] = directLink
                if 'silverlight' in test.get('href','') and 'archive' in test.get('href',''):
                    silverLink = test.get('href','')
                    silverLinks["silverlight"] = silverLink
    
        for name,url in directLinks.iteritems():
            qualityName = name #name[name.rindex('/'):]
            if self.mark_broken_cdn4_links and 'cdn-a-4' in url:
                qualityName += "*"
            self.util.addLink(qualityName, gamename, '', url, '', 1)
        for name,url in silverLinks.iteritems():
            self.util.addLink("has " + name, name, '', url, '', 1)

    def QUALITY_quick(self, games, gamename):
        for quality, url in games.iteritems():
            if self.__dbg__:
                print "game qs: " + str(games)
            self.util.addLink(quality, gamename, '', url, '', 1, 2000)

    def find_qualities(self, url):
        games = {}
        if self.__dbg__:
            print ("hockeystreams: \t\t find qs ")
    
        if 'archive' in url:
            foundQs = self.util.soupIt(url, 'attrs', archivePlaybackTypes, True)
        else:
            foundQs = self.util.soupIt(url, 'attrs', livePlaybackTypes, True)
        for test in foundQs:
            if self.__dbg__:
                print ("hockeystreams: \t\t soupfound qs %s" % (str(test)))
    
            ending = str(test['href'])
            gamePage = hockeystreams + ending
            gameName = os.path.basename(gamePage)
            gameName = re.sub('_|/', ' ', gameName)
            if self.__dbg__:
                print ("hockeystreams: \t\t q: %s" % gameName)
            games[gameName] = gamePage
        del foundQs
        return games
