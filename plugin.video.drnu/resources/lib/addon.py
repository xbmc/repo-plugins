#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
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
from pathlib import Path
import pickle
import traceback
import time
import urllib.parse as urlparse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from xbmcvfs import translatePath
from inputstreamhelper import Helper

from resources.lib import tvapi
from resources.lib import tvgui

addon = xbmcaddon.Addon()
get_setting = addon.getSetting
addon_path = addon.getAddonInfo('path')
resources_path = Path(addon_path)/'resources'
addon_name = addon.getAddonInfo('name')

SLUG_ADULT = 'dr1,dr2,dr3,dr-k'


def tr(id):
    if isinstance(id, list):
        return '\n'.join([addon.getLocalizedString(item) for item in id])
    return addon.getLocalizedString(id)


def bool_setting(name):
    return get_setting(name) == 'true'


def make_notice(object):
    xbmc.log(str(object), xbmc.LOGDEBUG)


class DrDkTvAddon(object):
    def __init__(self, plugin_url, plugin_handle):
        self._plugin_url = plugin_url
        self._plugin_handle = plugin_handle

        self.cache_path = Path(translatePath(addon.getAddonInfo('profile')))
        self.cache_path.mkdir(parents=True, exist_ok=True)

        self.favorites_path = self.cache_path/'favorites6.pickle'
        self.recent_path = self.cache_path/'recent6.pickle'
        self.search_path = self.cache_path/'search6.pickle'
        self.fanart_image = str(resources_path/'fanart.jpg')

        self.api = tvapi.Api(self.cache_path, tr, get_setting)
        self.favorites = {}
        self.recentlyWatched = []

        self.menuItems = list()
        runScript = "RunAddon(plugin.video.drnu,?show=areaselector)"
        self.menuItems.append((tr(30511), runScript))

        # Area Selector
        self.area_item = xbmcgui.ListItem(tr(30101), offscreen=True)
        self.area_item.setArt({'fanart': self.fanart_image, 'icon': str(resources_path/'icons/all.png')})

        self._load()

    def _save(self):
        # save favorites
        self.favorites = dict(sorted(self.favorites.items()))
        pickle.dump(self.favorites, self.favorites_path.open('wb'))

        self.recentlyWatched = self.recentlyWatched[0:25]  # Limit to 25 items
        pickle.dump(self.recentlyWatched, self.recent_path.open('wb'))

    def _load(self):
        # load favorites
        if self.favorites_path.exists():
            try:
                self.favorites = pickle.load(self.favorites_path.open('rb'))
            except Exception:
                pass

        # load recently watched
        if self.recent_path.exists():
            try:
                self.recentlyWatched = pickle.load(self.recent_path.open('rb'))
            except Exception:
                pass

    def showAreaSelector(self):
        gui = tvgui.AreaSelectorDialog(tr, resources_path)
        gui.doModal()
        areaSelected = gui.areaSelected
        del gui

        if areaSelected == 'none':
            pass
        elif areaSelected == 'drtv':
            self.showMainMenu()
        else:
            items = self.api.get_children_front_items('dr-' + areaSelected)
            self.listEpisodes(items)

    def showMainMenu(self):
        items = []

        # Live TV
        item = xbmcgui.ListItem(tr(30027), offscreen=True)
        item.setArt({'fanart': self.fanart_image, 'icon': str(resources_path/'icons/livetv.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=liveTV', item, True))

        for hitem in self.api.get_home():
            if hitem['path']:
                item = xbmcgui.ListItem(hitem['title'], offscreen=True)
                png = hitem.get('icon', 'star.png')
                item.setArt({'fanart': self.fanart_image, 'icon': str(resources_path/f'icons/{png}')})
                item.addContextMenuItems(self.menuItems, False)
                items.append((self._plugin_url + '?listVideos=' + hitem['path'], item, True))

        # Search videos
        item = xbmcgui.ListItem(tr(30003), offscreen=True)
        item.setArt({'fanart': self.fanart_image, 'icon': str(resources_path/'icons/search.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=search', item, True))

        # Recently watched Program Series
        item = xbmcgui.ListItem(tr(30007), offscreen=True)
        item.setArt({'fanart': self.fanart_image, 'icon': str(resources_path/'icons/eye-star.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=recentlyWatched', item, True))

        # Favorite Program Series
        item = xbmcgui.ListItem(tr(30008), offscreen=True)
        item.setArt({'fanart': self.fanart_image, 'icon': str(resources_path/'icons/plusone.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=favorites', item, True))

        if bool_setting('enable.areaitem'):
            items.append((self._plugin_url + '?show=areaselector', self.area_item, True))

        xbmcplugin.addDirectoryItems(self._plugin_handle, items)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def showFavorites(self):
        self._load()
        if not self.favorites:
            xbmcgui.Dialog().ok(addon_name, tr(30013))
            xbmcplugin.endOfDirectory(self._plugin_handle, succeeded=False)
        else:
            series = []
            for title, path in self.favorites.items():
                series.extend([self.api.get_programcard(path)['entries'][0]['item']['show']])
            self.listEpisodes(series, seasons=True)

    def showRecentlyWatched(self):
        self._load()
        videos = []
        for path in self.recentlyWatched:
            try:
                item = self.api.get_programcard(path)
                if item is None:
                    self.recentlyWatched.remove(path)
                else:
                    videos.append(item['entries'][0]['item'])
            except tvapi.ApiException:
                # probably a 404 - non-existent slug
                self.recentlyWatched.remove(path)

        self._save()
        if not videos:
            xbmcgui.Dialog().ok(addon_name, tr([30013, 30020]))
            xbmcplugin.endOfDirectory(self._plugin_handle, succeeded=False)
        else:
            self.listEpisodes(videos)

    def showLiveTV(self):
        items = []
        for channel in self.api.getLiveTV():
            item = xbmcgui.ListItem(channel['title'], offscreen=True)
            item.setArt({'thumb': channel['item']['images']['logo'],
                         'icon': channel['item']['images']['logo'],
                         'fanart': channel['item']['images']['logo']})
            item.addContextMenuItems(self.menuItems, False)
            if bool_setting('enable.subtitles'):
                url = channel['item']['customFields']['hlsWithSubtitlesURL']
            else:
                url = channel['item']['customFields']['hlsURL']
            item.setInfo('video', {
                'title': channel['title'],
                'plot': channel['schedule_str'],
                })
            item.setProperty('IsPlayable', 'true')
            items.append((url, item, False))

        xbmcplugin.setContent(self._plugin_handle, 'episodes')
        xbmcplugin.addDirectoryItems(self._plugin_handle, items)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def search(self):
        keyboard = xbmc.Keyboard('', tr(30003))
        keyboard.doModal()
        if keyboard.isConfirmed():
            keyword = keyboard.getText()
            search_results = self.api.search(keyword)
            directoryItems = []
            for key in [
                    'series',
                    'playable',
                    'competitions',
                    'confederations',
                    'events',
                    'movies',
                    'newshighlights',
                    'persons',
                    'teams',
                    'tv']:
                if search_results[key]['size'] > 0:
                    url = self._plugin_url + f"?searchresult={key}"
                    directoryItems.append((url, xbmcgui.ListItem(
                        f'{key.capitalize()} ({search_results[key]["size"]} found)', offscreen=True), True,))

            if directoryItems:
                pickle.dump(search_results, self.search_path.open('wb'))
                xbmcplugin.addDirectoryItems(self._plugin_handle, directoryItems)
                xbmcplugin.endOfDirectory(self._plugin_handle)

    def kodi_item(self, item, is_season=False):
        menuItems = list(self.menuItems)
        isFolder = item['type'] not in ['program', 'episode']
        if item['type'] in ['ImageEntry', 'TextEntry'] or item['title'] == '':
            return None

        title, infoLabels = self.api.get_info(item)
        listItem = xbmcgui.ListItem(title, offscreen=True)
        if 'images' in item:
            listItem.setArt({'thumb': item['images']['tile'],
                            'icon': item['images']['tile'],
                             'fanart': item['images']['wallpaper']
                             })
        else:
            listItem.setArt({'fanart': self.fanart_image, 'icon': str(resources_path/'icons/star.png')})

        if isFolder:
            if title in self.favorites:
                runScript = f"RunPlugin(plugin://plugin.video.drnu/?delfavorite={title})"
                menuItems.append((tr(30201), runScript))
            else:
                if item['type'] not in ['ListEntry', 'RecommendationEntry']:
                    runScript = f"RunPlugin(plugin://plugin.video.drnu/?addfavorite={title}&favoritepath={item['path']})"
                    menuItems.append((tr(30200), runScript))
            if item.get('path', False):
                url = self._plugin_url + f"?listVideos={item['path']}&seasons={is_season}"
            elif 'list' in item:
                param = item['list'].get('parameter', 'NoParam')
                url = self._plugin_url + \
                    f"?listVideos=ID_{item['list']['id']}&list_param={param}&seasons={is_season}"
            else:
                return None
        else:
            kids = self.api.kids_item(item)
            url = self._plugin_url + f"?playVideo={item['id']}&kids={str(kids)}&idpath={item['path']}"
            listItem.setProperty('IsPlayable', 'true')

        listItem.setInfo('video', infoLabels)
        listItem.addContextMenuItems(menuItems, False)
        return (url, listItem, isFolder,)

    def listEpisodes(self, items, addSortMethods=False, seasons=False):
        directoryItems = list()
        for item in items:
            gui_item = self.kodi_item(item, is_season=seasons)
            if gui_item is not None:
                directoryItems.append(gui_item)

        xbmcplugin.setContent(self._plugin_handle, 'episodes')
        xbmcplugin.addDirectoryItems(self._plugin_handle, directoryItems)
        if addSortMethods:
            xbmcplugin.addSortMethod(self._plugin_handle, xbmcplugin.SORT_METHOD_DATE)
            xbmcplugin.addSortMethod(self._plugin_handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def list_entries(self, path, seasons=False):
        entries = self.api.get_programcard(path)['entries']
        if len(entries) > 1:
            self.listEpisodes(entries)
        else:
            item = entries[0]
            if item['type'] == 'ItemEntry':
                if item['item']['type'] == 'season':
                    if seasons or item['item']['show']['availableSeasonCount'] == 1:
                        # we have shown the root of this series (or only one season anyhow)
                        self.listEpisodes(item['item']['episodes']['items'], seasons=False)
                    else:
                        # list only the season items of this series
                        self.listEpisodes(item['item']['show']['seasons']['items'], seasons=True)
                else:
                    raise tvapi.ApiException(f"{item['item']['type']} unknown")
            elif item['type'] == 'ListEntry':
                items = self.api.unfold_list(item['list'])
                self.listEpisodes(items)
            else:
                raise tvapi.ApiException(f"{item['type']} unknown")

    def playVideo(self, id, kids_channel, path):
        self.updateRecentlyWatched(path)
        video = self.api.get_stream(id)
        subs = {}
        for i, sub in enumerate(video['subtitles']):
            subs[sub['language']] = i
        kids_channel = kids_channel == 'True'

        if not video['url']:
            self.displayError(tr(30904))
            return

        item = xbmcgui.ListItem(path=video['url'], offscreen=True)

        if get_setting('inputstream') == 'adaptive':
            is_helper = Helper('hls')
            if is_helper.check_inputstream():
                item.setProperty('inputstream', is_helper.inputstream_addon)
                item.setProperty('inputstream.adaptive.manifest_type', 'hls')

        xbmcplugin.setResolvedUrl(self._plugin_handle, video['url'] is not None, item)
        if len(subs) == 0:
            return

        player = xbmc.Player()
        # Wait for positive confirmation of playback
        t = 0
        dt = 0.2
        while not player.isPlaying():
            t += dt
            if t >= 5:
                # Still not playing after 10 seconds, giving up...
                return
            else:
                time.sleep(dt)
        time.sleep(1)  # wait 1 more second to make sure it has fully started

        # Set subtitles according to setting wishes
        if player.isPlaying():
            if all([bool_setting('disable.kids.subtitles') and kids_channel]):
                player.showSubtitles(False)
            elif bool_setting('enable.subtitles'):
                for type in ['DanishLanguageSubtitles', 'CombinedLanguageSubtitles', 'ForeignLanguageSubtitles']:
                    if type in subs:
                        player.setSubtitleStream(subs[type])
                        player.showSubtitles(True)
                        return
            else:
                if 'ForeignLanguageSubtitles' in subs:
                    player.setSubtitleStream(subs['ForeignLanguageSubtitles'])
                    player.showSubtitles(True)
                else:
                    player.showSubtitles(False)

    def addFavorite(self, title, path):
        self._load()
        if title not in self.favorites:
            self.favorites[title] = path
        self._save()
        xbmcgui.Dialog().ok(addon_name, tr([30008, 30009]))

    def delFavorite(self, title):
        self._load()
        if title in self.favorites:
            del self.favorites[title]
        self._save()
        xbmcgui.Dialog().ok(addon_name, tr([30008, 30010]))

    def updateRecentlyWatched(self, path):
        self._load()
        if path in self.recentlyWatched:
            self.recentlyWatched.remove(path)
        self.recentlyWatched.insert(0, path)
        self._save()

    def displayError(self, message='n/a'):
        heading = 'API error'
        xbmcgui.Dialog().ok(heading, '\n'.join([tr(30900), tr(30901), message]))

    def displayIOError(self, message='n/a'):
        heading = 'I/O error'
        xbmcgui.Dialog().ok(heading, '\n'.join([tr(30902), tr(30903), message]))

    def route(self, query):
        try:
            PARAMS = dict(urlparse.parse_qsl(query[1:]))
            if 'show' in PARAMS:
                if PARAMS['show'] == 'liveTV':
                    self.showLiveTV()
                elif PARAMS['show'] == 'search':
                    self.search()
                elif PARAMS['show'] == 'favorites':
                    self.showFavorites()
                elif PARAMS['show'] == 'recentlyWatched':
                    self.showRecentlyWatched()
                elif PARAMS['show'] == 'areaselector':
                    self.showAreaSelector()
            elif 'searchresult' in PARAMS:
                search_results = pickle.load(self.search_path.open('rb'))
                self.listEpisodes(search_results[PARAMS['searchresult']]['items'])

            elif 'listVideos' in PARAMS:
                seasons = PARAMS.get('seasons', 'False') == 'True'
                if PARAMS['listVideos'].startswith('ID_'):
                    items = self.api.get_list(PARAMS['listVideos'], PARAMS['list_param'])
                    self.listEpisodes(self.api.unfold_list(items, filter_kids=bool_setting('disable.kids')))
                else:
                    self.list_entries(PARAMS['listVideos'], seasons)

            elif 'playVideo' in PARAMS:
                self.playVideo(PARAMS['playVideo'], PARAMS['kids'], PARAMS['idpath'])

            elif 'addfavorite' in PARAMS:
                self.addFavorite(PARAMS['addfavorite'], PARAMS['favoritepath'])

            elif 'delfavorite' in PARAMS:
                self.delFavorite(PARAMS['delfavorite'])

            elif 're-cache' in PARAMS:
                progress = xbmcgui.DialogProgress()
                progress.create("video.drnu")
                progress.update(0)
                self.api.recache_items(clear_expired=True, progress=progress)
                progress.update(100)
                progress.close()

            else:
                area = int(get_setting('area'))
                if area == 0:
                    self.showAreaSelector()
                elif area == 1:
                    self.showMainMenu()
                elif area == 2:
                    items = self.api.get_children_front_items('dr-ramasjang')
                    self.listEpisodes(items)
                elif area == 3:
                    items = self.api.get_children_front_items('dr-ultra')
                    self.listEpisodes(items)

        except tvapi.ApiException as ex:
            self.displayError(str(ex))

        except IOError as ex:
            self.displayIOError(str(ex))

        except Exception as ex:
            stack = traceback.format_exc()
            heading = 'drnu addon crash'
            xbmcgui.Dialog().ok(heading, '\n'.join([tr(30906), tr(30907), str(stack)]))
            raise ex
