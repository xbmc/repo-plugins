#
#      Copyright (C) 2014 Tommy Winther, msj33, TermeHansen
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

from resources.lib import tvapi
from resources.lib import tvgui

import buggalo

tr = xbmcaddon.Addon().getLocalizedString
get_setting = xbmcaddon.Addon().getSetting
addon_path = xbmcaddon.Addon().getAddonInfo('path')
addon_name = xbmcaddon.Addon().getAddonInfo('name')

def make_notice(object):
    xbmc.log(str(object), xbmc.LOGNOTICE )

class DrDkTvAddon(object):
    def __init__(self, plugin_url, plugin_handle):
        self._plugin_url = plugin_url
        self._plugin_handle = plugin_handle
        # PATH = sys.argv[0]
        # HANDLE = int(sys.argv[1])

        self.cache_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

        self.favorites_path = os.path.join(self.cache_path, 'favorites.pickle')
        self.recent_path = os.path.join(self.cache_path, 'recent.pickle')
        self.fanart_image = os.path.join(addon_path, 'resources', 'fanart.jpg')

        self.api = tvapi.Api(self.cache_path)
        self.favorites = list()
        self.recentlyWatched = list()

        self.menuItems = list()
        runScript = "RunAddon(plugin.video.drnu,?show=areaselector&random=%d)" % self._plugin_handle
        self.menuItems.append((tr(30511), runScript))


    def _save(self):
        # save favorites
        self.favorites.sort()
        pickle.dump(self.favorites, open(self.favorites_path, 'wb'))

        self.recentlyWatched = self.recentlyWatched[0:25]  # Limit to 25 items
        pickle.dump(self.recentlyWatched, open(self.recent_path, 'wb'))

    def _load(self):
        # load favorites
        if os.path.exists(self.favorites_path):
            try:
                self.favorites = pickle.load(open(self.favorites_path, 'rb'))
            except Exception:
                pass

        # load recently watched
        if os.path.exists(self.recent_path):
            try:
                self.recentlyWatched = pickle.load(open(self.recent_path, 'rb'))
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
        item = xbmcgui.ListItem(tr(30027), iconImage=os.path.join(addon_path, 'resources', 'icons', 'livetv.png'))
        item.setProperty('Fanart_Image', self.fanart_image)
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=liveTV', item, True))

        # A-Z Program Series
        item = xbmcgui.ListItem(tr(30000), iconImage=os.path.join(addon_path, 'resources', 'icons', 'all.png'))
        item.setProperty('Fanart_Image', self.fanart_image)
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=listAZ', item, True))

        # Latest
        item = xbmcgui.ListItem(tr(30001), iconImage=os.path.join(addon_path, 'resources', 'icons', 'all.png'))
        item.setProperty('Fanart_Image', self.fanart_image)
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=latest', item, True))

        # Premiere
        item = xbmcgui.ListItem(tr(30025), iconImage=os.path.join(addon_path, 'resources', 'icons', 'new.png'))
        item.setProperty('Fanart_Image', self.fanart_image)
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?listVideos=%s' % tvapi.SLUG_PREMIERES, item, True))

        # Themes
        item = xbmcgui.ListItem(tr(30028), iconImage=os.path.join(addon_path, 'resources', 'icons', 'all.png'))
        item.setProperty('Fanart_Image', self.fanart_image)
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=themes', item, True))

        # Most viewed
        item = xbmcgui.ListItem(tr(30011), iconImage=os.path.join(addon_path, 'resources', 'icons', 'eye.png'))
        item.setProperty('Fanart_Image', self.fanart_image)
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=mostViewed', item, True))

        # Spotlight
        item = xbmcgui.ListItem(tr(30002), iconImage=os.path.join(addon_path, 'resources', 'icons', 'star.png'))
        item.setProperty('Fanart_Image', self.fanart_image)
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=highlights', item, True))

        # Search videos
        item = xbmcgui.ListItem(tr(30003), iconImage=os.path.join(addon_path, 'resources', 'icons', 'search.png'))
        item.setProperty('Fanart_Image', self.fanart_image)
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=search', item, True))

        # Recently watched Program Series
        item = xbmcgui.ListItem(tr(30007), iconImage=os.path.join(addon_path, 'resources', 'icons', 'eye-star.png'))
        item.setProperty('Fanart_Image', self.fanart_image)
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=recentlyWatched', item, True))

        # Favorite Program Series
        item = xbmcgui.ListItem(tr(30008), iconImage=os.path.join(addon_path, 'resources', 'icons', 'plusone.png'))
        item.setProperty('Fanart_Image', self.fanart_image)
        items.append((self._plugin_url + '?show=favorites', item, True))
        item.addContextMenuItems(self.menuItems, False)

        xbmcplugin.addDirectoryItems(self._plugin_handle, items)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def showFavorites(self):
        self._load()
        if not self.favorites:
            xbmcgui.Dialog().ok(addon_name, tr(30013))
            xbmcplugin.endOfDirectory(self._plugin_handle, succeeded=False)
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
            xbmcgui.Dialog().ok(addon_name, tr(30013), tr(30020))
            xbmcplugin.endOfDirectory(self._plugin_handle, succeeded=False)
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

            item = xbmcgui.ListItem(channel['Title'])
            fanart_h = int(get_setting('fanart.size'))
            fanart_w = int(fanart_h*16/9)            
            item.setArt({'thumb': self.api.redirectImageUrl(channel['PrimaryImageUri'], 640, 360),
                         'icon': self.api.redirectImageUrl(channel['PrimaryImageUri'], 75, 42),
                         'fanart': self.api.redirectImageUrl(channel['PrimaryImageUri'], fanart_w, fanart_h)}) 
            item.addContextMenuItems(self.menuItems, False)

            url = server['Server'] + '/' + server['Qualities'][0]['Streams'][0]['Stream']
            items.append((url, item, False))

        items = sorted(items, lambda mine, yours: cmp(mine[1].getLabel().replace(' ', ''), yours[1].getLabel().replace(' ', '')))

        xbmcplugin.addDirectoryItems(self._plugin_handle, items)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def showAZ(self):
        # All Program Series
        iconImage = os.path.join(addon_path, 'resources', 'icons', 'all.png')
        items = list()
        for programIndex in self.api.getProgramIndexes():
            item = xbmcgui.ListItem(programIndex['Title'], iconImage=iconImage)
            item.setProperty('Fanart_Image', self.fanart_image)
            item.addContextMenuItems(self.menuItems, False)

            url = self._plugin_url + '?listProgramSeriesByLetter=' + programIndex['_Param']
            items.append((url, item, True))
        xbmcplugin.addDirectoryItems(self._plugin_handle, items)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def showThemes(self):
        iconImage = os.path.join(addon_path, 'resources', 'icons', 'all.png')

        items = list()
        for theme in self.api.getThemes():
            item = xbmcgui.ListItem(theme['Title'], iconImage=iconImage)
            item.setProperty('Fanart_Image', self.fanart_image)
            item.addContextMenuItems(self.menuItems, False)

            url = self._plugin_url + '?listThemeSeries=' + theme['Paging']['Source'].split('list/',1)[1]
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(self._plugin_handle, items)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def searchSeries(self):
        keyboard = xbmc.Keyboard('', tr(30003))
        keyboard.doModal()
        if keyboard.isConfirmed():
            keyword = keyboard.getText()
            self.listSeries(self.api.getSeries(keyword))

    def listSeries(self, items, addToFavorites=True):
        if not items:
            xbmcplugin.endOfDirectory(self._plugin_handle, succeeded=False)
            if not addToFavorites:
                xbmcgui.Dialog().ok(addon_name, tr(30013),
                                    tr(30018), tr(30019))
            else:
                xbmcgui.Dialog().ok(addon_name, tr(30013))
        else:
            directoryItems = list()
            for item in items:
                menuItems = list(self.menuItems)

                if self.favorites.count(item['SeriesTitle']) > 0:
                    runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?delfavorite=%s)" % item['SeriesTitle'].replace('&', '%26').replace(',', '%2C')
                    menuItems.append((tr(30201), runScript))
                else:
                    runScript = "XBMC.RunPlugin(plugin://plugin.video.drnu/?addfavorite=%s)" % item['SeriesTitle'].replace('&', '%26').replace(',', '%2C')
                    menuItems.append((tr(30200), runScript))


                listItem = xbmcgui.ListItem(item['SeriesTitle'])
                fanart_h = int(get_setting('fanart.size'))
                fanart_w = int(fanart_h*16/9)            
                listItem.setArt({'thumb': self.api.redirectImageUrl(item['PrimaryImageUri'], 640, 360),
                          	 'icon': self.api.redirectImageUrl(item['PrimaryImageUri'], 75, 42),
                          	 'fanart': self.api.redirectImageUrl(item['PrimaryImageUri'], fanart_w, fanart_h)})
                listItem.addContextMenuItems(menuItems, False)

                url = self._plugin_url + '?listVideos=' + item['SeriesSlug']
                directoryItems.append((url, listItem, True))

            xbmcplugin.addDirectoryItems(self._plugin_handle, directoryItems)
            xbmcplugin.endOfDirectory(self._plugin_handle)

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

            listItem = xbmcgui.ListItem(item['Title'])
            fanart_h = int(get_setting('fanart.size'))
            fanart_w = int(fanart_h*16/9)            
            listItem.setArt({'thumb': self.api.redirectImageUrl(item['PrimaryImageUri'], 640, 360),
                             'icon': self.api.redirectImageUrl(item['PrimaryImageUri'], 75, 42),
                             'fanart': self.api.redirectImageUrl(item['PrimaryImageUri'], fanart_w, fanart_h)})
            listItem.setInfo('video', infoLabels)
            url = self._plugin_url + '?playVideo=' + item['Slug']
            listItem.setProperty('IsPlayable', 'true')
            listItem.addContextMenuItems(self.menuItems, False)
            directoryItems.append((url, listItem))

        xbmcplugin.addDirectoryItems(self._plugin_handle, directoryItems)
        if addSortMethods:
            xbmcplugin.addSortMethod(self._plugin_handle, xbmcplugin.SORT_METHOD_DATE)
            xbmcplugin.addSortMethod(self._plugin_handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def playVideo(self, slug):
        self.updateRecentlyWatched(slug)
        item = self.api.getEpisode(slug)
        kids_channel = item['PrimaryBroadcast']['ChannelSlug'] in ['dr-ramasjang', 'dr-ultra']
        if not 'PrimaryAsset' in item:
            self.displayError(tr(30904))
            return

        video = self.api.getVideoUrl(item['PrimaryAsset']['Uri'])
        item = xbmcgui.ListItem(path=video['Uri'], thumbnailImage=item['PrimaryImageUri'])

        if not all([get_setting('disable.kids.subtitles') == 'true' and kids_channel]):
            if video['SubtitlesUri']:
                if get_setting('enable.subtitles') == 'true':
                    item.setSubtitles(video['SubtitlesUri'][::-1])
                else:
                    item.setSubtitles(video['SubtitlesUri'])
        xbmcplugin.setResolvedUrl(self._plugin_handle, video['Uri'] is not None, item)

    # Supported slugs are dr1, dr2 and dr-ramasjang
    def playLiveTV(self, slug):
        item = None
        url = None
        for channel in self.api.getLiveTV():
            # If the channel has the right slug, play the channel
            if channel['Slug'] == slug:
                server = None
                for streamingServer in channel['StreamingServers']:
                    if streamingServer['LinkType'] == 'HLS':
                        server = streamingServer
                        break
                if server is None:
                    continue

                url = server['Server'] + '/' + server['Qualities'][0]['Streams'][0]['Stream']
                item = xbmcgui.ListItem(channel['Title'], iconImage=channel['PrimaryImageUri'], path=url)
                item.setProperty('Fanart_Image', channel['PrimaryImageUri'])
                item.addContextMenuItems(self.menuItems, False)
                break
        if item:
            xbmcplugin.setResolvedUrl(self._plugin_handle, True, item)
        else:
            self.displayError(tr(30905) + ' ' + slug)

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

        xbmcgui.Dialog().ok(tr(30008), tr(30009))

    def delFavorite(self, key):
        self._load()
        if self.favorites.count(key):
            self.favorites.remove(key)
        self._save()
        xbmcgui.Dialog().ok(tr(30008), tr(30010))

    def updateRecentlyWatched(self, assetUri):
        self._load()
        if self.recentlyWatched.count(assetUri):
            self.recentlyWatched.remove(assetUri)
        self.recentlyWatched.insert(0, assetUri)
        self._save()

    def displayError(self, message='n/a'):
        heading = buggalo.getRandomHeading()
        line1 = tr(30900)
        line2 = tr(30901)
        xbmcgui.Dialog().ok(heading, line1, line2, message)

    def displayIOError(self, message='n/a'):
        heading = buggalo.getRandomHeading()
        line1 = tr(30902)
        line2 = tr(30903)
        xbmcgui.Dialog().ok(heading, line1, line2, message)

    def route(self, query):
        try:
            PARAMS = dict(urlparse.parse_qsl(query[1:]))
            if 'show' in PARAMS:
                if PARAMS['show'] == 'liveTV':
                    self.showLiveTV()
                elif PARAMS['show'] == 'listAZ':
                    self.showAZ()
                elif PARAMS['show'] == 'latest':
                    self.listEpisodes(self.api.getLatestPrograms(), addSortMethods=False)
                elif PARAMS['show'] == 'mostViewed':
                    self.listEpisodes(self.api.getMostViewed())
                elif PARAMS['show'] == 'highlights':
                    self.listEpisodes(self.api.getSelectedList())
                elif PARAMS['show'] == 'search':
                    self.searchSeries()
                elif PARAMS['show'] == 'favorites':
                    self.showFavorites()
                elif PARAMS['show'] == 'recentlyWatched':
                    self.showRecentlyWatched()
                elif PARAMS['show'] == 'areaselector':
                    self.showAreaSelector()
                elif PARAMS['show'] == 'themes':
                    self.showThemes()

            elif 'listThemeSeries' in PARAMS:
                self.listSeries(self.api.getEpisodes(PARAMS['listThemeSeries']))

            elif 'listProgramSeriesByLetter' in PARAMS:
                self.listSeries(self.api.getSeries(PARAMS['listProgramSeriesByLetter']))

            elif 'listVideos' in PARAMS:
                self.listEpisodes(self.api.getEpisodes(PARAMS['listVideos']))

            elif 'playVideo' in PARAMS:
                self.playVideo(PARAMS['playVideo'])

            # Supported slugs are dr1, dr2 and dr-ramasjang
            elif 'playLiveTV' in PARAMS:
                self.playLiveTV(PARAMS['playLiveTV'])

            elif 'addfavorite' in PARAMS:
                self.addFavorite(PARAMS['addfavorite'])

            elif 'delfavorite' in PARAMS:
                self.delFavorite(PARAMS['delfavorite'])

            else:
                try:
                    area = int(get_setting('area'))
                except:
                    area = 0

                if area == 0:
                    self.showAreaSelector()
                elif area == 1:
                    self.showMainMenu()
                elif area == 2:
                    items = self.api.getChildrenFrontItems('dr-ramasjang')
                    self.listSeries(items)
                elif area == 3:
                    items = self.api.getChildrenFrontItems('dr-ultra')
                    self.listSeries(items)

        except tvapi.ApiException as ex:
            self.displayError(str(ex))

        except IOError as ex:
            self.displayIOError(str(ex))

        except Exception:
            buggalo.onExceptionRaised()
