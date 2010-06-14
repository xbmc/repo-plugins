import sys
import urllib
import ted_talks_scraper
import xbmc
import xbmcplugin
import xbmcgui
from talkDownloader import Download
import xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.ted.talks')
getLS = __settings__.getLocalizedString

#getLS = xbmc.getLocalizedString
TedTalks = ted_talks_scraper.TedTalks()


class updateArgs:

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.iteritems():
            if value == 'None':
                kwargs[key] = None
            else:
                kwargs[key] = urllib.unquote_plus(kwargs[key])
        self.__dict__.update(kwargs)


class UI:

    def __init__(self):
        self.main = Main(checkMode = False)
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')

    def endofdirectory(self, sortMethod = 'title'):
        # set sortmethod to something xbmc can use
        if sortMethod == 'title':
            sortMethod = xbmcplugin.SORT_METHOD_LABEL
        elif sortMethod == 'date':
            sortMethod = xbmcplugin.SORT_METHOD_DATE
        #Sort methods are required in library mode.
        xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod)
        #If name is next or previous, then the script arrived here from a navItem, and won't to add to the heirarchy
        if self.main.args.name in [getLS(30020), getLS(30021)]:
            dontAddToHierarchy = True
        else:
            dontAddToHierarchy = False
        #let xbmc know the script is done adding items to the list.
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]), updateListing = dontAddToHierarchy)

    def addItem(self, info, isFolder=True):
        #Defaults in dict. Use 'None' instead of None so it is compatible for quote_plus in parseArgs
        info.setdefault('url', 'None')
        info.setdefault('Thumb', 'None')
        info.setdefault('Icon', info['Thumb'])
        #create params for xbmcplugin module
        u = sys.argv[0]+\
            '?url='+urllib.quote_plus(info['url'])+\
            '&mode='+urllib.quote_plus(info['mode'])+\
            '&name='+urllib.quote_plus(info['Title'])+\
            '&icon='+urllib.quote_plus(info['Thumb'])
        #create list item
        li=xbmcgui.ListItem(label = info['Title'], iconImage = info['Icon'], thumbnailImage = info['Thumb'])
        li.setInfo(type='Video', infoLabels=info)
        #for videos, replace context menu with queue and add to favorites
        if not isFolder:
            li.setProperty("IsPlayable", "true")#let xbmc know this can be played, unlike a folder.
            #add context menu items to non-folder items.
            contextmenu = [(getLS(13347), 'Action(Queue)')]
            contextmenu += [(getLS(30096), 'RunPlugin(%s?downloadVideo=%s)' % (sys.argv[0], info['url']))]
            #only add add to favorites context menu if the user has a username & isn't already looking at favorites.
            if self.main.settings['username']:
                if self.main.args.mode == 'favorites':
                    contextmenu += [(getLS(30093), 'RunPlugin(%s?removeFromFavorites=%s)' % (sys.argv[0], info['url']))]
                else:
                    contextmenu += [(getLS(30090), 'RunPlugin(%s?addToFavorites=%s)' % (sys.argv[0], info['url']))]
            #replaceItems=True replaces the useless one with the two defined above.
            li.addContextMenuItems(contextmenu, replaceItems=True)
        #for folders, completely remove contextmenu, as it is totally useless.
        else:
            li.addContextMenuItems([], replaceItems=True)
        #add item to list
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=li, isFolder=isFolder)

    def playVideo(self):
        video = TedTalks.getVideoDetails(self.main.args.url)
        li=xbmcgui.ListItem(video['Title'],
                            iconImage = self.main.args.icon,
                            thumbnailImage = self.main.args.icon,
                            path = video['url'])
        li.setInfo(type='Video', infoLabels=video)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)

    def navItems(self, navItems, mode):
        if navItems['next']:
            self.addItem({'Title': getLS(30020), 'url':navItems['next'], 'mode':mode})
        if navItems['previous']:
            self.addItem({'Title': getLS(30021), 'url':navItems['previous'], 'mode':mode})

    def showCategories(self):
        self.addItem({'Title':getLS(30001), 'mode':'newTalks', 'Plot':getLS(30031)})#new
        self.addItem({'Title':getLS(30002), 'mode':'speakers', 'Plot':getLS(30032)})#speakers
        self.addItem({'Title':getLS(30003), 'mode':'themes', 'Plot':getLS(30033)})#themes
        #self.addItem({'Title':getLS(30004), 'mode':'search', 'Plot':getLS(30034)})#search
        if self.main.settings['username']:
            self.addItem({'Title':getLS(30005), 'mode':'favorites', 'Plot':getLS(30035)})#favorites
        self.endofdirectory()

    def newTalks(self):
        newMode = 'playVideo'
        newTalks = TedTalks.NewTalks(self.main.args.url)
        #add talks to the list
        for talk in newTalks.getNewTalks():
            talk['mode'] = newMode
            self.addItem(talk, isFolder = False)
        #add nav items to the list
        self.navItems(newTalks.navItems, self.main.args.mode)
        #end the list
        self.endofdirectory(sortMethod = 'date')

    def speakers(self):
        newMode = 'speakerVids'
        speakers = TedTalks.Speakers(self.main.args.url)
        #add speakers to the list
        for speaker in speakers.getAllSpeakers():
            speaker['mode'] = newMode
            self.addItem(speaker, isFolder = True)
        #add nav items to the list
        self.navItems(speakers.navItems, self.main.args.mode)
        #end the list
        self.endofdirectory()

    def speakerVids(self):
        newMode = 'playVideo'
        speakers = TedTalks.Speakers(self.main.args.url)
        for talk in speakers.getTalks():
            talk['mode'] = newMode
            self.addItem(talk, isFolder = False)
        #end the list
        self.endofdirectory()

    def themes(self):
        newMode = 'themeVids'
        themes = TedTalks.Themes(self.main.args.url)
        #add themes to the list
        for theme in themes.getThemes():
            theme['mode'] = newMode
            self.addItem(theme, isFolder = True)
        #end the list
        self.endofdirectory()

    def themeVids(self):
        newMode = 'playVideo'
        themes = TedTalks.Themes(self.main.args.url)
        for talk in themes.getTalks():
            talk['mode'] = newMode
            self.addItem(talk, isFolder = False)
        self.endofdirectory()

    def favorites(self):
        newMode = 'playVideo'
        #attempt to login
        if self.main.isValidUser():
            favorites = TedTalks.Favorites()
            for talk in favorites.getFavoriteTalks(self.main.user):
                talk['mode'] = newMode
                self.addItem(talk, isFolder = False)
            self.endofdirectory()


