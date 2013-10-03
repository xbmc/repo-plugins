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

import tvapi
import buggalo

LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '\xC3\x86', '\xC3\x98', '\xC3\x85']


class DrDkTvAddon(object):
    def __init__(self):
        self.api = tvapi.TvApi()
        self.favorites = list()
        self.recentlyWatched = list()

    def _save(self):
        # save favorites
        self.favorites.sort()
        pickle.dump(self.favorites, open(FAVORITES_PATH, 'wb'))

        self.recentlyWatched = self.recentlyWatched[0:25]  # Limit to 25 items
        pickle.dump(self.recentlyWatched, open(RECENT_PATH, 'wb'))

    def _load(self):
        # load favorites
        if os.path.exists(FAVORITES_PATH):
            try:
                self.favorites = pickle.load(open(FAVORITES_PATH, 'rb'))
            except Exception:
                pass

        # load recently watched
        if os.path.exists(RECENT_PATH):
            try:
                self.recentlyWatched = pickle.load(open(RECENT_PATH, 'rb'))
            except Exception:
                pass

    def showMainMenu(self):
        items = list()
        # A-Z Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30000), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'all.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        items.append((PATH + '?show=listAZ', item, True))

        # Premiere
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30025), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'new.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        items.append((PATH + '?listVideos=%s' % tvapi.SLUG_PREMIERES, item, True))

        # Most viewed
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30011), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'eye.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        items.append((PATH + '?show=mostViewed', item, True))

        # Spotlight
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30002), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'star.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        items.append((PATH + '?listVideos=%s' % tvapi.SLUG_SPOTS, item, True))

        # Highlights
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30021), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'star.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        items.append((PATH + '?listVideos=%s' % tvapi.SLUG_HIGHLIGHTS, item, True))

        # Search videos
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30003), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'search.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        items.append((PATH + '?show=search', item, True))

        # Recently watched Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30007), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'eye-star.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        items.append((PATH + '?show=recentlyWatched', item, True))

        # Favorite Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30008), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'plusone.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        items.append((PATH + '?show=favorites', item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def showProgramSeriesVideos(self, slug):
        self.listVideos(self.api.programCardRelations(slug))

    def showMostViewedVideos(self):
        self.listVideos(self.api.getMostViewedProgramCards())

    def showFavorites(self):
        self._load()
        if not self.favorites:
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013))
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        else:
            self.listBundles(self.api.bundle(slugs=self.favorites), addToFavorites=False)

    def showRecentlyWatched(self):
        self._load()
        videos = list()
        for programCardUrn in self.recentlyWatched:
            video = self.api.programCard(programCardUrn)
            if video is None or not 'Data' in video or len(video['Data']) == 0:
                self.recentlyWatched.remove(programCardUrn)
            else:
                videos.append(video['Data'][0])

        self._save()
        if not videos:
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013), ADDON.getLocalizedString(30020))
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        else:
            self.listVideos(videos)

    def showProgramSeries(self, letter=None):
        self.listBundles(self.api.bundlesWithPublicAsset(letter))

    def showAZ(self):
        items = list()

        # All Program Series
        iconImage = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'all.png')

        for letter in LETTERS:
            item = xbmcgui.ListItem(letter, iconImage=iconImage)
            item.setProperty('Fanart_Image', FANART_IMAGE)

            url = PATH + '?listProgramSeriesByLetter=' + letter
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def searchVideos(self):
        keyboard = xbmc.Keyboard('', ADDON.getLocalizedString(30003))
        keyboard.doModal()
        if keyboard.isConfirmed():
            keyword = keyboard.getText()
            self.listVideos(self.api.searchProgramCard(keyword))

    def listBundles(self, bundles, addToFavorites=True):
        if not bundles:
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
            if not addToFavorites:
                xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013),
                                    ADDON.getLocalizedString(30018), ADDON.getLocalizedString(30019))
            else:
                xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013))
        else:
            items = list()
            for bundle in bundles['Data']:
                if 'ProgramCard' in bundle and bundle['ProgramCard']['PrimaryAssetKind'] != 'VideoResource':
                    continue

                infoLabels = {}
                if bundle['CreatedTime'] is not None:
                    publishTime = self.parseDate(bundle['CreatedTime'])
                    if publishTime:
                        infoLabels['plotoutline'] = ADDON.getLocalizedString(30004) % publishTime.strftime('%d. %b %Y kl. %H:%M')
                        infoLabels['date'] = publishTime.strftime('%d.%m.%Y')
                        infoLabels['year'] = int(publishTime.strftime('%Y'))
                        infoLabels['aired'] = publishTime.strftime('%Y-%m-%d')
                infoLabels['title'] = bundle['Title']

                menuItems = list()
                if self.favorites.count(bundle['Slug']) > 0:
                    runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?delfavorite=%s)" % bundle['Slug']
                    menuItems.append((ADDON.getLocalizedString(30201), runScript))
                else:
                    runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?addfavorite=%s)" % bundle['Slug']
                    menuItems.append((ADDON.getLocalizedString(30200), runScript))

                if 'ProgramCard' in bundle:
                    programCard = bundle['ProgramCard']
                else:
                    programCard = bundle

                imageAsset = self.api.getAsset('Image', programCard)
                if imageAsset:
                    iconImage = imageAsset['Uri']
                else:
                    iconImage = ''
                item = xbmcgui.ListItem(infoLabels['title'], iconImage=iconImage)
                item.setInfo('video', infoLabels)
                item.setProperty('Fanart_Image', iconImage)
                item.addContextMenuItems(menuItems, False)

                url = PATH + '?listVideos=' + bundle['Slug']
                items.append((url, item, True))

            xbmcplugin.addDirectoryItems(HANDLE, items)
            xbmcplugin.endOfDirectory(HANDLE)

    def listVideos(self, programCards):
        items = list()
        if 'Data' in programCards:
            programCards = programCards['Data']

        for programCard in programCards:
            if 'ProgramCard' in programCard:
                programCard = programCard['ProgramCard']
            if not 'PrimaryAssetUri' in programCard:
                continue

            infoLabels = self.createInfoLabels(programCard)

            imageAsset = self.api.getAsset('Image', programCard)
            if imageAsset:
                iconImage = imageAsset['Uri']
            else:
                iconImage = ''
            item = xbmcgui.ListItem(infoLabels['title'], iconImage=iconImage)
            item.setInfo('video', infoLabels)
            item.setProperty('Fanart_Image', iconImage)
            url = PATH + '?videoasset=' + programCard['PrimaryAssetUri'] + '&urn=' + programCard['Urn']
            item.setProperty('IsPlayable', 'true')
            items.append((url, item))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(HANDLE)

    def playVideo(self, assetUri, programCardUrn):
        self.updateRecentlyWatched(programCardUrn)
        asset = self.api._http_request(assetUri)
        if not asset:
            raise tvapi.TvNuException('Video with ID %s not found!' % assetUri)

        if ADDON.getSetting('show.stream.selector') == 'true':
            options = []
            for link in asset['Links']:
                options.append('%s (%s kbps)' % (link['Target'], link['Bitrate'] if 'Bitrate' in link else '?'))
            options.append('vodfiles.dr.dk')

            d = xbmcgui.Dialog()
            idx = d.select('Stream', options)
            if idx == -1:
                xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
                return
            elif idx == len(options) - 1:
                videoUrl = self.api.getLink(asset, 'Android')
                videoUrl = videoUrl.replace('rtsp://om.gss.dr.dk/mediacache/_definst_/mp4:content/', 'http://vodfiles.dr.dk/')
            else:
                videoUrl = asset['Links'][idx]['Uri']

        else:
            if ADDON.getSetting('prefer.stream.target') == 'vodfiles.dr.dk':
                videoUrl = self.api.getLink(asset, 'Android')
                videoUrl = videoUrl.replace('rtsp://om.gss.dr.dk/mediacache/_definst_/mp4:content/', 'http://vodfiles.dr.dk/')
            elif ADDON.getSetting('prefer.stream.target') == 'Android':
                videoUrl = self.api.getLink(asset, 'Android')
            elif ADDON.getSetting('prefer.stream.target') == 'Streaming':
                videoUrl = self.api.getLink(asset, 'Streaming')
            else:
                videoUrl = self.api.getLink(asset, 'Ios')

        if videoUrl is None:
            videoUrl = self.api.getLink(asset)
            if videoUrl is None:
                raise Exception('No stream found')

        if videoUrl[0:7] == 'rtmp://':
            m = re.search('(rtmp://vod.dr.dk/cms)/([^\?]+)(\?.*)', videoUrl)
            if m:
                videoUrl = m.group(1) + m.group(3)
                videoUrl += ' playpath=' + m.group(2) + m.group(3)
                videoUrl += ' app=cms' + m.group(3)

        try:
            print videoUrl
        except:
            pass

        item = xbmcgui.ListItem(path=videoUrl)
        xbmcplugin.setResolvedUrl(HANDLE, videoUrl is not None, item)

        if ADDON.getSetting('enable.subtitles') == 'true' and 'SubtitlesList' in asset and asset['SubtitlesList']:
            path = None
            if len(asset['SubtitlesList']) > 0:
                path = asset['SubtitlesList'][0]['Uri']

            if path:
                player = xbmc.Player()
                for retry in range(0, 20):
                    if player.isPlaying():
                        break
                    xbmc.sleep(250)
                xbmc.Player().setSubtitles(path)

    def parseDate(self, dateString):
        if dateString is not None:
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

    def createInfoLabels(self, programCard):
        infoLabels = dict()

        if programCard['Title'] is not None:
            infoLabels['title'] = programCard['Title']
        else:
            infoLabels['title'] = ADDON.getLocalizedString(30006)

        if 'Description' in programCard and programCard['Description'] is not None:
            infoLabels['plot'] = programCard['Description']
        if 'PrimaryBroadcastStartTime' in programCard and programCard['PrimaryBroadcastStartTime'] is not None and programCard['PrimaryBroadcastStartTime'][0:4] != '0001':
            broadcastTime = self.parseDate(programCard['PrimaryBroadcastStartTime'])
            if broadcastTime:
                infoLabels['plotoutline'] = ADDON.getLocalizedString(30015) % broadcastTime.strftime('%d. %b %Y kl. %H:%M')
                infoLabels['date'] = broadcastTime.strftime('%d.%m.%Y')
                infoLabels['aired'] = broadcastTime.strftime('%Y-%m-%d')
                infoLabels['year'] = int(broadcastTime.strftime('%Y'))
        if 'EndPublish' in programCard and programCard['EndPublish'] is not None and programCard['EndPublish'][0:4] != '9999':
            expireTime = self.parseDate(programCard['EndPublish'])
            if expireTime:
                infoLabels['plot'] += '[CR][CR]' + ADDON.getLocalizedString(30016) % expireTime.strftime('%d. %b %Y kl. %H:%M')

        return infoLabels

    def addFavorite(self, slug):
        self._load()
        if not self.favorites.count(slug):
            self.favorites.append(slug)
        self._save()

        xbmcgui.Dialog().ok(ADDON.getLocalizedString(30008), ADDON.getLocalizedString(30009))

    def delFavorite(self, slug):
        self._load()
        if self.favorites.count(slug):
            self.favorites.remove(slug)
        self._save()
        xbmcgui.Dialog().ok(ADDON.getLocalizedString(30008), ADDON.getLocalizedString(30010))

    def updateRecentlyWatched(self, assetUri):
        self._load()
        if self.recentlyWatched.count(assetUri):
            self.recentlyWatched.remove(assetUri)
        self.recentlyWatched.insert(0, assetUri)
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
    FANART_IMAGE = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    buggalo.addExtraData('cache_path', CACHE_PATH)
    drDkTvAddon = DrDkTvAddon()
    try:
        if 'show' in PARAMS:
            if PARAMS['show'][0] == 'allProgramSeries':
                drDkTvAddon.showProgramSeries()
            elif PARAMS['show'][0] == 'listAZ':
                drDkTvAddon.showAZ()
            elif PARAMS['show'][0] == 'mostViewed':
                drDkTvAddon.showMostViewedVideos()
            elif PARAMS['show'][0] == 'search':
                drDkTvAddon.searchVideos()
            elif PARAMS['show'][0] == 'favorites':
                drDkTvAddon.showFavorites()
            elif PARAMS['show'][0] == 'recentlyWatched':
                drDkTvAddon.showRecentlyWatched()

        elif 'listProgramSeriesByLetter' in PARAMS:
            drDkTvAddon.showProgramSeries(letter=PARAMS['listProgramSeriesByLetter'][0])

        elif 'listVideos' in PARAMS:
            drDkTvAddon.showProgramSeriesVideos(PARAMS['listVideos'][0])

        elif 'videoasset' in PARAMS:
            drDkTvAddon.playVideo(PARAMS['videoasset'][0], PARAMS['urn'][0])

        elif 'addfavorite' in PARAMS:
            drDkTvAddon.addFavorite(PARAMS['addfavorite'][0])

        elif 'delfavorite' in PARAMS:
            drDkTvAddon.delFavorite(PARAMS['delfavorite'][0])

        else:
            drDkTvAddon.showMainMenu()

    except tvapi.TvNuException, ex:
        drDkTvAddon.displayError(str(ex))

    except IOError, ex:
        drDkTvAddon.displayIOError(str(ex))

    except Exception:
        buggalo.onExceptionRaised()
