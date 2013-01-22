import urllib, urllib2, re, sys, os
import xbmc, xbmcaddon, xbmcgui, xbmcplugin

import CommonFunctions
from BeautifulSoup import BeautifulSoup

pluginhandle=int(sys.argv[1])

class Day9:

    USERAGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8"
    __settings__ = xbmcaddon.Addon(id='plugin.video.day9')
    __language__ = __settings__.getLocalizedString
    common = CommonFunctions

    # this should probably move into default.py or it's own actions.py and not be so iffy
    def action(self, params):
        get = params.get
        if (get("action") == "showTitles"):
            self.showTitles(params)
        if (get("action") == "showGames"):
            self.showGames(params)
        if (get("action") == "removeSearch"):
            self.removeSearch(params)
        if (get("action") == "newSearchDialog"):
            self.newSearchDialog(params)
        if (get("action") == "showSearch"):
            self.showSearch(params)
        if (get("action") == "showVideo"):
            self.showVideo(params)

    # ------------------------------------- Menu functions ------------------------------------- #

    # display the root menu
    def root(self):
        self.addCategory(self.__language__(31000), 'http://day9.tv/archives', 'showTitles')
        self.addCategory(self.__language__(31002), '', 'showSearch')
        # these need to be dynamic
        self.addCategory('Funday Monday', 'http://day9.tv/archives?q=%22Funday%20Monday%22', 'showTitles')
        self.addCategory('Newbie Tuesday', 'http://day9.tv/archives?q=%22Newbie%20Tuesday%22', 'showTitles')
        self.addCategory('MetaDating', 'http://day9.tv/archives?q=MetaDating', 'showTitles')
        self.addCategory('Red Bull LAN', 'http://day9.tv/archives?q=%22Red%20Bull%20LAN%22', 'showTitles')
        self.addCategory('Amnesia: The Dark Descent', 'http://day9.tv/archives?q=%22Amnesia%3A%20The%20Dark%20Descent%22', 'showTitles')
        self.addCategory('IEM GamesCom', 'http://day9.tv/archives?q=%22IEM%20GamesCom%22', 'showTitles')
        self.addCategory('Protoss', 'http://day9.tv/archives?q=protoss', 'showTitles')
        self.addCategory('Zerg', 'http://day9.tv/archives?q=zerg', 'showTitles')
        self.addCategory('Terran', 'http://day9.tv/archives?q=terran', 'showTitles')


    # ------------------------------------- Add functions ------------------------------------- #


    def addCategory(self, title, url, action, menu=None):
        url=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&title="+title+"&action="+urllib.quote_plus(action)
        listitem=xbmcgui.ListItem(title,iconImage="DefaultFolder.png", thumbnailImage="DefaultFolder.png")
        listitem.setInfo( type="Video", infoLabels={ "Title": title } )
        if menu:
            listitem.addContextMenuItems(menu, replaceItems=True)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True)

    def addVideo(self,title,youtubeid,description='',picture=''):
        url=sys.argv[0]+"?youtubeid="+youtubeid+"&action=showVideo"
        liz=xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage="DefaultVideo.png")
        liz.setInfo( type="Video", infoLabels={ "Title": title, "Plot" : description } )
        liz.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)

    # ------------------------------------- Show functions ------------------------------------- #

    def newSearchDialog(self, params = {}):
        search = self.common.getUserInput(self.__language__(32000))
        search=urllib.quote_plus(search)
        save = xbmcgui.Dialog().yesno(self.__language__(32010), self.__language__(32015) % search)
        if save:
            self.saveSearch(search)
        params['url']='http://day9.tv/archives?q='+search
        self.showTitles(params=params)

    def showSearch(self, params = {}):
        get = params.get
        self.addCategory(self.__language__(32000), 'url', 'newSearchDialog')
        searches = self.getSearch() 
        for search in searches:
            cm = []
            cm.append((self.__language__(32500) % search, 'XBMC.RunPlugin(%s?action=removeSearch&search=%s)' % (sys.argv[0], search)))
            url='http://day9.tv/archives?q='+search
            self.addCategory(search, url, 'showTitles', menu=cm)

    def removeSearch(self, params = {}):
        get = params.get
        search = get("search")
        delete = xbmcgui.Dialog().yesno(self.__language__(32598), self.__language__(32599) % search)
        if delete:
            self.deleteSearch(search)

    def showTitles(self, params = {}):
        get = params.get
        link = self.getRequest(get("url"))
        tree = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
        # narrow down the search to get rid of upcoming shows
        # I'd like to add them just to inform people of what/when things are
        # happening but there isn't good markup to isolate them.  I guess I
        # could excise the existing shows and say whatever is left is
        # upcoming...
        results=tree.find('ul', { "id" : "results" })
        for r in results.findAll('h3'):
            link = r.contents[0]
            self.addCategory(str(link.contents[0]), 'http://day9.tv/' + str(link['href']), 'showGames')
                
        try: 
            nextpage = tree.find('li', { "class" : "next" }).find('a').get('href')
            if nextpage: 
                url = 'http://day9.tv/archives/'+nextpage
                self.addCategory(self.__language__(31001), url, 'showTitles')
        except:
            return

    def showGames(self, params = {}):
        get = params.get
        link = self.getRequest(get("url"))
        tree = BeautifulSoup(link)
	airdate = tree.find('time')
        # instead of using the title from get("title") we're grabbing it from the page to avoid HTML %20 and such.  Could probably strip it with HTML_ENTITIES again if need be.  This became a problem with frodo I think.  It no longer parses the HTML.  
        title = tree.find('h1', { "name" : "title" }).contents[0]
        try: 
            description = tree.find(text='Description').findNext('p')
        except:
            description = ''
        i=0
        for video in tree.findAll('iframe'):
            v=re.match('http://www.youtube.com/embed/(.*)', video.get('src'))
            i=i+1
            self.addVideo(str(title)+' Part '+str(i), youtubeid=v.group(1), description=description)

    def showVideo(self, params = {}):
        get = params.get
        youTubeId = get("youtubeid")
        # need to start a video before you can hand it over youtube plugin
        req = urllib2.Request('http://www.youtube.com/embed/'+youTubeId)
        response = urllib2.urlopen(req)
        link = response.read()
        response.close()

        stream_url = "plugin://plugin.video.youtube/?action=play_video&videoid=" + youTubeId
        item = xbmcgui.ListItem(path=stream_url)
        item.setProperty("IsPlayable","true")
        xbmcplugin.setResolvedUrl(pluginhandle, True, item)
        return False

    # ------------------------------------- Data functions ------------------------------------- #


    # need to work out how editing is going to work for this.  Also don't know
    # if it matters but I'm storing searches quoted where other people stored
    # them unquoted.  I feel like this way is safer.
    def saveSearchList(self, searches):
        self.__settings__.setSetting("saved_searches", repr(searches))

    def saveSearch(self, search):
        searches = self.getSearch()
        searches.append(urllib.quote_plus(search))
        self.saveSearchList(searches)

    def deleteSearch(self, search):
        searches = self.getSearch()
        for count, s in enumerate(searches):
            if (search == s):
                del (searches[count])
                self.saveSearchList(searches)
                break
        xbmc.executebuiltin("Container.Refresh")
 
    def getSearch(self):
        try:
            searches = eval(self.__settings__.getSetting("saved_searches"))
        except:
            searches = []
        return searches


    def getParams(self, paramList):
        splitParams = paramList[paramList.find('?')+1:].split('&')
        paramsFinal = {}
        for value in splitParams:
            splitParams = value.split('=')
            type = splitParams[0]
            content = splitParams[1]
            if type == 'url':
                content = urllib.unquote_plus(content)
            paramsFinal[type] = content
        return paramsFinal

    def getRequest(self, url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', self.USERAGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link