class Main:

    def __init__(self, checkMode = True):
        self.user = None
        self.parseArgs()
        self.getSettings()
        if checkMode:
            self.checkMode()

    def parseArgs(self):
        # call updateArgs() with our formatted argv to create the self.args object
        if (sys.argv[2]):
            exec "self.args = updateArgs(%s')" % (sys.argv[2][1:].replace('&', "',").replace('=', "='"))
        else:
            # updateArgs will turn the 'None' into None.
            # Don't simply define it as None because unquote_plus in updateArgs will throw an exception.
            # This is a pretty ugly solution, but fuck it :(
            self.args = updateArgs(mode = 'None', url = 'None', name = 'None')

    def getSettings(self):
        self.settings = dict()
        self.settings['username'] = __settings__.getSetting('username')
        self.settings['password'] = __settings__.getSetting('password')
        self.settings['downloadMode'] = __settings__.getSetting('downloadMode')
        self.settings['downloadPath'] = __settings__.getSetting('downloadPath')

    def isValidUser(self):
        self.user = TedTalks.User(self.settings['username'], self.settings['password'])
        if self.user:
            return True
        else:
            xbmcgui.Dialog().ok(getLS(30050), getLS(30051))
            return False

    def addToFavorites(self, url):
        if self.isValidUser():
            successful = TedTalks.Favorites().addToFavorites(self.user, url)
            if successful:
                xbmc.executebuiltin('Notification(%s,%s,)' % (getLS(30000), getLS(30091)))
            else:
                xbmc.executebuiltin('Notification(%s,%s,)' % (getLS(30000), getLS(30092)))

    def removeFromFavorites(self, url):
        if self.isValidUser():
            successful = TedTalks.Favorites().removeFromFavorites(self.user, url)
            if successful:
                xbmc.executebuiltin('Notification(%s,%s,)' % (getLS(30000), getLS(30094)))
            else:
                xbmc.executebuiltin('Notification(%s,%s,)' % (getLS(30000), getLS(30095)))

    def downloadVid(self, url):
        video = TedTalks.getVideoDetails(url)
        if self.settings['downloadMode'] == 'true':
            downloadPath = xbmcgui.Dialog().browse(3, getLS(30096), 'files')
        else:
            downloadPath = self.settings['downloadPath']
        if downloadPath:
            Download(video['Title'], video['url'], downloadPath)

    def checkMode(self):
        mode = self.args.mode
        if mode is None:
            UI().showCategories()
        elif mode == 'playVideo':
            UI().playVideo()
        elif mode == 'newTalks':
            UI().newTalks()
        elif mode == 'speakers':
            UI().speakers()
        elif mode == 'speakerVids':
            UI().speakerVids()
        elif mode == 'themes':
            UI().themes()
        elif mode == 'themeVids':
            UI().themeVids()
        elif mode == 'favorites':
            UI().favorites()
