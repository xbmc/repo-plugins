#
#      Copyright (C) 2013 Tommy Winther
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
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import pickle
import os
import sys
import urlparse
import re
import datetime

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import xbmcvfs

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

        self.recentlyWatched = self.recentlyWatched[0:25]  # Limit to ten items
        pickle.dump(self.recentlyWatched, open(RECENT_PATH, 'wb'))

    def showMainMenu(self):
        fanartImage = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

        items = list()
        # A-Z Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30000),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'all.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=azProgramSeries', item, True))
        # Program Series label
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30012),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'tag.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=programSeriesLabels', item, True))
        # Premiere
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30025),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'new.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=premiere', item, True))
        # Latest
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30001),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'new.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=newest', item, True))
        # Most viewed
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30011),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'eye.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=mostViewed', item, True))
        # Spotlight
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30002),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'star.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=spotlight', item, True))
        # Highlights
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30021),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'star.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=highlights', item, True))
        # Last chance
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30014),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'clock.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=lastChance', item, True))
        # Search videos
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30003),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'search.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=search', item, True))
        # Recently watched Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30007),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons',
                                                       'eye-star.png'))
        item.setProperty('Fanart_Image', fanartImage)
        items.append((PATH + '?show=recentlyWatched', item, True))
        # Favorite Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30008),
                                iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'plusone.png'))
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

    def showPremiereVideos(self):
        self.listVideos(self.api.getPremiereVideos())

    def showFavorites(self):
        self.showProgramSeries(self.favorites, False)

    def showRecentlyWatched(self):
        videos = list()

        for videoId in self.recentlyWatched:
            video = self.api.getVideoById(videoId)

            if video is not None:
                videos.append(video)

        if not videos:
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013),
                                ADDON.getLocalizedString(30020))
        else:
            self.listVideos(videos)

    def showProgramSeries(self, limitToSlugs=None, addToFavorites=True, label=None, letter=None):
        programs = self.api.getProgramSeries(limitToSlugs, label)

        if not programs:
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
            if not addToFavorites:
                xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013),
                                    ADDON.getLocalizedString(30018), ADDON.getLocalizedString(30019))
            else:
                xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013))
        else:
            items = list()
            for program in programs:
                if letter is not None and program['title'][0].upper() != letter.decode('utf-8', 'ignore'):
                    continue
                infoLabels = {}

                if program['newestVideoPublishTime'] is not None:
                    publishTime = self.parseDate(program['newestVideoPublishTime'])
                    if publishTime:
                        infoLabels['plotoutline'] = ADDON.getLocalizedString(30004) % publishTime.strftime(
                            '%d. %b %Y kl. %H:%M')
                        infoLabels['date'] = publishTime.strftime('%d.%m.%Y')
                        infoLabels['year'] = int(publishTime.strftime('%Y'))
                        infoLabels['aired'] = publishTime.strftime('%Y-%m-%d')
                    if len(program['labels']) > 0:
                        infoLabels['genre'] = program['labels'][0]

                infoLabels['title'] = program['title']
                infoLabels['plot'] = program['description']
                infoLabels['count'] = int(program['videoCount'])

                menuItems = list()

                if self.favorites.count(program['slug']) > 0:
                    runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?delfavorite=%s)" % program['slug']
                    menuItems.append((ADDON.getLocalizedString(30201), runScript))
                else:
                    runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?addfavorite=%s)" % program['slug']
                    menuItems.append((ADDON.getLocalizedString(30200), runScript))

                customThumbFile = self.getCustomThumbPath(program['slug'])
                if os.path.exists(customThumbFile):
                    menuItems.append((ADDON.getLocalizedString(30024),
                                      "XBMC.RunPlugin(plugin://plugin.video.drnu/?delthumb=%s)" % program['slug']))
                    iconImage = customThumbFile
                else:
                    menuItems.append((ADDON.getLocalizedString(30023),
                                      "XBMC.RunPlugin(plugin://plugin.video.drnu/?setthumb=%s)" % program['slug']))
                    iconImage = self.api.getProgramSeriesImageUrl(program['slug'], 256)
                fanartImage = self.api.getProgramSeriesImageUrl(program['slug'], 1280, 720)
                item = xbmcgui.ListItem(infoLabels['title'], iconImage=iconImage)
                item.setInfo('video', infoLabels)
                item.setProperty('Fanart_Image', fanartImage)

                item.addContextMenuItems(menuItems, False)

                url = PATH + '?listVideos=' + program['slug']
                items.append((url, item, True))

            xbmcplugin.addDirectoryItems(HANDLE, items)
            xbmcplugin.setContent(HANDLE, 'tvshows')
            xbmcplugin.endOfDirectory(HANDLE)

    def showProgramSeriesAZ(self):
        programs = self.api.getProgramSeries()

        if not programs:
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013),
                                ADDON.getLocalizedString(30018), ADDON.getLocalizedString(30019))
        else:
            items = list()

            # All Program Series
            iconImage = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'all.png')
            fanartImage = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

            item = xbmcgui.ListItem(ADDON.getLocalizedString(30022), iconImage=iconImage)
            item.setProperty('Fanart_Image', fanartImage)
            items.append((PATH + '?show=allProgramSeries', item, True))

            letter = programs[0]['title'][0].upper()
            count = 0
            for idx, program in enumerate(programs):
                count += 1
                if letter != program['title'][0].upper() or idx == len(programs):
                    letter = program['title'][0].upper()
                    infoLabels = {'title': letter, 'count': count}

                    item = xbmcgui.ListItem(letter, iconImage=iconImage)
                    item.setInfo('video', infoLabels)
                    item.setProperty('Fanart_Image', fanartImage)

                    url = PATH + '?programSeriesLetter=' + letter
                    items.append((url, item, True))
                    count = 0

            xbmcplugin.addDirectoryItems(HANDLE, items)
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
            fanartImage = self.api.getVideoImageUrl(str(video['id']), 1280, 720)
            item = xbmcgui.ListItem(infoLabels['title'], iconImage=iconImage)
            item.setInfo('video', infoLabels)
            item.setProperty('Fanart_Image', fanartImage)
            url = PATH + '?videoId=' + str(video['id'])
            if 'chapters' in video and video['chapters'] and ADDON.getSetting('enable.chapters') == 'true':
                url += "&chapters=true"
                items.append((url, item, True))
            else:
                item.setProperty('IsPlayable', 'true')
                items.append((url, item))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.setContent(HANDLE, 'episodes')
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(HANDLE)

    def listVideoChapters(self, videoId):
        video = self.api.getVideoById(videoId)
        if not video:
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
            return

        items = list()
        startTimes = list()

        for chapter in video['chapters']:
            startTimes.append(self.parseTime(chapter['startTime']))
        startTimes.append(self.parseTime(video['duration']))

        # 'Play from the start' item
        iconImage = self.api.getVideoImageUrl(str(video['id']), 256)
        fanartImage = self.api.getVideoImageUrl(str(video['id']), 1280, 720)
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30017), iconImage=iconImage)
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
                infoLabels['duration'] = str(duration.seconds * 60)

            iconImage = self.api.getChapterImageUrl(str(chapter['id']), 256)
            fanartImage = self.api.getChapterImageUrl(str(chapter['id']), 1280, 720)
            item = xbmcgui.ListItem(chapter['title'], iconImage=iconImage)
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

    def playVideo(self, videoId, startTime=None):
        self._updateRecentlyWatched(videoId)
        video = self.api.getVideoById(videoId)
        if not video:
            raise nuapi.DrNuException('Video with ID %s not found!' % videoId)

        if ADDON.getSetting('show.stream.selector') == 'true':
            json = self.api._call_api(video['videoResourceUrl'])
            options = []
            links = sorted(json['links'], key=lambda link: link['bitrateKbps'], reverse=True)
            for link in links:
                options.append('%s (%s kbps)' % (link['linkType'], link['bitrateKbps']))

            d = xbmcgui.Dialog()
            idx = d.select(video['title'], options)
            if idx == -1:
                xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
                return
            rtmpUrl = links[idx]['uri']

        else:
            rtmpUrl = self.api._http_request(video['videoManifestUrl'])

        if rtmpUrl[0:7] == '<script':
            d = xbmcgui.Dialog()
            d.ok(ADDON.getLocalizedString(30100), ADDON.getLocalizedString(30101), ADDON.getLocalizedString(30102))
        else:
            m = re.search('(rtmp://vod.dr.dk/cms)/([^\?]+)(\?.*)', rtmpUrl)
            rtmpUrl = m.group(1) + m.group(3)
            rtmpUrl += ' playpath=' + m.group(2) + m.group(3)
            rtmpUrl += ' app=cms' + m.group(3)

            if startTime:
                rtmpUrl += ' start=' + startTime
            thumbnailImage = self.api.getVideoImageUrl(str(video['id']), 256)
            item = xbmcgui.ListItem(path=rtmpUrl, thumbnailImage=thumbnailImage)
            xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def parseDate(self, dateString):
        if 'Date(' in dateString:
            try:
                m = re.search('/Date\(([0-9]+).*?\)/', dateString)
                microseconds = long(m.group(1))
                return datetime.datetime.fromtimestamp(microseconds / 1000)
            except ValueError:
                return None
        elif dateString is not None:
            try:
                m = re.search('(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)', dateString)
                year = int(m.group(1))
                month = int(m.group(2))
                day = int(m.group(3))
                hours = int(m.group(4))
                minutes = int(m.group(5))
                seconds = int(m.group(6))
                return datetime.datetime(year, month, day, hours, minutes, seconds)
            except ValueError:
                return None
        else:
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

    def parseDuration(self, duration):
        try:
            minutes = int(duration[0:2]) * 60
            minutes += int(duration[3:5])
            minutes += int(duration[6:8]) / 60
            return str(minutes)
        except:
            return 0

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

        if 'spotSubTitle' in video and video['spotSubTitle'] is not None:
            infoLabels['plot'] = video['spotSubTitle']
        elif 'description' in video and video['description'] is not None:
            infoLabels['plot'] = video['description']

        if 'duration' in video and video['duration'] is not None:
            infoLabels['duration'] = self.parseDuration(video['duration'])
        if 'broadcastChannel' in video and video['broadcastChannel'] is not None:
            infoLabels['studio'] = video['broadcastChannel']
        if 'broadcastTime' in video and video['broadcastTime'] is not None:
            broadcastTime = self.parseDate(video['broadcastTime'])
            if broadcastTime:
                infoLabels['plotoutline'] = ADDON.getLocalizedString(30015) % broadcastTime.strftime(
                    '%d. %b %Y kl. %H:%M')
                infoLabels['date'] = broadcastTime.strftime('%d.%m.%Y')
                infoLabels['aired'] = broadcastTime.strftime('%Y-%m-%d')
                infoLabels['year'] = int(broadcastTime.strftime('%Y'))
        if 'expireTime' in video and video['expireTime'] is not None:
            expireTime = self.parseDate(video['expireTime'])
            if expireTime:
                infoLabels['plot'] += '[CR][CR]' + ADDON.getLocalizedString(30016) % expireTime.strftime(
                    '%d. %b %Y kl. %H:%M')
        if 'isHq' in video and video['isHq']:
            infoLabels['overlay'] = xbmcgui.ICON_OVERLAY_HD

        return infoLabels

    def addFavorite(self, slug):
        if not self.favorites.count(slug):
            self.favorites.append(slug)
        self._save()

        xbmcgui.Dialog().ok(ADDON.getLocalizedString(30008), ADDON.getLocalizedString(30009))

    def delFavorite(self, slug):
        if self.favorites.count(slug):
            self.favorites.remove(slug)
        self._save()
        xbmcgui.Dialog().ok(ADDON.getLocalizedString(30008), ADDON.getLocalizedString(30010))

    def setCustomThumb(self, slug):
        imageFile = xbmcgui.Dialog().browse(2, 'custom thumb', 'myprograms', '.jpg|.png', True)
        if imageFile is not None and xbmcvfs.exists(imageFile):
            thumbFile = self.getCustomThumbPath(slug)
            xbmcvfs.copy(imageFile, thumbFile)

    def delCustomThumb(self, slug):
        thumbFile = self.getCustomThumbPath(slug)
        if os.path.exists(thumbFile):
            os.unlink(thumbFile)

    def getCustomThumbPath(self, slug):
        return os.path.join(CACHE_PATH, '%s-thumb.jpg' % slug)

    def _updateRecentlyWatched(self, videoId):
        xbmc.log("Adding recently watched video ID: " + videoId)
        if self.recentlyWatched.count(videoId):
            self.recentlyWatched.remove(videoId)
        self.recentlyWatched.insert(0, videoId)
        self._save()

    def displayError(self, message='n/a'):
        heading = buggalo.getRandomHeading()
        line1 = ADDON.getLocalizedString(30900)
        line2 = ADDON.getLocalizedString(30901)
        xbmcgui.Dialog().ok(heading, line1, line2, message)

    def displayIOError(self, message='n/a'):
        heading = buggalo.getRandomHeading()
        line1 = ADDON.getLocalizedString(30902)
        line2 = ADDON.getLocalizedString(30903)
        xbmcgui.Dialog().ok(heading, line1, line2, message)


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    CACHE_PATH = xbmc.translatePath(ADDON.getAddonInfo("Profile"))
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)

    FAVORITES_PATH = os.path.join(CACHE_PATH, 'favorites.pickle')
    RECENT_PATH = os.path.join(CACHE_PATH, 'recent.pickle')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    buggalo.addExtraData('cache_path', CACHE_PATH)
    nuAddon = NuAddon()
    try:
        if 'show' in PARAMS:
            if PARAMS['show'][0] == 'allProgramSeries':
                nuAddon.showProgramSeries()
            elif PARAMS['show'][0] == 'azProgramSeries':
                nuAddon.showProgramSeriesAZ()
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
            elif PARAMS['show'][0] == 'premiere':
                nuAddon.showPremiereVideos()
            elif PARAMS['show'][0] == 'lastChance':
                nuAddon.showLastChanceVideos()
            elif PARAMS['show'][0] == 'search':
                nuAddon.searchVideos()
            elif PARAMS['show'][0] == 'favorites':
                nuAddon.showFavorites()
            elif PARAMS['show'][0] == 'recentlyWatched':
                nuAddon.showRecentlyWatched()

        elif 'programSeriesLabel' in PARAMS:
            nuAddon.showProgramSeries(label=PARAMS['programSeriesLabel'][0])

        elif 'programSeriesLetter' in PARAMS:
            nuAddon.showProgramSeries(letter=PARAMS['programSeriesLetter'][0])

        elif 'listVideos' in PARAMS:
            nuAddon.showProgramSeriesVideos(PARAMS['listVideos'][0])

        elif 'videoId' in PARAMS and 'chapters' in PARAMS:
            nuAddon.listVideoChapters(PARAMS['videoId'][0])

        elif 'videoId' in PARAMS and 'startTime' in PARAMS:
            nuAddon.playVideo(PARAMS['videoId'][0], PARAMS['startTime'][0])

        elif 'videoId' in PARAMS:
            nuAddon.playVideo(PARAMS['videoId'][0])

        elif 'addfavorite' in PARAMS:
            nuAddon.addFavorite(PARAMS['addfavorite'][0])

        elif 'delfavorite' in PARAMS:
            nuAddon.delFavorite(PARAMS['delfavorite'][0])

        elif 'setthumb' in PARAMS:
            nuAddon.setCustomThumb(PARAMS['setthumb'][0])

        elif 'delthumb' in PARAMS:
            nuAddon.delCustomThumb(PARAMS['delthumb'][0])

        else:
            nuAddon.showMainMenu()

    except nuapi.DrNuException, ex:
        nuAddon.displayError(str(ex))

    except IOError, ex:
        nuAddon.displayIOError(str(ex))

    except Exception:
        buggalo.onExceptionRaised()
