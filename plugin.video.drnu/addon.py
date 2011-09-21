import pickle
import os
import sys
import cgi as urlparse
import urllib2
import re
import datetime

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import nuapi

class NuAddon(object):
    def __init__(self):
        self.api = nuapi.DrNuApi(CACHE_PATH, 60)

        # load favorites
        self.favorites = list()
        if os.path.exists(FAVORITES_PATH):
            try:
                self.favorites = pickle.load(open(FAVORITES_PATH, 'rb'))
            except Exception:
                pass

        # load recently watched
        self.recentlyWatched = list()
        if os.path.exists(RECENT_PATH):
            try:
                self.recentlyWatched = pickle.load(open(RECENT_PATH, 'rb'))
            except Exception:
                pass


    def _save(self):
        # save favorites
        self.favorites.sort()
        pickle.dump(self.favorites, open(FAVORITES_PATH, 'wb'))

        self.recentlyWatched = self.recentlyWatched[0:10] # Limit to ten items
        pickle.dump(self.recentlyWatched, open(RECENT_PATH, 'wb'))

    def showMainMenu(self):
        fanartImage = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

        # All Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30000), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'all.png'))
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?show=allProgramSeries', item, isFolder = True)
        # Program Series label
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30012), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'tag.png'))
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?show=programSeriesLabels', item, isFolder = True)
        # Latest
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30001), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'new.png'))
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?show=newest', item, isFolder = True)
        # Most viewed
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30011), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'eye.png'))
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?show=mostViewed', item, isFolder = True)
        # Spotlight
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30002), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'star.png'))
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?show=spotlight', item, isFolder = True)
        # Last chance
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30014), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'clock.png'))
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?show=lastChance', item, isFolder = True)
        # Search videos
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30003), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'search.png'))
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?show=search', item, isFolder = True)
        # Recently watched Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30007), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'eye-star.png'))
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?show=recentlyWatched', item, isFolder = True)
        # Favorite Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30008), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'plusone.png'))
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?show=favorites', item, isFolder = True)

        xbmcplugin.endOfDirectory(HANDLE)

    def showProgramSeriesVideos(self, slug):
        self.listVideos(self.api.getProgramSeriesVideos(slug))

    def showNewestVideos(self):
        self.listVideos(self.api.getNewestVideos())

    def showSpotlightVideos(self):
        self.listVideos(self.api.getSpotlightVideos())

    def showMostViewedVideos(self):
        self.listVideos(self.api.getMostViewedVideos())

    def showLastChanceVideos(self):
        self.listVideos(self.api.getLastChanceVideos())

    def showFavorites(self):
        nuAddon.showProgramSeries(self.favorites, False)

    def showRecentlyWatched(self):
        videos = list()

        for videoId in self.recentlyWatched:
            video = self.api.getVideoById(videoId)

            if video is not None:
                videos.append(video)
                
        if not videos:
            xbmcplugin.endOfDirectory(HANDLE, succeeded = False)
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013))
        else:
            self.listVideos(videos)

    def showProgramSeries(self, limitToSlugs = None, addToFavorites = True, label = None):
        programs = self.api.getProgramSeries(limitToSlugs, label)

        if not programs:
            xbmcplugin.endOfDirectory(HANDLE, succeeded = False)
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013))
        else:
            for program in programs:
                infoLabels = {}

                if program['newestVideoPublishTime'] is not None:
                    publishTime = self.parseDate(program['newestVideoPublishTime'])
                    if publishTime:
                        infoLabels['plotoutline'] = ADDON.getLocalizedString(30004) % publishTime.strftime('%d. %b %Y kl. %H:%M')
                        infoLabels['date'] = publishTime.strftime('%d.%m.%Y')
                        infoLabels['year'] = int(publishTime.strftime('%Y'))
                        infoLabels['aired'] = publishTime.strftime('%Y-%m-%d')
                    if len(program['labels']) > 0:
                        infoLabels['genre'] = program['labels'][0]

                infoLabels['title'] = program['title']
                infoLabels['plot'] = program['description']
                infoLabels['count'] = int(program['videoCount'])

                iconImage = self.api.getProgramSeriesImageUrl(program['slug'], 256)
                thumbnailImage = self.api.getProgramSeriesImageUrl(program['slug'], 512)
                fanartImage = self.api.getProgramSeriesImageUrl(program['slug'], 1280, 720)

                item = xbmcgui.ListItem(infoLabels['title'], iconImage=iconImage, thumbnailImage=thumbnailImage)
                item.setInfo('video', infoLabels)
                item.setProperty('Fanart_Image', fanartImage)

                if addToFavorites:
                    runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?addfavorite=%s)" % program['slug']
                    item.addContextMenuItems([(ADDON.getLocalizedString(30200), runScript)], True)
                else:
                    runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?delfavorite=%s)" % program['slug']
                    item.addContextMenuItems([(ADDON.getLocalizedString(30201), runScript)], True)

                url = PATH + '?listVideos=' + program['slug']
                xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder = True, totalItems = int(program['videoCount']))

            xbmcplugin.setContent(HANDLE, 'tvshows')
            xbmcplugin.endOfDirectory(HANDLE)

    def showProgramSeriesLabels(self):
        iconImage = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'tag.png')
        fanartImage = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

        labels = self.api.getProgramSeriesLabels()

        for label in labels:
            item = xbmcgui.ListItem(label.capitalize(), iconImage=iconImage)
            item.setProperty('Fanart_Image', fanartImage)
            
            url = PATH + '?programSeriesLabel=' + label
            xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder = True)

        xbmcplugin.endOfDirectory(HANDLE)


    def searchVideos(self):
        keyboard = xbmc.Keyboard('', ADDON.getLocalizedString(30003))
        keyboard.doModal()
        if keyboard.isConfirmed():
            keyword = keyboard.getText()
            self.listVideos(self.api.search(keyword))


    def listVideos(self, videos):
        tvShowTitles = dict()

        for video in videos:
            infoLabels = dict()

            if video['title'] is not None:
                infoLabels['title'] = video['title']
            else:
                infoLabels['title'] = ADDON.getLocalizedString(30006)

            if video.has_key('spotSubTitle') and video['spotSubTitle'] is not None:
                infoLabels['plot'] = video['spotSubTitle']
            elif video.has_key('description') and video['description'] is not None:
                infoLabels['plot'] = video['description']

            if video.has_key('duration') and video['duration'] is not None:
                infoLabels['duration'] = video['duration']
            if video.has_key('broadcastChannel') and video['broadcastChannel'] is not None:
                infoLabels['studio'] = video['broadcastChannel']
            if video.has_key('broadcastTime') and video['broadcastTime'] is not None:
                broadcastTime = self.parseDate(video['broadcastTime'])
                if broadcastTime:
                    infoLabels['plotoutline'] = ADDON.getLocalizedString(30015) % broadcastTime.strftime('%d. %b %Y kl. %H:%M')
                    infoLabels['date'] = broadcastTime.strftime('%d.%m.%Y')
                    infoLabels['aired'] = broadcastTime.strftime('%Y-%m-%d')
                    infoLabels['year'] = int(broadcastTime.strftime('%Y'))
                infoLabels['season'] = infoLabels['year']
            if video.has_key('programSerieSlug') and video['programSerieSlug'] is not None:
                if tvShowTitles.has_key(video['programSerieSlug']):
                    infoLabels['tvshowtitle'] = tvShowTitles[video['programSerieSlug']]
                else:
                    serie = self.api.getProgramSeriesInfo(video['programSerieSlug'])
                    if serie is not None:
                        tvShowTitles[video['programSerieSlug']] = serie['title']
                        infoLabels['tvshowtitle'] = serie['title']
                    else:
                        tvShowTitles[video['programSerieSlug']] = None
            if video.has_key('expireTime') and video['expireTime'] is not None:
                expireTime = self.parseDate(video['expireTime'])
                if expireTime:
                    infoLabels['plot'] += '[CR][CR]' + ADDON.getLocalizedString(30016) % expireTime.strftime('%d. %b %Y kl. %H:%M')

            iconImage = self.api.getVideoImageUrl(str(video['id']), 256)
            thumbnailImage = self.api.getVideoImageUrl(str(video['id']), 512)
            fanartImage = self.api.getVideoImageUrl(str(video['id']), 1280, 720)

            item = xbmcgui.ListItem(infoLabels['title'], iconImage=iconImage, thumbnailImage=thumbnailImage)
            item.setInfo('video', infoLabels)
            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', fanartImage)
            url = PATH + '?videoId=' + str(video['id'])
            xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder = False)

        xbmcplugin.setContent(HANDLE, 'episodes')
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(HANDLE)


    def playVideo(self, videoId):
        self._updateRecentlyWatched(videoId)
        video = self.api.getVideoById(videoId)

        u = urllib2.urlopen(video['videoManifestUrl'])
        rtmpUrl = u.read()
        u.close()

        if rtmpUrl[0:7] == '<script':
            d = xbmcgui.Dialog()
            d.ok(ADDON.getLocalizedString(30100), ADDON.getLocalizedString(30101), ADDON.getLocalizedString(30102))
        else:
            rtmpUrl = rtmpUrl.replace('rtmp://vod.dr.dk/', 'rtmp://vod.dr.dk/cms/')
            item = xbmcgui.ListItem(path = rtmpUrl)
            xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def parseDate(self, dateString):
        try:
            m = re.search('/Date\(([0-9]+).*?\)/', dateString)
            microseconds = long(m.group(1))
            return datetime.datetime.fromtimestamp(microseconds / 1000)
        except ValueError:
            return None


    def addFavorite(self, slug):
        if not self.favorites.count(slug):
            self.favorites.append(slug)
        self._save()

        xbmcgui.Dialog().ok(ADDON.getLocalizedString(30008), ADDON.getLocalizedString(30009))

    def delFavorite(self, slug):
        self.favorites.remove(slug)
        self._save()
        xbmcgui.Dialog().ok(ADDON.getLocalizedString(30008), ADDON.getLocalizedString(30010))

    def _updateRecentlyWatched(self, videoId):
        xbmc.log("Adding recently watched video ID: " + videoId)
        if self.recentlyWatched.count(videoId):
            self.recentlyWatched.remove(videoId)
        self.recentlyWatched.insert(0, videoId)
        self._save()


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id = 'plugin.video.drnu')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    CACHE_PATH = xbmc.translatePath(ADDON.getAddonInfo("Profile"))
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)

    FAVORITES_PATH = os.path.join(CACHE_PATH, 'favorites.pickle')
    RECENT_PATH = os.path.join(CACHE_PATH, 'recent.pickle')

    nuAddon = NuAddon()
    if PARAMS.has_key('show'):
        if PARAMS['show'][0] == 'allProgramSeries':
            nuAddon.showProgramSeries()
        elif PARAMS['show'][0] == 'programSeriesLabels':
            nuAddon.showProgramSeriesLabels()
        elif PARAMS['show'][0] == 'newest':
            nuAddon.showNewestVideos()
        elif PARAMS['show'][0] == 'spotlight':
            nuAddon.showSpotlightVideos()
        elif PARAMS['show'][0] == 'mostViewed':
            nuAddon.showMostViewedVideos()
        elif PARAMS['show'][0] == 'lastChance':
            nuAddon.showLastChanceVideos()
        elif PARAMS['show'][0] == 'search':
            nuAddon.searchVideos()
        elif PARAMS['show'][0] == 'favorites':
            nuAddon.showFavorites()
        elif PARAMS['show'][0] == 'recentlyWatched':
            nuAddon.showRecentlyWatched()

    elif PARAMS.has_key('programSeriesLabel'):
        nuAddon.showProgramSeries(label = PARAMS['programSeriesLabel'][0])

    elif PARAMS.has_key('listVideos'):
        nuAddon.showProgramSeriesVideos(PARAMS['listVideos'][0])

    elif PARAMS.has_key('videoId'):
        nuAddon.playVideo(PARAMS['videoId'][0])

    elif PARAMS.has_key('addfavorite'):
        nuAddon.addFavorite(PARAMS['addfavorite'][0])

    elif PARAMS.has_key('delfavorite'):
        nuAddon.delFavorite(PARAMS['delfavorite'][0])

    else:
        nuAddon.showMainMenu()

