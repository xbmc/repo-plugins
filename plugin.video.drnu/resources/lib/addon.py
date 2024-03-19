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
from distutils.version import StrictVersion

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from xbmcvfs import translatePath
from inputstreamhelper import Helper

from resources.lib import tvapi
from resources.lib import tvgui
from resources.lib.iptvmanager import IPTVManager
from resources.lib.cronjob import setup_cronjob

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


def log(object, level=0):
    if bool_setting('log.debug'):
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

        self.search_path = self.cache_path/'search6.pickle'
        self.fanart_image = str(resources_path/'fanart.jpg')

        self.api = tvapi.Api(self.cache_path, tr, get_setting)

        self.menuItems = list()
        runScript = "RunAddon(plugin.video.drnu,?show=areaselector)"
        self.menuItems.append((tr(30205), runScript))

        # Area Selector
        self.area_item = xbmcgui.ListItem(tr(30101), offscreen=True)
        self.area_item.setArt({'fanart': self.fanart_image, 'icon': str(resources_path/'icons/all.png')})
        self.current_area = 'drtv'

        setup_cronjob(addon_path, bool_setting, get_setting)
        self._version_change_fixes()

    def _version_change_fixes(self):
        first_run, settings_version, settings_V, addon_V = self._version_check()
        if first_run:
            if settings_version == '' and kodi_version_major() <= 19:
                # kodi matrix subtitle handling https://github.com/xbmc/inputstream.adaptive/issues/1037
                set_setting('enable.localsubtitles', 'true')
            elif addon_V == StrictVersion('6.2.0').version and kodi_version_major() == 20:
                set_setting('enable.localsubtitles', 'false')

    def _version_check(self):
        # Get version from settings.xml
        settings_version = get_setting('version')

        # Get version from addon.xml
        addon_version = get_addon_info('version')

        # Compare versions (settings_version was not present in version 6.0.2 and older)
        if settings_version != '':
            settings_V = StrictVersion(settings_version.split('+')[0]).version
        else:
            settings_V = StrictVersion('6.0.2').version
        addon_V = StrictVersion(addon_version.split('+')[0]).version

        if addon_V > settings_V:
            # New version found, save addon version to settings
            set_setting('version', addon_version)
            return True, settings_version, settings_V, addon_V

        return False, settings_version, settings_V, addon_V

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
            elif areaSelected == 'gensyn':
                self.current_area = 'gensyn'
                self.list_entries('/gensyn')
            elif areaSelected == 'ultra':
                self.current_area = 'ultra'
                self.list_entries('/ultra')
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
        # Gensyn
        item = xbmcgui.ListItem('Gensyn', offscreen=True)
        item.setArt({'fanart': str(resources_path/'media/gensyn.png'),
                     'icon': str(resources_path/'media/gensyn.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?area=5', item, True))

        xbmcplugin.addDirectoryItems(self._plugin_handle, items)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def showMainMenu(self):
        items = []

        # Live TV
        item = xbmcgui.ListItem(tr(30001), offscreen=True)
        item.setArt({'fanart': self.fanart_image, 'icon': str(resources_path/'icons/livetv.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=liveTV', item, True))

        if self.api._user_name != 'anonymous':
            # Mylist
            item = xbmcgui.ListItem(f'{tr(30004)} ({self.api._user_name})', offscreen=True)
            item.setArt({'fanart': self.fanart_image, 'icon': str(resources_path/'icons/star.png')})
            item.addContextMenuItems(self.menuItems, False)
            items.append((self._plugin_url + '?show=mylist', item, True))

            # Continue watching
            item = xbmcgui.ListItem(f'{tr(30003)} ({self.api._user_name})', offscreen=True)
            item.setArt({'fanart': self.fanart_image, 'icon': str(resources_path/'icons/star.png')})
            item.addContextMenuItems(self.menuItems, False)
            items.append((self._plugin_url + '?show=continue', item, True))

        for hitem in self.api.get_home():
            if hitem['path']:
                item = xbmcgui.ListItem(hitem['title'], offscreen=True)
                png = hitem.get('icon', 'star.png')
                item.setArt({'fanart': self.fanart_image, 'icon': str(resources_path/f'icons/{png}')})
                item.addContextMenuItems(self.menuItems, False)
                items.append((self._plugin_url + '?listVideos=' + hitem['path'], item, True))

        # Search videos
        item = xbmcgui.ListItem(tr(30002), offscreen=True)
        item.setArt({'fanart': self.fanart_image, 'icon': str(resources_path/'icons/search.png')})
        item.addContextMenuItems(self.menuItems, False)
        items.append((self._plugin_url + '?show=search', item, True))

        if bool_setting('enable.areaitem'):
            items.append((self._plugin_url + '?show=areaselector', self.area_item, True))

        xbmcplugin.addDirectoryItems(self._plugin_handle, items)
        xbmcplugin.endOfDirectory(self._plugin_handle)

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
        keyboard = xbmc.Keyboard('', tr(30002))
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
        isFolder = item['type'] not in ['program', 'episode']
        if item.get('path','').startswith('/kanal/') and item['type'] == 'link':
            isFolder = False
        if item['type'] in ['ImageEntry', 'TextEntry'] or item['title'] == '':
            return None
        if 'kodi_seasons' in item:
            is_season = item['kodi_seasons']

        title = self.api.get_title(item)
        listItem = xbmcgui.ListItem(title, offscreen=True)
        videoInfoTag = listItem.getVideoInfoTag()
        self.api.set_info(item, videoInfoTag, title)
        if 'images' in item:
            listItem.setArt({'thumb': item['images']['tile'],
                            'icon': item['images']['tile'],
                             'fanart': item['images']['wallpaper']
                             })
        else:
            icon_file = str(resources_path/'icons/star.png')
            if self.current_area == 'ultra':
                icon_file = str(resources_path/'icons/ultra.png')
            elif self.current_area == 'gensyn':
                icon_file = str(resources_path/'icons/gensyn.png')
            listItem.setArt({'fanart': self.fanart_image, 'icon': icon_file})

        log(f'{title} -- {item["id"]} | {item["type"]} | {item.get("path")}', level=2)
        if item.get('in_mylist', False):
            runScript = f"RunPlugin(plugin://plugin.video.drnu/?delfavorite={item['id']})"
            menuItems.append((tr(30010), runScript))
        elif item.get('ResumeTime', False):
            runScript = f"RunPlugin(plugin://plugin.video.drnu/?delwatched={item['id']})"
            menuItems.append((tr(30008), runScript))
        else:
            if item['type'] not in ['ListEntry', 'RecommendationEntry']:
                runScript = f"RunPlugin(plugin://plugin.video.drnu/?addfavorite={item['id']})"
                menuItems.append((tr(30009), runScript))

        if isFolder:
            if item.get('path', False):
                url = self._plugin_url + f"?listVideos={item['path']}&seasons={is_season}"
            elif 'list' in item:
                param = item['list'].get('parameter', 'NoParam')
                url = self._plugin_url + \
                    f"?listVideos=ID_{item['list']['id']}&list_param={param}&seasons={is_season}"
            else:
                return None
            listItem.setIsFolder(True)
        else:
            listItem.setIsFolder(False)
            kids = self.api.kids_item(item)
            url = self._plugin_url + f"?playVideo={item['id']}&kids={str(kids)}&idpath={item['path']}"
            listItem.setProperty('IsPlayable', 'true')

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
            video = self.api.get_stream(id)

        subs = {}
        for i, sub in enumerate(video['subtitles']):
            subs[sub['language']] = i
        kids_channel = kids_channel == 'True'

        if not video['url']:
            self.displayError(tr(30904))
            return

        listItem = xbmcgui.ListItem(path=video['url'], offscreen=True)

        if int(get_setting('inputstream')) == 0:
            is_helper = Helper('hls')
            if is_helper.check_inputstream():
                listItem.setProperty('inputstream', is_helper.inputstream_addon)
                listItem.setProperty('inputstream.adaptive.manifest_type', 'hls')

        local_subs_bool = bool_setting('enable.localsubtitles') or int(get_setting('inputstream')) == 1
        if local_subs_bool and video['srt_subtitles']:
            listItem.setSubtitles(video['srt_subtitles'])
        xbmcplugin.setResolvedUrl(self._plugin_handle, video['url'] is not None, listItem)
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
    def resfresh_ui(self, params=''):
        xbmc.executebuiltin(f'Container.Update({self._plugin_url + params})')

    def login(self):
        err = self.api.request_tokens()
        if self.api.user:
            if err:
                xbmcgui.Dialog().ok(tr(30306), tr(30307))
            else:
                xbmcgui.Dialog().ok(tr(30303), tr(30304) + f'"{self.api._user_name}"')
                self.resfresh_ui()
        else:
            if err:
                self.displayError(err)
            else:
                xbmcgui.Dialog().ok(tr(30303), tr(30305))
                self.resfresh_ui('?area=1')

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
                elif PARAMS['show'] == 'areaselector':
                    self.showAreaSelector()
                elif PARAMS['show'] == 'mylist':
                    self.listEpisodes(self.api.get_mylist())
                elif PARAMS['show'] == 'continue':
                    self.listEpisodes(self.api.get_continue())
                    
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
                    filter_kids = bool_setting('disable.kids')
                    if 'Ultra' in items['title']:
                        filter_kids = False
                    self.listEpisodes(self.api.unfold_list(items, filter_kids=filter_kids))
                else:
                    self.list_entries(PARAMS['listVideos'], seasons)

            elif 'playVideo' in PARAMS:
                self.playVideo(PARAMS['playVideo'], PARAMS['kids'], PARAMS['idpath'])

            elif 'addfavorite' in PARAMS:
                self.api.add_to_mylist(PARAMS['addfavorite'])
            elif 'delfavorite' in PARAMS:
                self.api.delete_from_mylist(PARAMS['delfavorite'])
                self.resfresh_ui('?show=mylist')
            elif 'delwatched' in PARAMS:
                self.api.delete_from_watched(PARAMS['delwatched'])
                self.resfresh_ui('?show=continue')

            elif 'loginnow' in PARAMS:
                self.login()

            elif 're-cache' in PARAMS:
                progress = xbmcgui.DialogProgress()
                progress.create("video.drnu")
                progress.update(0)
                self.api.recache_items(clear_expired=True, progress=progress)
                progress.update(100)
                progress.close()
                if PARAMS['re-cache'] == 2:
                    xbmc.executebuiltin('ActivateWindow(Home)')

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
                    self.current_area = 'ultra'
                    self.list_entries('/ultra')
                elif area == 5:
                    self.current_area = 'gensyn'
                    self.list_entries('/gensyn')

        except tvapi.ApiException as ex:
            self.displayError(str(ex))

        except IOError as ex:
            self.displayIOError(str(ex))

        except Exception as ex:
            stack = traceback.format_exc()
            heading = 'drnu addon crash'
            xbmcgui.Dialog().ok(heading, '\n'.join([tr(30906), tr(30907), str(stack)]))
            raise ex
