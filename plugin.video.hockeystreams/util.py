import sys, urllib
import xbmcplugin, xbmcaddon, xbmcgui
from BeautifulSoup import BeautifulSoup

import weblogin, gethtml

super_verbose_logging = False

class HockeyUtil:
    def __init__(self, settings, cookiepath):
        self.__settings__ = settings
        self.cookiepath = cookiepath
        self.__dbg__ = settings.getSetting("debug") == "true"

    def addDir(self, name, url, mode, icon, count, year=-1, month=-1, day=-1, gamename = None, fullDate = None):
        u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
        if gamename is not None:
            u += "&gamename=" + urllib.quote_plus(gamename)
        if year > 0:
            u += "&year=" + str(year)
            if month > 0:
                u += "&month=" + str(month)
                if day > 0:
                    u += "&day=" + str(day)
        liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=icon)
        if fullDate is not None:
            liz.setInfo(type="Video", infoLabels={"Title": name, "Date" : str(fullDate)})
        else:
            liz.setInfo(type="Video", infoLabels={"Title": name})

        if self.__dbg__:
            print str("about to add url %s modes %s name %s  directory" % (u, str(mode), name))
            print str("about to add icon: " + icon)
        ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=str(u), listitem=liz, isFolder=True, totalItems=count)
        return ok

    def addLink(self, name, gamename, date, url, icon, count, mode = 2001):
        u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name) + \
            "&gamename=" + urllib.quote_plus(gamename)
        liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=icon)
        liz.setInfo(type="Video", infoLabels={"Title": gamename, "Date": date})
        liz.setProperty('isPlayable', 'true')
        if self.__dbg__: print ("about to add %s %s %d link" % (name, u, int(count)))
        ok = xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, isFolder=False, totalItems=count)
        return ok

    def soupIt(self, currentUrl, selector, gameType, loginRequired = False):
        if self.__dbg__:
            if gameType is not None:
                print ("hockeystreams: enter soupIt url %s selector %s gameType %s" % (
                currentUrl, selector, gameType.pattern))
            else:
                print (
                "hockeystreams: enter soupIt  url %s selector %s gameType %s" % (currentUrl, selector, "empty"))
        if loginRequired:
            try:
                html = gethtml.get(currentUrl, cookiepath = self.cookiepath, debug = self.__dbg__)
                if html is None:
                    raise IndexError
            except IndexError:
                self.__settings__.openSettings()
                self.login()
                return self.soupIt(currentUrl, selector, gameType, loginRequired)
        else:
            html = gethtml.get(currentUrl, debug = self.__dbg__)

        if self.__dbg__:            print ("hockeystreams: \t\tfetch browser result %s " % html)
        if self.__dbg__:            print ("hockeystreams: \t\t soupIt %s " % html)
        soup = BeautifulSoup(''.join(html))

        if selector == 'input':
            found = soup.findAll('input')
            found.extend(soup.findAll('href'))
        else:
            found = soup.findAll(attrs={'href': gameType})
        del selector
        print "hockeystreams: soupit: found count " + str(len(found))
        return found



    def login(self):
        if self.__dbg__:            print ("hockeystreams: login attempt")
        if not self.__settings__.getSetting('username') or not self.__settings__.getSetting('password'):
            self.__settings__.openSettings()
            return False
        if not weblogin.doLogin(self.cookiepath, self.__settings__.getSetting('username'), self.__settings__.getSetting('password'), self.__dbg__):
            if self.__dbg__:                print ("hockeystreams: login fail")
            return False
        return True
