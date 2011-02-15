import re
import datetime
import os

import xbmc
import xbmcgui
import xbmcplugin

import danishaddons
import danishaddons.web
import danishaddons.info

class DRnuUI(object):
    def __init__(self, api):
        self.api = api

    def getMainMenu(self):
        iconImage = os.path.join(danishaddons.ADDON.getAddonInfo('path'), 'icon.png')
        # All Program Series
        item = xbmcgui.ListItem(danishaddons.msg(30000), iconImage=iconImage)
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, danishaddons.ADDON_PATH + '?all', item, isFolder=True)
        # Latest
        item = xbmcgui.ListItem(danishaddons.msg(30001), iconImage=iconImage)
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, danishaddons.ADDON_PATH + '?newest', item, isFolder=True)
        # Spotlight
        item = xbmcgui.ListItem(danishaddons.msg(30002), iconImage=iconImage)
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, danishaddons.ADDON_PATH + '?spot', item, isFolder=True)
        # Search
        item = xbmcgui.ListItem(danishaddons.msg(30003), iconImage=iconImage)
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, danishaddons.ADDON_PATH + '?search', item, isFolder=True)
        # Recently watched Program Series
        item = xbmcgui.ListItem(danishaddons.msg(30007), iconImage=iconImage)
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, danishaddons.ADDON_PATH + '?recentlywatched', item, isFolder=True)
        # Favorite Program Series
        item = xbmcgui.ListItem(danishaddons.msg(30008), iconImage=iconImage)
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, danishaddons.ADDON_PATH + '?favorites', item, isFolder=True)

        xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)

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
                infoLabels['plotoutline'] = danishaddons.msg(30004) % publishTime.strftime('%d. %b %Y kl. %H:%M')
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
                item.addContextMenuItems([(danishaddons.msg(30200), runScript)], True)
            else:
                runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?delfavorite=%s)" % program['slug']
                item.addContextMenuItems([(danishaddons.msg(30201), runScript)], True)

            url = danishaddons.ADDON_PATH + '?slug=' + program['slug']
            xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item, isFolder=True)

        xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)

    def searchVideos(self):
        keyboard = xbmc.Keyboard('', danishaddons.msg(30003))
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
                xbmcgui.Dialog().ok(danishaddons.msg(30003), danishaddons.msg(30005))
            else:
                self.listVideos(videos, False)


    def listVideos(self, videos, isSpot):
        for video in videos:
            infoLabels = dict()

            if video['title'] is not None:
                infoLabels['title'] = video['title']
            else:
                infoLabels['title'] = danishaddons.msg(30006)

            if isSpot:
                infoLabels['plot'] = video['spotSubTitle']
            else:
                infoLabels['plot'] = video['description']
                if video.has_key('duration'):
                    infoLabels['duration'] = video['duration']
                if video.has_key('broadcastChannel'):
                    infoLabels['studio'] = video['broadcastChannel']
                if video['broadcastTime'] is not None:
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
            url = danishaddons.ADDON_PATH + '?id=' + str(video['id'])
            xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item)

        xbmcplugin.addSortMethod(danishaddons.ADDON_HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)


    def playVideo(self, videoId):
        video = self.api.getVideoById(videoId)

        rtmpUrl = danishaddons.web.downloadUrl(video['videoManifestUrl'])
        if rtmpUrl[0:7] == '<script':
            d = xbmcgui.Dialog()
            d.ok(danishaddons.msg(30100), danishaddons.msg(30101), danishaddons.msg(30102))
        else:
            rtmpUrl = rtmpUrl.replace('rtmp://vod.dr.dk/', 'rtmp://vod.dr.dk/cms/')
            item = xbmcgui.ListItem(path = rtmpUrl)
            xbmcplugin.setResolvedUrl(danishaddons.ADDON_HANDLE, True, item)

    def parseDate(self, dateString):
        m = re.search('/Date\(([0-9]+).*?\)/', dateString)
        microseconds = long(m.group(1))
        return datetime.datetime.fromtimestamp(microseconds / 1000)

