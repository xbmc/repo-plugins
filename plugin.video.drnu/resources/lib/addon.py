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
import pickle
import traceback
import urllib.parse as urlparse
from pathlib import Path

import xbmc
import xbmcgui
import xbmcplugin
from xbmcvfs import translatePath

from resources.lib import gui, tvapi, tvgui
from resources.lib.cronjob import remove_cronjob
from resources.lib.iptvmanager import IPTVManager
from resources.lib.kodiutils import (
    bool_setting,
    get_addon,
    get_addon_info,
    get_setting,
    kodi_version_major,
    log,
    resources_path,
    set_setting,
    tr,
    version,
)
from resources.lib.subtitles import resolve_subtitle_action


def migrate_pre_7_1():
    """Enforce the 7.1 recache defaults and drop the deprecated cronxbmc job.

    Versions before 7.1 scheduled the re-cache through cronxbmc and had no
    'recache.time'/'recache.service'/'recache.service.idle' settings. On the
    upgrade to 7.1 that job must go, the new settings must start at their 7.1
    defaults (03:00, service on, idle gate on), and the two cronxbmc keys must
    be cleared so they don't linger in the addon settings.
    """
    remove_cronjob()
    set_setting('recache.time', '03:00')
    set_setting('recache.service', 'true')
    set_setting('recache.service.idle', 'true')
    for old_key in ('recache.cronjob', 'recache.cronexpression'):
        if get_setting(old_key):
            set_setting(old_key, '')


def _wait_for_playback(player, monitor):
    """Wait until the player confirms playback, or give up after 5 seconds.

    Uses Monitor.waitForAbort so Kodi shutdown interrupts the wait; returns
    once playback is confirmed, after a 1 second settle wait.
    """
    dt = 0.2
    waited = 0.0
    while not player.isPlaying():
        if monitor.waitForAbort(dt):
            # Kodi is shutting down
            return
        waited += dt
        if waited >= 5:
            # Still not playing after 5 seconds, giving up...
            return
    monitor.waitForAbort(1)  # wait 1 more second to make sure it has fully started


