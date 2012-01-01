#
#      Copyright (C) 2011 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import pickle
import os
import sys
import urlparse
import urllib2
import re
import datetime
import random

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import nuapi
import buggalo

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

        items = list()
        # All Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30000), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'all.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=allProgramSeries', item, True))
        # Program Series label
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30012), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'tag.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=programSeriesLabels', item, True))
        # Latest
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30001), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'new.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=newest', item, True))
        # Most viewed
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30011), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'eye.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=mostViewed', item, True))
        # Spotlight
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30002), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'star.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=spotlight', item, True))
        # Highlights
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30021), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'star.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=highlights', item, True))
        # Last chance
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30014), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'clock.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=lastChance', item, True))
        # Search videos
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30003), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'search.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=search', item, True))
        # Recently watched Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30007), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'eye-star.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=recentlyWatched', item, True))
        # Favorite Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30008), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'plusone.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=favorites', item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def showProgramSeriesVideos(self, slug):
        self.listVideos(self.api.getProgramSeriesVideos(slug))

    def showNewestVideos(self):
        self.listVideos(self.api.getNewestVideos())

    def showSpotlightVideos(self):
        self.listVideos(self.api.getSpotlightVideos())

    def showHighlightVideos(self):
        self.listVideos(self.api.getHighlightVideos())

    def showMostViewedVideos(self):
        self.listVideos(self.api.getMostViewedVideos())

    def showLastChanceVideos(self):
        self.listVideos(self.api.getLastChanceVideos())

    def showFavorites(self):
        self.showProgramSeries(self.favorites, False)

    def showRecentlyWatched(self):
        videos = list()

        for videoId in self.recentlyWatched:
            video = self.api.getVideoById(videoId)

            if video is not None:
                videos.append(video)
                
        if not videos:
            xbmcplugin.endOfDirectory(HANDLE, succeeded = False)
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013), ADDON.getLocalizedString(30020))
        else:
            self.listVideos(videos)

    def showProgramSeries(self, limitToSlugs = None, addToFavorites = True, label = None):
        programs = self.api.getProgramSeries(limitToSlugs, label)

        if not programs:
            xbmcplugin.endOfDirectory(HANDLE, succeeded = False)
            if not addToFavorites:
                xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013), ADDON.getLocalizedString(30018), ADDON.getLocalizedString(30019))
            else:
                xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013))
        else:
            items = list()
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

                if self.favorites.count(program['slug']) > 0:
                    runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?delfavorite=%s)" % program['slug']
                    item.addContextMenuItems([(ADDON.getLocalizedString(30201), runScript)], True)
                else:
                    runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?addfavorite=%s)" % program['slug']
                    item.addContextMenuItems([(ADDON.getLocalizedString(30200), runScript)], True)

                url = PATH + '?listVideos=' + program['slug']
                items.append((url, item, True))

            xbmcplugin.addDirectoryItems(HANDLE, items)
            xbmcplugin.setContent(HANDLE, 'tvshows')
            xbmcplugin.endOfDirectory(HANDLE)

    def showProgramSeriesLabels(self):
        iconImage = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'tag.png')
        fanartImage = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

        labels = self.api.getProgramSeriesLabels()
        items = list()
        for label in labels:
            item = xbmcgui.ListItem(label.capitalize(), iconImage=iconImage)
            item.setProperty('Fanart_Image', fanartImage)
            
            url = PATH + '?programSeriesLabel=' + label
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)


    def searchVideos(self):
        keyboard = xbmc.Keyboard('', ADDON.getLocalizedString(30003))
        keyboard.doModal()
        if keyboard.isConfirmed():
            keyword = keyboard.getText()
            self.listVideos(self.api.search(keyword))


    def listVideos(self, videos):
        items = list()

        for video in videos:
            infoLabels = self.createInfoLabels(video)

            iconImage = self.api.getVideoImageUrl(str(video['id']), 256)
            thumbnailImage = self.api.getVideoImageUrl(str(video['id']), 512)
            fanartImage = self.api.getVideoImageUrl(str(video['id']), 1280, 720)

            item = xbmcgui.ListItem(infoLabels['title'], iconImage=iconImage, thumbnailImage=thumbnailImage)
            item.setInfo('video', infoLabels)
            item.setProperty('Fanart_Image', fanartImage)
            url = PATH + '?videoId=' + str(video['id'])
            if video.has_key('chapters') and video['chapters'] and ADDON.getSetting('enable.chapters') == 'true':
                url += "&chapters=true"
                items.append((url, item, True))
            else:
                item.setProperty('IsPlayable', 'true')
                items.append((url, item))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.setContent(HANDLE, 'episodes')
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(HANDLE)

    def listVideoChapters(self, videoId):
        video = self.api.getVideoById(videoId)
        items = list()
        startTimes = list()

        for chapter in video['chapters']:
            startTimes.append(self.parseTime(chapter['startTime']))
        startTimes.append(self.parseTime(video['duration']))

        # 'Play from the start' item
        iconImage = self.api.getVideoImageUrl(str(video['id']), 256)
        thumbnailImage = self.api.getVideoImageUrl(str(video['id']), 512)
        fanartImage = self.api.getVideoImageUrl(str(video['id']), 1280, 720)
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30017), iconImage=iconImage, thumbnailImage=thumbnailImage)
        item.setProperty('IsPlayable', 'true')
        item.setProperty('Fanart_Image', fanartImage)
        url = PATH + '?videoId=' + str(video['id'])
        items.append((url, item))

        for idx, chapter in enumerate(video['chapters']):
            infoLabels = self.createInfoLabels(video)

            if chapter['title'] is not None:
                infoLabels['title'] = chapter['title']
            else:
                infoLabels['title'] = ADDON.getLocalizedString(30006)
            infoLabels['plot'] = video['description']

            startTime = startTimes[idx]
            if startTime:
                duration = startTimes[idx + 1] - startTime
                infoLabels['duration'] = str(duration.seconds)

            iconImage = self.api.getChapterImageUrl(str(chapter['id']), 256)
            thumbnailImage = self.api.getChapterImageUrl(str(chapter['id']), 512)
            fanartImage = self.api.getChapterImageUrl(str(chapter['id']), 1280, 720)

            item = xbmcgui.ListItem(chapter['title'], iconImage=iconImage, thumbnailImage=thumbnailImage)
            item.setInfo('video', infoLabels)
            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', fanartImage)
            url = PATH + '?videoId=' + str(video['id'])
            if startTime:
                url += "&startTime=" + self.formatStartTime(startTime)
            items.append((url, item))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.setContent(HANDLE, 'episodes')
        xbmcplugin.endOfDirectory(HANDLE)

    def playVideo(self, videoId, startTime = None):
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
            if startTime:
                rtmpUrl += ' start=' + startTime
            item = xbmcgui.ListItem(path = rtmpUrl)
            xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def parseDate(self, dateString):
        try:
            m = re.search('/Date\(([0-9]+).*?\)/', dateString)
            microseconds = long(m.group(1))
            return datetime.datetime.fromtimestamp(microseconds / 1000)
        except ValueError:
            return None

    def parseTime(self, timeString):
        try:
            m = re.search('([0-9]+):([0-9]+):([0-9]+)(.([0-9]+))?', timeString)
            hours = int(m.group(1))
            minutes = int(m.group(2))
            seconds = int(m.group(3))
            return datetime.datetime(2011, 12, 28, hours, minutes, seconds)
        except ValueError:
            return None

    def formatStartTime(self, time):
        startTime = time.hour * 3600
        startTime += time.minute * 60
        startTime += time.second
        return str(startTime * 1000)

    def createInfoLabels(self, video):
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
            serie = self.api.getProgramSeriesInfo(video['programSerieSlug'])
            if serie:
                infoLabels['tvshowtitle'] = serie['title']
        if video.has_key('expireTime') and video['expireTime'] is not None:
            expireTime = self.parseDate(video['expireTime'])
            if expireTime:
                infoLabels['plot'] += '[CR][CR]' + ADDON.getLocalizedString(30016) % expireTime.strftime('%d. %b %Y kl. %H:%M')
        if video.has_key('isHq') and video['isHq']:
            infoLabels['overlay'] = xbmcgui.ICON_OVERLAY_HD

        return infoLabels

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

    def displayError(self, message = 'n/a'):
        heading = ADDON.getLocalizedString(random.randint(99980, 99985))
        line1 = ADDON.getLocalizedString(30900)
        line2 = ADDON.getLocalizedString(30901)
        xbmcgui.Dialog().ok(heading, line1, line2, message)

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
    try:
        if PARAMS.has_key('show'):
            if PARAMS['show'][0] == 'allProgramSeries':
                nuAddon.showProgramSeries()
            elif PARAMS['show'][0] == 'programSeriesLabels':
                nuAddon.showProgramSeriesLabels()
            elif PARAMS['show'][0] == 'newest':
                nuAddon.showNewestVideos()
            elif PARAMS['show'][0] == 'spotlight':
                nuAddon.showSpotlightVideos()
            elif PARAMS['show'][0] == 'highlights':
                nuAddon.showHighlightVideos()
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

        elif PARAMS.has_key('videoId') and PARAMS.has_key('chapters'):
            nuAddon.listVideoChapters(PARAMS['videoId'][0])

        elif PARAMS.has_key('videoId') and PARAMS.has_key('startTime'):
            nuAddon.playVideo(PARAMS['videoId'][0], PARAMS['startTime'][0])

        elif PARAMS.has_key('videoId'):
            nuAddon.playVideo(PARAMS['videoId'][0])

        elif PARAMS.has_key('addfavorite'):
            nuAddon.addFavorite(PARAMS['addfavorite'][0])

        elif PARAMS.has_key('delfavorite'):
            nuAddon.delFavorite(PARAMS['delfavorite'][0])

        else:
            nuAddon.showMainMenu()

    except nuapi.DrNuException, ex:
        nuAddon.displayError(str(ex))

    except Exception:
        buggalo.onExceptionRaised()

