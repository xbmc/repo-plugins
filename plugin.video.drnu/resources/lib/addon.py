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
from resources.lib.iptvmanager import IPTVManager

addon = xbmcaddon.Addon()
get_setting = addon.getSetting
set_setting = addon.setSetting
get_addon_info = addon.getAddonInfo
addon_path = get_addon_info('path')
addon_name = get_addon_info('name')
resources_path = Path(addon_path)/'resources'


def tr(id):
    if isinstance(id, list):
        return '\n'.join([addon.getLocalizedString(item) for item in id])
    return addon.getLocalizedString(id)


def bool_setting(name):
    return get_setting(name) == 'true'


def make_notice(object, level=0):
    xbmc.log(str(object), level)


def kodi_version():
    """Returns full Kodi version as string"""
    return xbmc.getInfoLabel('System.BuildVersion').split(' ')[0]


def kodi_version_major():
    """Returns major Kodi version as integer"""
    return int(kodi_version().split('.')[0])


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
        self._version_change_fixes()

    def _save(self):
        # save favorites
        self.favorites = dict(sorted(self.favorites.items()))
        with self.favorites_path.open('wb') as fh:
            pickle.dump(self.favorites, fh)

        self.recentlyWatched = self.recentlyWatched[0:25]  # Limit to 25 items
        with self.recent_path.open('wb') as fh:
            pickle.dump(self.recentlyWatched, fh)

    def _load(self):
        # load favorites
        if self.favorites_path.exists():
            try:
                with self.favorites_path.open('rb') as fh:
                    self.favorites = pickle.load(fh)
            except Exception:
                pass

        # load recently watched
        if self.recent_path.exists():
            try:
                with self.recent_path.open('rb') as fh:
                    self.recentlyWatched = pickle.load(fh)
            except Exception:
                pass

    def _version_change_fixes(self):
        first_run, settings_version, settings_tuple = self._version_check()
        if first_run:
            if settings_version == '' and kodi_version_major() <= 19:
                # kodi matrix subtitle handling https://github.com/xbmc/inputstream.adaptive/issues/1037
                set_setting('enable.localsubtitles', 'true')

    def _version_check(self):
        # Get version from settings.xml
        settings_version = get_setting('version')

        # Get version from addon.xml
        addon_version = get_addon_info('version')

        # Compare versions (settings_version was not present in version 6.0.2 and older)
        settings_tuple = tuple(map(int, settings_version.split('+')[0].split('.'))) if settings_version != '' else (6, 0, 2)
        addon_tuple = tuple(map(int, addon_version.split('+')[0].split('.')))

        if addon_tuple > settings_tuple:
            # New version found, save addon version to settings
            set_setting('version', addon_version)
            return True, settings_version, settings_tuple

        return False, settings_version, settings_tuple

    def showAreaSelector(self):
        if bool_setting('use.simpleareaitem'):
            self.showSimpleAreaSelector()
        else:
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

    def showSimpleAreaSelector(self):
        items = list()
        # DRTV
        item = xbmcgui.ListItem('DR TV', offscreen=True)
        item.setArt({'fanart': str(resources_path/'media/button-drtv.png'),
                     'icon': str(resources_path/'media/button-drtv.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?area=1', item, True))
        # Minisjang
        item = xbmcgui.ListItem('Minisjang', offscreen=True)
        item.setArt({'fanart': str(resources_path/'media/button-minisjang.png'),
                     'icon': str(resources_path/'media/button-minisjang.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?area=2', item, True))
        # Ramasjang
        item = xbmcgui.ListItem('Ramasjang', offscreen=True)
        item.setArt({'fanart': str(resources_path/'media/button-ramasjang.png'),
                     'icon': str(resources_path/'media/button-ramasjang.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?area=3', item, True))
        # Ultra
        item = xbmcgui.ListItem('Ultra', offscreen=True)
        item.setArt({'fanart': str(resources_path/'media/button-ultra.png'),
                     'icon': str(resources_path/'media/button-ultra.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?area=4', item, True))

        xbmcplugin.addDirectoryItems(self._plugin_handle, items)
        xbmcplugin.endOfDirectory(self._plugin_handle)

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
                item = self.api.get_item(path)
                item['kodi_delfavorit'] = True
                item['kodi_seasons'] = item['type'] != 'show'
                series.append(item)
            self.listEpisodes(series)

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

    def getIptvLiveChannels(self):
        iptv_channels = []
        for api_channel in self.api.getLiveTV():

            lowername = api_channel['title'].lower().replace(' ', '')
            if not bool_setting('iptv.channels.include.' + lowername):
                 continue

            iptv_channel = {
                'name': api_channel['title'],
                'stream': self.api.get_channel_url(api_channel, bool_setting('enable.subtitles')),
                'logo': api_channel['item']['images']['logo'],
                'id': 'drnu.' + api_channel['item']['id'],
                'preset': tvapi.CHANNEL_PRESET[api_channel['title']]
            }
            iptv_channels.append(iptv_channel)
        return iptv_channels

    def getIptvEpg(self):
        lookforward_hours = int(get_setting('iptv.schedule.lookahead'))
        channel_schedules = self.api.get_schedules(duration=lookforward_hours)
        epg = {}
        for channel in channel_schedules:
            channel_epg_id = 'drnu.' + channel['channelId']
            if channel_epg_id not in epg:
                epg[channel_epg_id] = []
            channel_epg = []
            for schedule in channel['schedules']:
                schedule_dict = {
                    'start' : schedule['startDate'],
                    'stop' : schedule['endDate'],
                    'title': schedule['item']['title'],
                    'description': schedule['item']['description'],
                    'image' : schedule['item']['images']['tile'],
                                }
                if ('seasonNumber' in schedule['item']) and ('episodeNumber' in schedule['item']):
                    schedule_dict['episode'] = 'S{:02d}E{:02d}'.format(
                        schedule['item']['seasonNumber'], schedule['item']['episodeNumber'])
                if ('path' in schedule['item']):
                    schedule_dict['stream'] = "{}?playVideo={}&kids={}&idpath={}".format(
                        self._plugin_url,
                        schedule['item']['id'],
                        self.api.kids_item(schedule['item']),
                        schedule['item']['path'],
                    )
                channel_epg.append(schedule_dict)
            epg[channel_epg_id] += channel_epg
        return epg

    def showLiveTV(self):
        items = []
        for channel in self.api.getLiveTV():
            item = xbmcgui.ListItem(channel['title'], offscreen=True)
            item.setArt({'thumb': channel['item']['images']['logo'],
                         'icon': channel['item']['images']['logo'],
                         'fanart': channel['item']['images']['logo']})
            item.addContextMenuItems(self.menuItems, False)
            url = self.api.get_channel_url(channel, bool_setting('enable.subtitles'))
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
                with self.search_path.open('wb') as fh:
                    pickle.dump(search_results, fh)
                xbmcplugin.addDirectoryItems(self._plugin_handle, directoryItems)
                xbmcplugin.endOfDirectory(self._plugin_handle)

    def kodi_item(self, item, is_season=False):
        menuItems = list(self.menuItems)
        isFolder = item['type'] not in ['program', 'episode', 'link']
        if item['type'] in ['ImageEntry', 'TextEntry'] or item['title'] == '':
            return None
        if 'kodi_seasons' in item:
            is_season = item['kodi_seasons']
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
            if title in self.favorites or item.get('kodi_delfavorit', False):
                runScript = f"RunPlugin(plugin://plugin.video.drnu/?delfavorite={title})"
                menuItems.append((tr(30201), runScript))
            else:
                if item['type'] not in ['ListEntry', 'RecommendationEntry']:
                    runScript = f"RunPlugin(plugin://plugin.video.drnu/?addfavorite={title}&favoritepath={item['id']})"
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
        use_cache = tvapi.cache_path(path)
        entries = self.api.get_programcard(path, use_cache=use_cache)['entries']
        if len(entries) == 0:
            # hack for get_programcard('/liste/306104') giving empty entries, but recommendations yields?!?
            id = int(path.split('/')[-1])
            self.listEpisodes(self.api.get_recommendations(id)['items'])
        elif len(entries) > 1:
            self.listEpisodes(entries)
        else:
            item = entries[0]
            if item['type'] == 'ItemEntry':
                if item['item']['type'] == 'season':
                    if seasons or item['item']['show']['availableSeasonCount'] == 1:
                        # we have shown the root of this series (or only one season anyhow)
                        self.listEpisodes(item['item']['episodes']['items'], seasons=False)
                    elif self.api.kids_item(item['item']) and bool_setting('disable.kids.seasons'):
                        # let's not have seasons on children items
                        collect_episodes = []
                        for season_item in item['item']['show']['seasons']['items']:
                            if season_item['id'] == item['item']['episodes']['items'][0]['seasonId']:
                                collect_episodes += self.api.unfold_list(item['item']['episodes'])
                            else:
                                newitem = self.api.get_programcard(season_item['path'])['entries'][0]
                                collect_episodes += self.api.unfold_list(newitem['item']['episodes'])
                        self.listEpisodes(collect_episodes, seasons=False)
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
        if path.startswith('/kanal'):
            # live stream
            video = self.api.get_livestream(path, with_subtitles=bool_setting('enable.subtitles'))
            video['srt_subtitles'] = []
        else:
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

        local_subs_bool = bool_setting('enable.localsubtitles') or get_setting('inputstream') == 'ffmpegdirect'
        if local_subs_bool and video['srt_subtitles']:
            item.setSubtitles(video['srt_subtitles'])
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
                if local_subs_bool:
                    player.setSubtitles(video['srt_subtitles'][-1])
                    player.showSubtitles(True)
                    return

                for type in ['DanishLanguageSubtitles', 'CombinedLanguageSubtitles', 'ForeignLanguageSubtitles']:
                    if type in subs:
                        player.setSubtitleStream(subs[type])
                        player.showSubtitles(True)
                        return
            else:
                if 'ForeignLanguageSubtitles' in subs:
                    if local_subs_bool:
                        player.setSubtitles(video['srt_subtitles'][0])
                        player.showSubtitles(True)
                        return
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
            # iptv manager integration
            elif 'iptv' in PARAMS:
                if PARAMS['iptv'] == 'channels':
                    IPTVManager(int(PARAMS['port']), channels=self.getIptvLiveChannels()).send_channels()
                elif PARAMS['iptv'] == 'epg':
                    IPTVManager(int(PARAMS['port']), epg=self.getIptvEpg()).send_epg()
            elif 'searchresult' in PARAMS:
                with self.search_path.open('rb') as fh:
                    search_results = pickle.load(fh)
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
                if 'area' in PARAMS:
                    area = int(PARAMS['area'])
                if area == 0:
                    self.showAreaSelector()
                elif area == 1:
                    self.showMainMenu()
                elif area == 2:
                    items = self.api.get_children_front_items('dr-minisjang')
                    self.listEpisodes(items)
                elif area == 3:
                    items = self.api.get_children_front_items('dr-ramasjang')
                    self.listEpisodes(items)
                elif area == 4:
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
