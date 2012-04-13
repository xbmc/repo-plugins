import sys
import urllib
import ted_talks_scraper
from talkDownloader import Download
from model.fetcher import Fetcher
from model.user import User
from model.rss_scraper import NewTalksRss
from model.favorites_scraper import Favorites
import menu_util
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.ted.talks')
getLS = __settings__.getLocalizedString


def login(user_scraper, username, password):
    user_details = user_scraper.login(username, password)
    if not user_scraper:
        xbmcgui.Dialog().ok(getLS(30050), getLS(30051))
    return user_details


class UI:

    def __init__(self, logger, get_HTML, ted_talks, user, settings, args):
        self.logger = logger
        self.get_HTML = get_HTML
        self.ted_talks = ted_talks
        self.user = user
        self.settings = settings
        self.args = args
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')

    def endofdirectory(self, sortMethod = 'title'):
        # set sortmethod to something xbmc can use
        if sortMethod == 'title':
            sortMethod = xbmcplugin.SORT_METHOD_LABEL
        elif sortMethod == 'date':
            sortMethod = xbmcplugin.SORT_METHOD_DATE
        #Sort methods are required in library mode.
        xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod)
        #let xbmc know the script is done adding items to the list.
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]), updateListing = False)

    def addItem(self, info, isFolder = True):
        #Defaults in dict. Use 'None' instead of None so it is compatible for quote_plus in parseArgs
        #create params for xbmcplugin module
        args = {}
        for key1, key2 in {'url': 'url', 'mode': 'mode', 'Title': 'name', 'Thumb': 'icon'}.iteritems():
            if key1 in info:
                if info[key1] is None:
                    self.logger("'None' in item dict: " + info)
                else:
                    args[key2] = urllib.quote_plus(info[key1].encode('ascii', 'ignore'))
        
        u = sys.argv[0] + '?' + "&".join(key + '=' + value for key, value in args.iteritems())
                        
        info.setdefault('url', 'None')
        info.setdefault('Thumb', 'None')
        info.setdefault('Icon', info['Thumb'])
        #create list item
        if info['Title'].startswith(" "):
            title = info['Title'][1:]
        else:
            title = info['Title']  
        li = xbmcgui.ListItem(label = title, iconImage = info['Icon'], thumbnailImage = info['Thumb'])
        li.setInfo(type='Video', infoLabels = info)
        #for videos, replace context menu with queue and add to favorites
        if not isFolder:
            li.setProperty("IsPlayable", "true")#let xbmc know this can be played, unlike a folder.
            context_menu = menu_util.create_context_menu(getLS = getLS)
            li.addContextMenuItems(context_menu, replaceItems = True)
        else:
            #for folders, completely remove contextmenu, as it is totally useless.
            li.addContextMenuItems([], replaceItems = True)
        #add item to list
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=li, isFolder=isFolder)

    def playVideo(self):
        video = self.ted_talks.getVideoDetails(self.args['url'])
        li=xbmcgui.ListItem(video['Title'],
                            iconImage = self.args['icon'],
                            thumbnailImage = self.args['icon'],
                            path = video['url'])
        li.setInfo(type='Video', infoLabels=video)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)

    def navItems(self, navItems, mode):
        if navItems['next']:
            self.addItem({'Title': getLS(30020), 'url':navItems['next'], 'mode':mode})
        if navItems['previous']:
            self.addItem({'Title': getLS(30021), 'url':navItems['previous'], 'mode':mode})

    def showCategories(self):
        self.addItem({'Title':getLS(30001), 'mode':'newTalksRss', 'Plot':getLS(30031)})#new RSS
        self.addItem({'Title':getLS(30002), 'mode':'speakers', 'Plot':getLS(30032)})#speakers
        self.addItem({'Title':getLS(30003), 'mode':'themes', 'Plot':getLS(30033)})#themes
        #self.addItem({'Title':getLS(30004), 'mode':'search', 'Plot':getLS(30034)})#search
        if self.settings['username']:
            self.addItem({'Title':getLS(30005), 'mode':'favorites', 'Plot':getLS(30035)})#favorites
        self.endofdirectory()
        
    def newTalksRss(self):
        newTalks = NewTalksRss(self.logger)
        for talk in newTalks.get_new_talks():
            li = xbmcgui.ListItem(label = talk['title'], iconImage = talk['thumb'], thumbnailImage = talk['thumb'])
            li.setProperty("IsPlayable", "true")
            li.setInfo('video', {'date':talk['date'], 'duration':talk['duration'], 'plot':talk['plot']})
            favorites_action = None
            if self.settings['username'] != None:
                favorites_action = "add"
            context_menu = menu_util.create_context_menu(getLS = getLS, url = talk['link'], favorites_action = favorites_action, talkID = talk['id'])
            li.addContextMenuItems(context_menu, replaceItems = True)
            xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = talk['link'], listitem = li)
        self.endofdirectory(sortMethod = 'date')

    def speakers(self):
        newMode = 'speakerVids'
        speakers = ted_talks_scraper.Speakers(self.get_HTML, self.args.get('url'))
        #add speakers to the list
        for speaker in speakers.getAllSpeakers():
            speaker['mode'] = newMode
            self.addItem(speaker, isFolder = True)
        #add nav items to the list
        self.navItems(speakers.navItems, self.args['mode'])
        #end the list
        self.endofdirectory()

    def speakerVids(self):
        newMode = 'playVideo'
        speakers = ted_talks_scraper.Speakers(self.get_HTML, self.args.get('url'))
        for talk in speakers.getTalks():
            talk['mode'] = newMode
            self.addItem(talk, isFolder = False)
        #end the list
        self.endofdirectory()

    def themes(self):
        newMode = 'themeVids'
        themes = self.ted_talks.Themes(self.get_HTML, self.args.get('url'))
        #add themes to the list
        for theme in themes.getThemes():
            theme['mode'] = newMode
            self.addItem(theme, isFolder = True)
        #end the list
        self.endofdirectory()

    def themeVids(self):
        newMode = 'playVideo'
        themes = self.ted_talks.Themes(self.get_HTML, self.args.get('url'))
        for talk in themes.getTalks():
            talk['mode'] = newMode
            self.addItem(talk, isFolder = False)
        self.endofdirectory()

    def favorites(self):
        newMode = 'playVideo'
        #attempt to login
        userID, realname = login(self.user, self.settings['username'], self.settings['password'])
        if userID:
            for talk in Favorites(self.logger, self.get_HTML).getFavoriteTalks(userID):
                talk['mode'] = newMode
                self.addItem(talk, isFolder = False)
            self.endofdirectory()