class DrDkTvAddon:
    def __init__(self, plugin_url, plugin_handle):
        self._plugin_url = plugin_url
        self._plugin_handle = plugin_handle

        self.cache_path = Path(translatePath(get_addon().getAddonInfo('profile')))
        self.cache_path.mkdir(parents=True, exist_ok=True)

        self.search_path = self.cache_path / 'search6.pickle'
        self.fanart_image = str(resources_path() / 'media' / 'fanart.jpg')

        self.api = tvapi.Api(self.cache_path, tr, get_setting, log)

        self.menuItems = []
        runScript = "RunAddon(plugin.video.drnu,?show=areaselector)"
        self.menuItems.append((tr(30205), runScript))

        self._version_change_fixes()

    def _version_change_fixes(self):
        first_run, settings_version, settings_V, addon_V = self._version_check()
        if first_run:
            if settings_V < version('7.1.0') <= addon_V:
                # upgrading from before 7.1: cronxbmc scheduling is gone and
                # the new recache settings must start at their 7.1 defaults
                migrate_pre_7_1()
            if settings_version == '' and kodi_version_major() <= 19:
                # kodi matrix subtitle handling https://github.com/xbmc/inputstream.adaptive/issues/1037
                set_setting('enable.localsubtitles', 'true')
            elif addon_V == version('6.2.0') and kodi_version_major() == 20:
                set_setting('enable.localsubtitles', 'false')

    def _version_check(self):
        # Get version from settings.xml
        settings_version = get_setting('version')

        # Get version from addon.xml
        addon_version = get_addon_info('version')

        # Compare versions (settings_version was not present in version 6.0.2 and older)
        settings_V = version(settings_version.split('+')[0]) if settings_version != '' else version('6.0.2')
        addon_V = version(addon_version.split('+')[0])

        if addon_V > settings_V:
            # New version found, save addon version to settings
            set_setting('version', addon_version)
            return True, settings_version, settings_V, addon_V

        return False, settings_version, settings_V, addon_V

    def showAreaSelector(self):
        if bool_setting('use.simpleareaitem'):
            self.showSimpleAreaSelector()
        else:
            gui = tvgui.AreaSelectorDialog(tr, resources_path())
            gui.doModal()
            areaSelected = gui.areaSelected
            del gui

            if areaSelected == 'none':
                pass
            else:
                self.showArea(areaSelected)

    def showArea(self, area):
        if area == 'none':
            self.showAreaSelector()
        elif area in ['drtv', 'ultra']:
            self.showMainMenu(area)
        elif area in ['minisjang', 'ramasjang']:
            if bool_setting('disable.kids.menu'):
                items = self.api.get_children_front_items(f'{area}')
                self.listEpisodes(items)
            else:
                self.showMainMenu(area)
        else:
            self.list_entries(f'/{area}')

    def showSimpleAreaSelector(self):
        xbmcplugin.addDirectoryItems(self._plugin_handle, gui.area_selector_items(self._plugin_url, self.menuItems))
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def showMainMenu(self, area):
        items = gui.main_menu_items(self._plugin_url, self.api, self.menuItems, self.fanart_image, area)
        xbmcplugin.addDirectoryItems(self._plugin_handle, items)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def getIptvLiveChannels(self):
        iptv_channels = []
        for api_channel in self.api.getLiveTV():

            lowername = api_channel['title'].lower().replace(' ', '')
            # DR renamed the fifth channel to 'TVA Live'; the setting keeps its
            # original id, so map the new title back to it
            if lowername == 'tvalive':
                lowername = 'drtv'
            if not bool_setting('iptv.channels.include.' + lowername):
                continue

            iptv_channel = {
                'name': api_channel['title'],
                'stream': self.api.get_channel_url(api_channel, bool_setting('enable.livetv_subtitles')),
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
                    'start': schedule['startDate'],
                    'stop': schedule['endDate'],
                    'title': schedule['item']['title'],
                    'description': schedule['item']['description'],
                    'image': schedule['item']['images']['tile'],
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
            url = self.api.get_channel_url(channel, bool_setting('enable.livetv_subtitles'))
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
        directoryItems = []
        if keyboard.isConfirmed():
            keyword = keyboard.getText()
            search_results = self.api.search(keyword)
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

        # always end the directory, also on cancel or zero results,
        # otherwise Kodi is left showing a busy spinner
        xbmcplugin.addDirectoryItems(self._plugin_handle, directoryItems)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def kodi_item(self, item, is_season=False):
        return gui.kodi_item(self._plugin_url, self.api, self.menuItems, self.fanart_image, item, is_season)

    def listEpisodes(self, items, addSortMethods=False, seasons=False):
        directoryItems = []
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

    def list_entries(self, path, caching=True, seasons=False):
        use_cache = tvapi.cache_path(path) and caching
        entries = self.api.get_programcard(path, use_cache=use_cache)['entries']
        if len(entries) == 0:
            # hack for get_programcard('/liste/306104') giving empty entries, but recommendations yields?!?
            id = int(path.split('/')[-1])
            self.listEpisodes(self.api.get_recommendations(id, use_cache=use_cache)['items'])
        elif len(entries) > 1:
            self.listEpisodes(entries)
        else:
            item = entries[0]
            if item['type'] == 'ItemEntry':
                if item['item']['type'] == 'season':
                    if seasons or item['item']['show']['availableSeasonCount'] == 1:
                        # we have shown the root of this series (or only one season anyhow)
                        self.listEpisodes(self.api.unfold_list(item['item']['episodes'], use_cache=use_cache), seasons=False)
                    elif self.api.kids_item(item['item']) and bool_setting('disable.kids.seasons'):
                        # let's not have seasons on children items
                        collect_episodes = []
                        for season_item in item['item']['show']['seasons']['items']:
                            if season_item['id'] == item['item']['episodes']['items'][0]['seasonId']:
                                collect_episodes += self.api.unfold_list(item['item']['episodes'], use_cache=use_cache)
                            else:
                                newitem = self.api.get_programcard(season_item['path'], use_cache=use_cache)['entries'][0]
                                collect_episodes += self.api.unfold_list(newitem['item']['episodes'], use_cache=use_cache)
                        self.listEpisodes(collect_episodes, seasons=False)
                    else:
                        # list only the season items of this series
                        self.listEpisodes(item['item']['show']['seasons']['items'], seasons=True)
                else:
                    raise tvapi.ApiException(f"{item['item']['type']} unknown")
            elif item['type'] == 'ListEntry':
                items = self.api.unfold_list(item['list'], use_cache=use_cache)
                self.listEpisodes(items)
            else:
                raise tvapi.ApiException(f"{item['type']} unknown")

    def playVideo(self, id, kids_channel, path):
        if path.startswith('/kanal'):
            # live stream
            video = self.api.get_livestream(path, with_subtitles=bool_setting('enable.livetv_subtitles'))
            video['srt_subtitles'] = {}
        else:
            video = self.api.get_stream(id)

        if video is None:
            # no StandardVideo stream available for this item
            self.displayError(tr(30904))
            xbmcplugin.setResolvedUrl(self._plugin_handle, False, xbmcgui.ListItem(offscreen=True))
            return

        subs = {}
        for i, sub in enumerate(video['subtitles']):
            subs[sub['language']] = i
        kids_channel = kids_channel == 'True'

        if not video['url']:
            self.displayError(tr(30904))
            return

        listItem = xbmcgui.ListItem(path=video['url'], offscreen=True)

        # inputstream.adaptive is an optional dependency: when it is not
        # installed (some platforms cannot ship it), forcing the property would
        # make playback fail, so degrade to Kodi's built-in player instead
        inputstream_setting = int(get_setting('inputstream'))
        if inputstream_setting == 0 and xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)'):
            listItem.setProperty('inputstream', 'inputstream.adaptive')
            if kodi_version_major() <= 20:
                listItem.setProperty('inputstream.adaptive.manifest_type', 'hls')

        local_subs_bool = bool_setting('enable.localsubtitles') or inputstream_setting == 1
        if local_subs_bool and video['srt_subtitles']:
            listItem.setSubtitles(list(video['srt_subtitles'].values()))
        xbmcplugin.setResolvedUrl(self._plugin_handle, video['url'] is not None, listItem)
        if len(subs) == 0:
            return

        player = xbmc.Player()
        _wait_for_playback(player, xbmc.Monitor())

        # Set subtitles according to setting wishes
        if player.isPlaying():
            settings = {
                'disable.kids.subtitles': bool_setting('disable.kids.subtitles'),
                'enable.subtitles': bool_setting('enable.subtitles'),
                'enable.localsubtitles': local_subs_bool,
                'inputstream': inputstream_setting,
            }
            action, value = resolve_subtitle_action(settings, subs, kids_channel, video['srt_subtitles'])
            if action == 'off':
                player.showSubtitles(False)
            elif action == 'stream':
                player.setSubtitleStream(value)
                player.showSubtitles(True)
            elif action == 'local':
                # 'value' is the SRT path selected by language
                player.setSubtitles(value)
                player.showSubtitles(True)

    def refresh_ui(self, params=''):
        xbmc.executebuiltin(f'Container.Update({self._plugin_url + params})')

    def login(self):
        self.api._refresh_settings()
        err = self.api.request_tokens()
        if self.api.user:
            if err:
                xbmcgui.Dialog().ok(tr(30306), tr(30307))
            else:
                xbmcgui.Dialog().ok(tr(30303), tr(30304) + f'"{self.api.user_name}"')
                self.refresh_ui()
        else:
            if err:
                self.displayError(err)
            else:
                xbmcgui.Dialog().ok(tr(30303), tr(30305))
                self.refresh_ui('?area=drtv')

    def displayError(self, message='n/a'):
        heading = 'API error'
        xbmcgui.Dialog().ok(heading, '\n'.join([tr(30900), tr(30901), message]))

    def displayIOError(self, message='n/a'):
        heading = 'I/O error'
        xbmcgui.Dialog().ok(heading, '\n'.join([tr(30902), tr(30903), message]))

    def route(self, query):
        try:
            PARAMS = dict(urlparse.parse_qsl(query[1:]))
            routes = {
                'show': self._route_show,
                'iptv': self._route_iptv,
                'searchresult': self._route_searchresult,
                'listVideos': self._route_listvideos,
                'playVideo': self._route_playvideo,
                'addfavorite': self._route_addfavorite,
                'delfavorite': self._route_delfavorite,
                'delwatched': self._route_delwatched,
                'loginnow': self._route_login,
                're-cache': self._route_recache,
            }
            for key, handler in routes.items():
                if key in PARAMS:
                    handler(PARAMS)
                    return
            areas = ['none', 'drtv', 'minisjang', 'ramasjang', 'ultra', 'gensyn']
            area = PARAMS.get('area', areas[int(get_setting('area'))])
            self.showArea(area)

        except tvapi.ApiException as ex:
            log(['API exception', query], level=1)
            self.displayError(str(ex))

        except OSError as ex:
            log(['IO exception', query], level=1)
            self.displayIOError(str(ex))

        except Exception as ex:
            log(['Exception', query], level=1)
            stack = traceback.format_exc()
            heading = 'drnu addon crash'
            xbmcgui.Dialog().ok(heading, '\n'.join([tr(30906), tr(30907), str(stack)]))
            raise ex

    def _route_show(self, params):
        routes = {
            'liveTV': self.showLiveTV,
            'search': self.search,
            'areaselector': self.showAreaSelector,
            'mylist': lambda: self.listEpisodes(self.api.get_mylist()),
            'continue': lambda: self.listEpisodes(self.api.get_continue()),
        }
        handler = routes.get(params['show'])
        if handler:
            handler()

    def _route_iptv(self, params):
        if params['iptv'] == 'channels':
            IPTVManager(int(params['port']), channels=self.getIptvLiveChannels()).send_channels()
        elif params['iptv'] == 'epg':
            IPTVManager(int(params['port']), epg=self.getIptvEpg()).send_epg()

    def _route_searchresult(self, params):
        with self.search_path.open('rb') as fh:
            search_results = pickle.load(fh)
        self.listEpisodes(self.api.unfold_list(search_results[params['searchresult']]))

    def _route_listvideos(self, params):
        seasons = params.get('seasons', 'False') == 'True'
        caching = params.get('nocache', '0') != '1'
        if params['listVideos'].startswith('ID_'):
            if caching is False:
                self.api.caching = False
            items = self.api.get_list(params['listVideos'], params['list_param'])
            if not items['items']:
                # the list and its recommendations were both empty; show an
                # empty directory instead of crashing on items[0]
                if caching is False:
                    self.api.caching = True
                self.listEpisodes([])
                return
            area = self.api.item_area(items['items'][0])
            filter_kids = False
            if area in ['drtv', 'gensyn']:
                filter_kids = bool_setting('disable.kids')
            items = self.api.unfold_list(items, filter_kids=filter_kids)
            if caching is False:
                self.api.caching = True
            self.listEpisodes(items)
        else:
            self.list_entries(params['listVideos'], caching=caching, seasons=seasons)

    def _route_playvideo(self, params):
        self.playVideo(params['playVideo'], params['kids'], params['idpath'])

    def _route_addfavorite(self, params):
        self.api.add_to_mylist(params['addfavorite'])

    def _route_delfavorite(self, params):
        self.api.delete_from_mylist(params['delfavorite'])
        self.refresh_ui('?show=mylist')

    def _route_delwatched(self, params):
        self.api.delete_from_watched(params['delwatched'])
        self.refresh_ui('?show=continue')

    def _route_login(self, params):
        self.login()

    def _route_recache(self, params):
        progress = xbmcgui.DialogProgress()
        progress.create('video.drnu')
        progress.update(0)
        self.api.recache_items(clear_expired=True, progress=progress)
        progress.update(100)
        progress.close()
        # legacy '?re-cache=2' (old cronxbmc job) and '?re-cache=1' now do
        # the same thing: just the crawl, no GUI side effects
