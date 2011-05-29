import re
import datetime
import os
import urllib2

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

class DRnuUI(object):
    ADDON = xbmcaddon.Addon(id = 'plugin.video.drnu')
    def __init__(self, api, addonHandle, addonPath):
        self.api = api
        self.addonHandle = addonHandle
        self.addonPath = addonPath

    def getMainMenu(self):
        iconImage = os.path.join(self.ADDON.getAddonInfo('path'), 'icon.png')
        fanartImage = os.path.join(self.ADDON.getAddonInfo('path'), 'fanart.jpg')
        # All Program Series
        item = xbmcgui.ListItem(self.ADDON.getLocalizedString(30000), iconImage=iconImage)
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(self.addonHandle, self.addonPath + '?all', item, isFolder=True)
        # Latest
        item = xbmcgui.ListItem(self.ADDON.getLocalizedString(30001), iconImage=iconImage)
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(self.addonHandle, self.addonPath + '?newest', item, isFolder=True)
        # Spotlight
        item = xbmcgui.ListItem(self.ADDON.getLocalizedString(30002), iconImage=iconImage)
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(self.addonHandle, self.addonPath + '?spot', item, isFolder=True)
        # Search
        item = xbmcgui.ListItem(self.ADDON.getLocalizedString(30003), iconImage=iconImage)
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(self.addonHandle, self.addonPath + '?search', item, isFolder=True)
        # Recently watched Program Series
        item = xbmcgui.ListItem(self.ADDON.getLocalizedString(30007), iconImage=iconImage)
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(self.addonHandle, self.addonPath + '?recentlywatched', item, isFolder=True)
        # Favorite Program Series
        item = xbmcgui.ListItem(self.ADDON.getLocalizedString(30008), iconImage=iconImage)
        item.setProperty('Fanart_Image', fanartImage)
        xbmcplugin.addDirectoryItem(self.addonHandle, self.addonPath + '?favorites', item, isFolder=True)

        xbmcplugin.endOfDirectory(self.addonHandle)

    def getProgramSeries(self, limitToSlugs = None, addToFavorites = True):
        programSeries = self.api.getProgramSeries()
        programs = list()

        if limitToSlugs is not None:
            for slug in limitToSlugs:
                for program in programSeries:
                    if slug == program['slug']:
                        programs.append(program)
        else:
            programs = programSeries


        for program in programs:
            infoLabels = {}

            if program['newestVideoPublishTime'] is not None:
                publishTime = self.parseDate(program['newestVideoPublishTime'])
                infoLabels['plotoutline'] = self.ADDON.getLocalizedString(30004) % publishTime.strftime('%d. %b %Y kl. %H:%M')
                infoLabels['date'] = publishTime.strftime('%d.%m.%Y')
                infoLabels['year'] = int(publishTime.strftime('%Y'))

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
                item.addContextMenuItems([(self.ADDON.getLocalizedString(30200), runScript)], True)
            else:
                runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?delfavorite=%s)" % program['slug']
                item.addContextMenuItems([(self.ADDON.getLocalizedString(30201), runScript)], True)

            url = self.addonPath + '?slug=' + program['slug']
            xbmcplugin.addDirectoryItem(self.addonHandle, url, item, isFolder=True)

        xbmcplugin.endOfDirectory(self.addonHandle)

    def searchVideos(self):
        keyboard = xbmc.Keyboard('', self.ADDON.getLocalizedString(30003))
        keyboard.doModal()
        if keyboard.isConfirmed():
            keyword = keyboard.getText()

            videos = self.api.getAllVideos()
            for idx in range(len(videos)-1, -1, -1):
                video = videos[idx]
                # simplistic search for title
                if video['title'].lower().find(keyword.lower()) == -1:
                    del videos[idx]

            if not len(videos):
                xbmcgui.Dialog().ok(self.ADDON.getLocalizedString(30003), self.ADDON.getLocalizedString(30005))
            else:
                self.listVideos(videos, False)


    def listVideos(self, videos, isSpot):
        for video in videos:
            infoLabels = dict()

            if video['title'] is not None:
                infoLabels['title'] = video['title']
            else:
                infoLabels['title'] = self.ADDON.getLocalizedString(30006)

            if isSpot:
                infoLabels['plot'] = video['spotSubTitle']
            else:
                infoLabels['plot'] = video['description']
                if video.has_key('duration') and video['duration'] is not None:
                    infoLabels['duration'] = video['duration']
                if video.has_key('broadcastChannel') and video['broadcastChannel'] is not None:
                    infoLabels['studio'] = video['broadcastChannel']
                if video.has_key('broadcastTime') and video['broadcastTime'] is not None:
                    broadcastTime = self.parseDate(video['broadcastTime'])
                    infoLabels['plotoutline'] = 'Sendt: %s' % broadcastTime.strftime('%d. %b %Y kl. %H:%M')
                    infoLabels['date'] = broadcastTime.strftime('%d.%m.%Y')
                    infoLabels['aired'] = broadcastTime.strftime('%Y-%m-%d')
                    infoLabels['year'] = int(broadcastTime.strftime('%Y'))

            iconImage = self.api.getVideoImageUrl(str(video['id']), 256)
            thumbnailImage = self.api.getVideoImageUrl(str(video['id']), 512)
            fanartImage = self.api.getVideoImageUrl(str(video['id']), 1280, 720)

            item = xbmcgui.ListItem(infoLabels['title'], iconImage=iconImage, thumbnailImage=thumbnailImage)
            item.setInfo('video', infoLabels)
            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', fanartImage)
            url = self.addonPath + '?id=' + str(video['id'])
            xbmcplugin.addDirectoryItem(self.addonHandle, url, item)

        xbmcplugin.addSortMethod(self.addonHandle, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(self.addonHandle)


    def playVideo(self, videoId):
        video = self.api.getVideoById(videoId)

        u = urllib2.urlopen(video['videoManifestUrl'])
        rtmpUrl = u.read()
        u.close()
        
        if rtmpUrl[0:7] == '<script':
            d = xbmcgui.Dialog()
            d.ok(self.ADDON.getLocalizedString(30100), self.ADDON.getLocalizedString(30101), self.ADDON.getLocalizedString(30102))
        else:
            rtmpUrl = rtmpUrl.replace('rtmp://vod.dr.dk/', 'rtmp://vod.dr.dk/cms/')
            item = xbmcgui.ListItem(path = rtmpUrl)
            xbmcplugin.setResolvedUrl(self.addonHandle, True, item)

    def parseDate(self, dateString):
        m = re.search('/Date\(([0-9]+).*?\)/', dateString)
        microseconds = long(m.group(1))
        return datetime.datetime.fromtimestamp(microseconds / 1000)