class Main:

    def __init__(self, logger, args_map):
        self.logger = logger
        self.args_map = args_map
        self.getSettings()
        self.get_HTML = Fetcher(logger, xbmc.translatePath).getHTML
        self.user = User(self.get_HTML)
        self.ted_talks = ted_talks_scraper.TedTalks(self.get_HTML)

    def getSettings(self):
        self.settings = dict()
        self.settings['username'] = __settings__.getSetting('username')
        self.settings['password'] = __settings__.getSetting('password')
        self.settings['downloadMode'] = __settings__.getSetting('downloadMode')
        self.settings['downloadPath'] = __settings__.getSetting('downloadPath')

    def set_favorite(self, talkID, is_favorite):
        """
        talkID ID for the talk.
        is_favorite True to set as a favorite, False to unset.
        """
        if login(self.user, self.settings['username'], self.settings['password']):
            favorites = Favorites(self.logger, self.fetcher.getHTML)
            if is_favorite:
                successful = favorites.addToFavorites(talkID)
            else:
                successful = favorites.removeFromFavorites(talkID)
            notification_messages = {(True, True): 30091, (True, False): 30092, (False, True): 30094, (False, False): 30095}
            notification_message = notification_messages[(is_favorite, successful)]
            xbmc.executebuiltin('Notification(%s,%s,)' % (getLS(30000), getLS(notification_message)))

    def downloadVid(self, url):
        video = self.ted_talks.getVideoDetails(url)
        if self.settings['downloadMode'] == 'true':
            downloadPath = xbmcgui.Dialog().browse(3, getLS(30096), 'files')
        else:
            downloadPath = self.settings['downloadPath']
        if downloadPath:
            Download(video['Title'], video['url'], downloadPath)

    def run(self):
        # TODO Make these all modes for consistency
        if 'addToFavorites' in self.args_map:
            self.set_favorite(self.args_map['addToFavorites'], True)
        if 'removeFromFavorites' in self.args_map:
            self.set_favorite(self.args_map['removeFromFavorites'], False)
        if 'downloadVideo' in self.args_map:
            self.downloadVid(self.args_map('downloadVideo'))
        
        ui = UI(self.logger, self.get_HTML, self.ted_talks, self.user, self.settings, self.args_map)
        if 'mode' not in self.args_map:
            ui.showCategories()
        else:
            mode = self.args_map['mode']
            if mode == 'playVideo':
                ui.playVideo()
            elif mode == 'newTalksRss':
                ui.newTalksRss()
            elif mode == 'speakers':
                ui.speakers()
            elif mode == 'speakerVids':
                ui.speakerVids()
            elif mode == 'themes':
                ui.themes()
            elif mode == 'themeVids':
                ui.themeVids()
            elif mode == 'favorites':
                ui.favorites()
