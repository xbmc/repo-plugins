#
#      Copyright (C) 2014 Tommy Winther, msj33
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
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
import tvgui
import buggalo


class DrDkTvAddon(object):
    def __init__(self):
        self.api = tvapi.Api(CACHE_PATH)
        self.favorites = list()
        self.recentlyWatched = list()

        self.menuItems = list()
        runScript = "RunAddon(plugin.video.drnu,?show=areaselector&random=%d)" % HANDLE
        self.menuItems.append((ADDON.getLocalizedString(30511), runScript))


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

    def showAreaSelector(self):
        gui = tvgui.AreaSelectorDialog()
        gui.doModal()
        areaSelected = gui.areaSelected
        del gui

        if areaSelected == 'none':
            pass
        elif areaSelected == 'drtv':
            self.showMainMenu()
        else:
            items = self.api.getChildrenFrontItems('dr-' + areaSelected)
            #xbmc.executebuiltin('Container.SetViewMode(500)')
            self.listSeries(items)

    def showMainMenu(self):
        items = list()
        # Live TV
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30027), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'livetv.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        item.addContextMenuItems(self.menuItems, False)
        items.append((PATH + '?show=liveTV', item, True))

        # A-Z Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30000), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'all.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        item.addContextMenuItems(self.menuItems, False)
        items.append((PATH + '?show=listAZ', item, True))

        # Latest
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30001), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'all.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        item.addContextMenuItems(self.menuItems, False)
        items.append((PATH + '?show=latest', item, True))

        # Premiere
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30025), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'new.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        item.addContextMenuItems(self.menuItems, False)
        items.append((PATH + '?listVideos=%s' % tvapi.SLUG_PREMIERES, item, True))

        # Themes / Repremiere
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30028), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'all.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        item.addContextMenuItems(self.menuItems, False)
        items.append((PATH + '?show=themes', item, True))

        # Most viewed
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30011), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'eye.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        item.addContextMenuItems(self.menuItems, False)
        items.append((PATH + '?show=mostViewed', item, True))

        # Spotlight
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30002), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'star.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        item.addContextMenuItems(self.menuItems, False)
        items.append((PATH + '?show=highlights', item, True))

        # Search videos
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30003), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'search.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        item.addContextMenuItems(self.menuItems, False)
        items.append((PATH + '?show=search', item, True))

        # Recently watched Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30007), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'eye-star.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        item.addContextMenuItems(self.menuItems, False)
        items.append((PATH + '?show=recentlyWatched', item, True))

        # Favorite Program Series
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30008), iconImage=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'plusone.png'))
        item.setProperty('Fanart_Image', FANART_IMAGE)
        items.append((PATH + '?show=favorites', item, True))
        item.addContextMenuItems(self.menuItems, False)

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def showFavorites(self):
        self._load()
        if not self.favorites:
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013))
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        else:
            series = []
            for slug in self.favorites:
                series.extend(self.api.searchSeries(slug))
            self.listSeries(series, addToFavorites=False)

    def showRecentlyWatched(self):
        self._load()
        videos = list()
        for slug in self.recentlyWatched:
            try:
                item = self.api.getEpisode(slug)
                if item is None:
                    self.recentlyWatched.remove(slug)
                else:
                    videos.append(item)
            except tvapi.ApiException:
                # probably a 404 - non-existent slug
                self.recentlyWatched.remove(slug)

        self._save()
        if not videos:
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013), ADDON.getLocalizedString(30020))
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        else:
            self.listEpisodes(videos)

    def showLiveTV(self):
        items = list()
        for channel in self.api.getLiveTV():
            if channel['WebChannel']:
                continue

            server = None
            for streamingServer in channel['StreamingServers']:
                if streamingServer['LinkType'] == 'HLS':
                    server = streamingServer
                    break

            if server is None:
                continue

            item = xbmcgui.ListItem(channel['Title'], iconImage=channel['PrimaryImageUri'])
            item.setProperty('Fanart_Image', channel['PrimaryImageUri'])
            item.addContextMenuItems(self.menuItems, False)

            url = server['Server'] + '/' + server['Qualities'][0]['Streams'][0]['Stream']
            items.append((url, item, False))

        items = sorted(items, lambda mine, yours: cmp(mine[1].getLabel().replace(' ', ''), yours[1].getLabel().replace(' ', '')))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def showAZ(self):
        # All Program Series
        iconImage = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'icons', 'all.png')

        items = list()
        for programIndex in self.api.getProgramIndexes():
            item = xbmcgui.ListItem(programIndex['Title'], iconImage=iconImage)
            item.setProperty('Fanart_Image', FANART_IMAGE)
            item.addContextMenuItems(self.menuItems, False)

            url = PATH + '?listProgramSeriesByLetter=' + programIndex['_Param']
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def showThemes(self):
        items = list()
        for theme in self.api.getThemes():
            item = xbmcgui.ListItem(theme['ThemeTitle'], iconImage=theme['PrimaryImageUri'])
            item.setProperty('Fanart_Image', theme['PrimaryImageUri'])
            item.addContextMenuItems(self.menuItems, False)

            url = PATH + '?listVideos=' + theme['ThemeSlug']
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def searchSeries(self):
        keyboard = xbmc.Keyboard('', ADDON.getLocalizedString(30003))
        keyboard.doModal()
        if keyboard.isConfirmed():
            keyword = keyboard.getText()
            self.listSeries(self.api.getSeries(keyword))

    def listSeries(self, items, addToFavorites=True):
        if not items:
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
            if not addToFavorites:
                xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013),
                                    ADDON.getLocalizedString(30018), ADDON.getLocalizedString(30019))
            else:
                xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(30013))
        else:
            directoryItems = list()
            for item in items:
                menuItems = list(self.menuItems)

                if self.favorites.count(item['SeriesTitle']) > 0:
                    runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?delfavorite=%s)" % item['SeriesTitle'].replace('&', '%26').replace(',', '%2C')
                    menuItems.append((ADDON.getLocalizedString(30201), runScript))
                else:
                    runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?addfavorite=%s)" % item['SeriesTitle'].replace('&', '%26').replace(',', '%2C')
                    menuItems.append((ADDON.getLocalizedString(30200), runScript))


                iconImage = item['PrimaryImageUri']
                listItem = xbmcgui.ListItem(item['SeriesTitle'], iconImage=iconImage)
                listItem.setProperty('Fanart_Image', iconImage)
                listItem.addContextMenuItems(menuItems, False)

                url = PATH + '?listVideos=' + item['SeriesSlug']
                directoryItems.append((url, listItem, True))

            xbmcplugin.addDirectoryItems(HANDLE, directoryItems)
            xbmcplugin.endOfDirectory(HANDLE)

    def listEpisodes(self, items, addSortMethods=True):
        directoryItems = list()
        for item in items:
            if 'PrimaryAsset' not in item or 'Uri' not in item['PrimaryAsset'] or not item['PrimaryAsset']['Uri']:
                continue

            infoLabels = {
                'title': item['Title']
            }
            if 'Description' in item:
                infoLabels['plot'] = item['Description']
            if 'PrimaryBroadcastStartTime' in item and item['PrimaryBroadcastStartTime'] is not None:
                broadcastTime = self.parseDate(item['PrimaryBroadcastStartTime'])
                if broadcastTime:
                    infoLabels['date'] = broadcastTime.strftime('%d.%m.%Y')
                    infoLabels['aired'] = broadcastTime.strftime('%Y-%m-%d')
                    infoLabels['year'] = int(broadcastTime.strftime('%Y'))

            iconImage = item['PrimaryImageUri']
            listItem = xbmcgui.ListItem(item['Title'], iconImage=iconImage)
            listItem.setInfo('video', infoLabels)
            listItem.setProperty('Fanart_Image', iconImage)
            url = PATH + '?playVideo=' + item['Slug']
            listItem.setProperty('IsPlayable', 'true')
            listItem.addContextMenuItems(self.menuItems, False)
            directoryItems.append((url, listItem))

        xbmcplugin.addDirectoryItems(HANDLE, directoryItems)
        if addSortMethods:
            xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
            xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(HANDLE)

    def playVideo(self, slug):
        self.updateRecentlyWatched(slug)
        item = self.api.getEpisode(slug)

        if not 'PrimaryAsset' in item:
            self.displayError(ADDON.getLocalizedString(30904))
            return

        video = self.api.getVideoUrl(item['PrimaryAsset']['Uri'])
        item = xbmcgui.ListItem(path=video['Uri'], thumbnailImage=item['PrimaryImageUri'])

        if ADDON.getSetting('enable.subtitles') == 'true':
            if video['SubtitlesUri']:
                item.setSubtitles([video['SubtitlesUri']])
                
        xbmcplugin.setResolvedUrl(HANDLE, video['Uri'] is not None, item)

                
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

    def addFavorite(self, key):
        self._load()
        if not self.favorites.count(key):
            self.favorites.append(key)
        self._save()

        xbmcgui.Dialog().ok(ADDON.getLocalizedString(30008), ADDON.getLocalizedString(30009))

    def delFavorite(self, key):
        self._load()
        if self.favorites.count(key):
            self.favorites.remove(key)
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
            if PARAMS['show'][0] == 'liveTV':
                drDkTvAddon.showLiveTV()
            elif PARAMS['show'][0] == 'listAZ':
                drDkTvAddon.showAZ()
            elif PARAMS['show'][0] == 'latest':
                drDkTvAddon.listEpisodes(drDkTvAddon.api.getLatestPrograms(), addSortMethods=False)
            elif PARAMS['show'][0] == 'mostViewed':
                drDkTvAddon.listEpisodes(drDkTvAddon.api.getMostViewed())
            elif PARAMS['show'][0] == 'highlights':
                drDkTvAddon.listEpisodes(drDkTvAddon.api.getSelectedList())
            elif PARAMS['show'][0] == 'search':
                drDkTvAddon.searchSeries()
            elif PARAMS['show'][0] == 'favorites':
                drDkTvAddon.showFavorites()
            elif PARAMS['show'][0] == 'recentlyWatched':
                drDkTvAddon.showRecentlyWatched()
            elif PARAMS['show'][0] == 'areaselector':
                drDkTvAddon.showAreaSelector()
            elif PARAMS['show'][0] == 'themes':
                drDkTvAddon.showThemes()

        elif 'listProgramSeriesByLetter' in PARAMS:
            drDkTvAddon.listSeries(drDkTvAddon.api.getSeries(PARAMS['listProgramSeriesByLetter'][0]))

        elif 'listVideos' in PARAMS:
            drDkTvAddon.listEpisodes(drDkTvAddon.api.getEpisodes(PARAMS['listVideos'][0]))

        elif 'playVideo' in PARAMS:
            drDkTvAddon.playVideo(PARAMS['playVideo'][0])

        elif 'addfavorite' in PARAMS:
            drDkTvAddon.addFavorite(PARAMS['addfavorite'][0])

        elif 'delfavorite' in PARAMS:
            drDkTvAddon.delFavorite(PARAMS['delfavorite'][0])

        else:
            try:
                area = int(ADDON.getSetting('area'))
            except:
                area = 0

            if area == 0:
                drDkTvAddon.showAreaSelector()
            elif area == 1:
                drDkTvAddon.showMainMenu()
            elif area == 2:
                items = drDkTvAddon.api.getChildrenFrontItems('dr-ramasjang')
                drDkTvAddon.listSeries(items)
            elif area == 3:
                items = drDkTvAddon.api.getChildrenFrontItems('dr-ultra')
                drDkTvAddon.listSeries(items)

    except tvapi.ApiException as ex:
        drDkTvAddon.displayError(str(ex))

    except IOError as ex:
        drDkTvAddon.displayIOError(str(ex))

    except Exception:
        buggalo.onExceptionRaised()
