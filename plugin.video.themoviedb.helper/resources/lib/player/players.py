import re
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
from resources.lib.kodi.rpc import get_directory, KodiLibrary
from resources.lib.addon.window import get_property
from resources.lib.container.listitem import ListItem
from resources.lib.addon.plugin import ADDON, PLUGINPATH, ADDONPATH, format_folderpath, kodi_log
from resources.lib.addon.parser import try_int, try_float
from resources.lib.files.utils import read_file, normalise_filesize
from resources.lib.player.details import get_item_details, get_detailed_item, get_playerstring, get_language_details
from resources.lib.player.inputter import KeyboardInputter
from resources.lib.player.configure import get_players_from_file
from resources.lib.addon.constants import PLAYERS_PRIORITY
from resources.lib.addon.decorators import busy_dialog, ProgressDialog
from string import Formatter


def string_format_map(fmt, d):
    try:
        str.format_map
    except AttributeError:
        parts = Formatter().parse(fmt)
        return fmt.format(**{part[1]: d[part[1]] for part in parts})
    else:
        return fmt.format(**d)


def wait_for_player(to_start=None, timeout=5, poll=0.25, stop_after=0):
    xbmc_monitor, xbmc_player = xbmc.Monitor(), xbmc.Player()
    while (
            not xbmc_monitor.abortRequested()
            and timeout > 0
            and (
                (to_start and (not xbmc_player.isPlaying() or not xbmc_player.getPlayingFile().endswith(to_start)))
                or (not to_start and xbmc_player.isPlaying()))):
        xbmc_monitor.waitForAbort(poll)
        timeout -= poll

    # Wait to stop file
    if timeout > 0 and to_start and stop_after:
        xbmc_monitor.waitForAbort(stop_after)
        if xbmc_player.isPlaying() and xbmc_player.getPlayingFile().endswith(to_start):
            xbmc_player.stop()

    # Clean up
    del xbmc_monitor
    del xbmc_player
    return timeout


def resolve_to_dummy(handle=None, stop_after=1, delay_wait=0):
    """
    Kodi does 5x retries to resolve url if isPlayable property is set - strm files force this property.
    However, external plugins might not resolve directly to URL and instead might require PlayMedia.
    Also, if external plugin endpoint is a folder we need to do ActivateWindow/Container.Update instead.
    Passing False to setResolvedUrl doesn't work correctly and the retry is triggered anyway.
    In these instances we use a hack to avoid the retry by first resolving to a dummy file instead.
    """
    # If we don't have a handle there's nothing to resolve
    if handle is None:
        return

    # Set our dummy resolved url
    path = u'{}/resources/dummy.mp4'.format(ADDONPATH)
    kodi_log(['lib.player.players - attempt to resolve dummy file\n', path], 1)
    xbmcplugin.setResolvedUrl(handle, True, ListItem(path=path).get_listitem())

    # Wait till our file plays and then stop after setting duration
    if wait_for_player(to_start='dummy.mp4', stop_after=stop_after) <= 0:
        kodi_log(['lib.player.players - resolving dummy file timeout\n', path], 1)
        return -1

    # Wait for our file to stop before continuing
    if wait_for_player() <= 0:
        kodi_log(['lib.player.players - stopping dummy file timeout\n', path], 1)
        return -1

    # Added delay
    with busy_dialog(False if delay_wait < 1 else True):
        xbmc.Monitor().waitForAbort(delay_wait)

    # Success
    kodi_log(['lib.player.players -- successfully resolved dummy file\n', path], 1)


class Players(object):
    def __init__(self, tmdb_type, tmdb_id=None, season=None, episode=None, ignore_default=False, islocal=False, **kwargs):
        with ProgressDialog('TMDbHelper', u'{}...'.format(ADDON.getLocalizedString(32374)), total=3) as _p_dialog:
            self.api_language = None
            self.players = get_players_from_file()

            _p_dialog.update(u'{}...'.format(ADDON.getLocalizedString(32375)))
            self.details = get_item_details(tmdb_type, tmdb_id, season, episode)
            self.item = get_detailed_item(tmdb_type, tmdb_id, season, episode, details=self.details) or {}

            _p_dialog.update(u'{}...'.format(ADDON.getLocalizedString(32376)))
            self.playerstring = get_playerstring(tmdb_type, tmdb_id, season, episode, details=self.details)
            self.dialog_players = self._get_players_for_dialog(tmdb_type)

            self.default_player = ADDON.getSettingString('default_player_movies') if tmdb_type == 'movie' else ADDON.getSettingString('default_player_episodes')
            self.ignore_default = ignore_default
            self.tmdb_type, self.tmdb_id, self.season, self.episode = tmdb_type, tmdb_id, season, episode
            self.dummy_duration = try_float(ADDON.getSettingString('dummy_duration')) or 1.0
            self.dummy_delay = try_float(ADDON.getSettingString('dummy_delay')) or 1.0
            self.force_xbmcplayer = ADDON.getSettingBool('force_xbmcplayer')
            self.is_strm = islocal

    def _check_assert(self, keys=[]):
        if not self.item:
            return True  # No item so no need to assert values as we're only building to choose default player
        for i in keys:
            if i.startswith('!'):  # Inverted assert check for NOT value
                if self.item.get(i[1:]) and self.item.get(i[1:]) != 'None':
                    return False  # Key has a value so player fails assert check
            else:  # Standard assert check for value
                if not self.item.get(i) or self.item.get(i) == 'None':
                    return False  # Key didn't have a value so player fails assert check
        return True  # Player passed the assert check

    def _get_built_player(self, file, mode, value=None):
        value = value or self.players.get(file) or {}
        if mode in ['play_movie', 'play_episode']:
            name = ADDON.getLocalizedString(32061)
            is_folder = False
        else:
            name = xbmc.getLocalizedString(137)
            is_folder = True
        return {
            'file': file, 'mode': mode,
            'is_folder': is_folder,
            'is_resolvable': value.get('is_resolvable'),
            'api_language': value.get('api_language'),
            'language': value.get('language'),
            'name': u'{} {}'.format(name, value.get('name')),
            'plugin_name': value.get('plugin'),
            'plugin_icon': value.get('icon', '').format(ADDONPATH) or xbmcaddon.Addon(value.get('plugin', '')).getAddonInfo('icon'),
            'fallback': value.get('fallback', {}).get(mode),
            'actions': value.get(mode)}

    def _get_local_item(self, tmdb_type):
        file = self._get_local_movie() if tmdb_type == 'movie' else self._get_local_episode()
        if not file:
            return []
        return [{
            'name': u'{} Kodi'.format(ADDON.getLocalizedString(32061)),
            'is_folder': False,
            'is_local': True,
            'is_resolvable': "true",
            'plugin_name': 'xbmc.core',
            'plugin_icon': u'{}/resources/icons/other/kodi.png'.format(ADDONPATH),
            'actions': file}]

    def _get_local_file(self, file):
        if not file:
            return
        if file.endswith('.strm'):
            contents = read_file(file)
            if contents.startswith('plugin://plugin.video.themoviedb.helper'):
                return
            return contents
        return file

    def _get_local_movie(self):
        dbid = KodiLibrary(dbtype='movie').get_info(
            'dbid', fuzzy_match=False,
            tmdb_id=self.item.get('tmdb'),
            imdb_id=self.item.get('imdb'))
        if not dbid:
            return
        if self.details:  # Add dbid to details to update our local progress.
            self.details.infolabels['dbid'] = dbid
        return self._get_local_file(KodiLibrary(dbtype='movie').get_info('file', fuzzy_match=False, dbid=dbid))

    def _get_local_episode(self):
        dbid = KodiLibrary(dbtype='tvshow').get_info(
            'dbid', fuzzy_match=False,
            tmdb_id=self.item.get('tmdb'),
            tvdb_id=self.item.get('tvdb'),
            imdb_id=self.item.get('imdb'))
        return self._get_local_file(KodiLibrary(dbtype='episode', tvshowid=dbid).get_info(
            'file', season=self.item.get('season'), episode=self.item.get('episode')))

    def _get_players_for_dialog(self, tmdb_type):
        if tmdb_type not in ['movie', 'tv']:
            return []
        dialog_play = self._get_local_item(tmdb_type)
        dialog_search = []
        for k, v in sorted(self.players.items(), key=lambda i: try_int(i[1].get('priority')) or PLAYERS_PRIORITY):
            if v.get('disabled', '').lower() == 'true':
                continue  # Skip disabled players
            if tmdb_type == 'movie':
                if v.get('play_movie') and self._check_assert(v.get('assert', {}).get('play_movie', [])):
                    dialog_play.append(self._get_built_player(file=k, mode='play_movie', value=v))
                if v.get('search_movie') and self._check_assert(v.get('assert', {}).get('search_movie', [])):
                    dialog_search.append(self._get_built_player(file=k, mode='search_movie', value=v))
            else:
                if v.get('play_episode') and self._check_assert(v.get('assert', {}).get('play_episode', [])):
                    dialog_play.append(self._get_built_player(file=k, mode='play_episode', value=v))
                if v.get('search_episode') and self._check_assert(v.get('assert', {}).get('search_episode', [])):
                    dialog_search.append(self._get_built_player(file=k, mode='search_episode', value=v))
        return dialog_play + dialog_search

    def select_player(self, detailed=True, clear_player=False, header=ADDON.getLocalizedString(32042)):
        """ Returns user selected player via dialog - detailed bool switches dialog style """
        dialog_players = [] if not clear_player else [{
            'name': ADDON.getLocalizedString(32311),
            'plugin_name': 'plugin.video.themoviedb.helper',
            'plugin_icon': u'{}/resources/icons/other/kodi.png'.format(ADDONPATH)}]
        dialog_players += self.dialog_players
        players = [ListItem(
            label=i.get('name'),
            label2=u'{} v{}'.format(i.get('plugin_name'), xbmcaddon.Addon(i.get('plugin_name', '')).getAddonInfo('version')),
            art={'thumb': i.get('plugin_icon')}).get_listitem() for i in dialog_players]
        x = xbmcgui.Dialog().select(header, players, useDetails=detailed)
        if x == -1:
            return {}
        player = dialog_players[x]
        player['idx'] = x
        return player

    def _get_player_fallback(self, fallback):
        if not fallback:
            return
        file, mode = fallback.split()
        if not file or not mode:
            return
        player = self._get_built_player(file, mode)
        if not player:
            return
        for x, i in enumerate(self.dialog_players):
            if i == player:
                player['idx'] = x
                return player

    def _get_path_from_rules(self, folder, action):
        """ Returns tuple of (path, is_folder) """
        for x, f in enumerate(folder):
            for k, v in action.items():  # Iterate through our key (infolabel) / value (infolabel must match) pairs of our action
                if k == 'position':  # We're looking for an item position not an infolabel
                    if try_int(string_format_map(v, self.item)) != x + 1:  # Format our position value and add one since people are dumb and don't know that arrays start at 0
                        break  # Not the item position we want so let's go to next item in folder
                elif not f.get(k) or not re.match(string_format_map(v, self.item), u'{}'.format(f.get(k, ''))):  # Format our value and check if it regex matches the infolabel key
                    break  # Item's key value doesn't match value we are looking for so let's got to next item in folder
            else:  # Item matched our criteria so let's return it
                if f.get('file'):
                    is_folder = False if f.get('filetype') == 'file' else True  # Set false for files so we can play
                    return (f.get('file'), is_folder)   # Get ListItem.FolderPath for item and return as player

    def _player_dialog_select(self, folder, auto=False):
        d_items = []
        for f in folder:

            # Skip items without labels as probably not worth playing
            if not f.get('label') or f.get('label') == 'None':
                continue

            # Get the label of the item
            label_a = f.get('label')
            label_b_list = []

            # Add year to our label if exists and not special value of 1601
            if f.get('year') and f.get('year') != 1601:
                label_a = u'{} ({})'.format(label_a, f.get('year'))

            # Add season and episode numbers to label
            if try_int(f.get('season', 0)) > 0 and try_int(f.get('episode', 0)) > 0:
                if f.get('filetype') == 'file':  # If file assume is an episode so add to main label
                    label_a = u'{}x{}. {}'.format(f['season'], f['episode'], label_a)
                else:  # If folder assume is tvshow or season so add episode count to label2
                    label_b_list.append(u'{} {}'.format(f['episode'], xbmc.getLocalizedString(20360)))

            # Add various stream details to ListItem.Label2 (aka label_b)
            if f.get('streamdetails'):
                sdv_list = f.get('streamdetails', {}).get('video', [{}]) or [{}]
                sda_list = f.get('streamdetails', {}).get('audio', [{}]) or [{}]
                sdv, sda = sdv_list[0], sda_list[0]
                if sdv.get('width') or sdv.get('height'):
                    label_b_list.append(u'{}x{}'.format(sdv.get('width'), sdv.get('height')))
                if sdv.get('codec'):
                    label_b_list.append(u'{}'.format(sdv.get('codec', '').upper()))
                if sda.get('codec'):
                    label_b_list.append(u'{}'.format(sda.get('codec', '').upper()))
                if sda.get('channels'):
                    label_b_list.append(u'{} CH'.format(sda.get('channels', '')))
                for i in sda_list:
                    if i.get('language'):
                        label_b_list.append(u'{}'.format(i.get('language', '').upper()))
                if sdv.get('duration'):
                    label_b_list.append(u'{} mins'.format(try_int(sdv.get('duration', 0)) // 60))
            if f.get('size'):
                label_b_list.append(u'{}'.format(normalise_filesize(f.get('size', 0))))
            label_b = ' | '.join(label_b_list) if label_b_list else ''

            # Add item to select dialog list
            d_items.append(ListItem(label=label_a, label2=label_b, art={'thumb': f.get('thumbnail')}).get_listitem())

        if not d_items:
            return -1  # No items so ask user to select new player

        # If autoselect enabled and only 1 item choose that otherwise ask user to choose
        idx = 0 if auto and len(d_items) == 1 else xbmcgui.Dialog().select(ADDON.getLocalizedString(32236), d_items, useDetails=True)

        if idx == -1:
            return  # User exited the dialog so return nothing

        is_folder = False if folder[idx].get('filetype') == 'file' else True
        return (folder[idx].get('file'), is_folder)  # Return the player

    def _get_path_from_actions(self, actions, is_folder=True):
        """ Returns tuple of (path, is_folder) """
        is_dialog = None
        keyboard_input = None
        path = (actions[0], is_folder)
        if not is_folder:
            return path
        for action in actions[1:]:
            # Start thread with keyboard inputter if needed
            if action.get('keyboard'):
                if action['keyboard'] in ['Up', 'Down', 'Left', 'Right', 'Select']:
                    keyboard_input = KeyboardInputter(action="Input.{}".format(action.get('keyboard')))
                else:
                    text = string_format_map(action['keyboard'], self.item)
                    keyboard_input = KeyboardInputter(text=text[::-1] if action.get('direction') == 'rtl' else text)
                keyboard_input.setName('keyboard_input')
                keyboard_input.start()
                continue  # Go to next action

            # Get the next folder from the plugin
            folder = get_directory(string_format_map(path[0], self.item))

            # Kill our keyboard inputter thread
            if keyboard_input:
                keyboard_input.exit = True
                keyboard_input = None

            # Pop special actions
            is_return = action.pop('return', None)
            is_dialog = action.pop('dialog', None)

            # Get next path if there's still actions left
            next_path = self._get_path_from_rules(folder, action) if action else None

            # Special action to fallback to select dialog if match is not found directly
            if is_dialog and not next_path:
                next_path = self._player_dialog_select(folder, auto=is_dialog.lower() == 'auto')

            # Early return flag ignores a step failure and instead continues onto trying next step
            # Check against next_path[1] also to make sure we aren't trying to play a folder
            if is_return and (not next_path or next_path[1]):
                continue

            # No next path and no special flags means that player failed
            if not next_path:
                return

            # File is playable and user manually selected or early return flag set
            # Useful for early exit to play episodes in flattened miniseries instead of opening season folder
            if not next_path[1] and (is_dialog or is_return):
                return next_path

            # Set next path to path for next action
            path = next_path

        # If dialog repeat flag set then repeat action over until find playable or user cancels
        if path and is_dialog == 'repeat':
            return self._get_path_from_actions([path[0], {'dialog': 'repeat'}], path[1])

        return path

    def _get_path_from_player(self, player=None):
        """ Returns tuple of (path, is_folder) """
        if not player or not isinstance(player, dict):
            return
        actions = player.get('actions')
        if not actions:
            return
        if isinstance(actions, list):
            return self._get_path_from_actions(actions)
        if isinstance(actions, str):
            return (string_format_map(actions, self.item), player.get('is_folder', False))  # Single path so return it formatted

    def get_default_player(self):
        """ Returns default player """
        if self.ignore_default:
            return
        # Check local first if we have the setting
        if ADDON.getSettingBool('default_player_local') and self.dialog_players[0].get('is_local'):
            player = self.dialog_players[0]
            player['idx'] = 0
            return player
        if not self.default_player:
            return
        all_players = [u'{} {}'.format(i.get('file'), i.get('mode')) for i in self.dialog_players]
        try:
            x = all_players.index(self.default_player)
        except Exception:
            return
        player = self.dialog_players[x]
        player['idx'] = x
        return player

    def _get_resolved_path(self, player=None, allow_default=False):
        if not player and allow_default:
            player = self.get_default_player()

        # If we dont have a player from fallback then ask user to select one
        if not player:
            header = self.item.get('name') or ADDON.getLocalizedString(32042)
            if self.item.get('episode') and self.item.get('title'):
                header = u'{} - {}'.format(header, self.item['title'])
            player = self.select_player(header=header)
            if not player:
                return

        # Allow players to override language settings
        # Compare against self.api_language to check if another player changed language previously
        if player.get('api_language', None) != self.api_language:
            self.api_language = player.get('api_language', None)
            self.details = get_item_details(self.tmdb_type, self.tmdb_id, self.season, self.episode, language=self.api_language)
            self.item = get_detailed_item(self.tmdb_type, self.tmdb_id, self.season, self.episode, details=self.details) or {}

        # Allow for a separate translation language to add "{de_title}" keys ("de" is iso language code)
        if player.get('language'):
            self.item = get_language_details(
                self.item, self.tmdb_type, self.tmdb_id, self.season, self.episode,
                player['language'], self.item.get('year'))

        path = self._get_path_from_player(player)
        if not path:
            if player.get('idx') is not None:
                del self.dialog_players[player['idx']]  # Remove out player so we don't re-ask user for it
            fallback = self._get_player_fallback(player['fallback']) if player.get('fallback') else None
            return self._get_resolved_path(fallback)
        if path and isinstance(path, tuple):
            return {
                'url': path[0],
                'is_local': 'true' if player.get('is_local', False) else 'false',
                'is_folder': 'true' if path[1] else 'false',
                'isPlayable': 'false' if path[1] else 'true',
                'is_resolvable': player['is_resolvable'] if player.get('is_resolvable') else 'select',
                'player_name': player.get('name')}

    def get_resolved_path(self, return_listitem=True):
        if not self.item:
            return
        get_property('PlayerInfoString', clear_property=True)
        path = self._get_resolved_path(allow_default=True) or {}
        if return_listitem:
            self.details.params = {}
            self.details.path = path.pop('url', None)
            for k, v in path.items():
                self.details.infoproperties[k] = v
            path = self.details.get_listitem()
        return path

    def _update_listing_hack(self, folder_path=None, reset_focus=None):
        """
        Some plugins use container.update after search results to rewrite path history
        This is a quick hack to rewrite the path back to our original path before updating
        """
        if not folder_path:
            return
        xbmc.Monitor().waitForAbort(2)
        container_folderpath = xbmc.getInfoLabel("Container.FolderPath")
        if container_folderpath == folder_path:
            return
        xbmc.executebuiltin(u'Container.Update({},replace)'.format(folder_path))
        if not reset_focus:
            return
        timeout = 20
        while not xbmc.Monitor().abortRequested() and xbmc.getInfoLabel("Container.FolderPath") != folder_path and timeout > 0:
            xbmc.Monitor().waitForAbort(0.25)
            timeout -= 1
        xbmc.executebuiltin(reset_focus)
        xbmc.Monitor().waitForAbort(0.5)

    def configure_action(self, listitem, handle=None):
        path = listitem.getPath()
        if listitem.getProperty('is_folder') == 'true':
            return format_folderpath(path)
        if not handle or listitem.getProperty('is_resolvable') == 'false':
            return path
        if listitem.getProperty('is_resolvable') == 'select' and not xbmcgui.Dialog().yesno(
                '{} - {}'.format(listitem.getProperty('player_name'), ADDON.getLocalizedString(32353)),
                ADDON.getLocalizedString(32354),
                yeslabel=u"{} (setResolvedURL)".format(xbmc.getLocalizedString(107)),
                nolabel=u"{} (PlayMedia)".format(xbmc.getLocalizedString(106))):
            return path

    def play(self, folder_path=None, reset_focus=None, handle=None):
        # Get some info about current container for container update hack
        if not folder_path:
            folder_path = xbmc.getInfoLabel("Container.FolderPath")
        if not reset_focus and folder_path:
            containerid = xbmc.getInfoLabel("System.CurrentControlID")
            current_pos = xbmc.getInfoLabel("Container({}).CurrentItem".format(containerid))
            reset_focus = 'SetFocus({},{},absolute)'.format(containerid, try_int(current_pos) - 1)

        # Get the resolved path
        listitem = self.get_resolved_path()

        # Reset folder hack
        self._update_listing_hack(folder_path=folder_path, reset_focus=reset_focus)

        # Check we have an actual path to open
        if not listitem.getPath() or listitem.getPath() == PLUGINPATH:
            return

        action = self.configure_action(listitem, handle)

        # Kodi launches busy dialog on home screen that needs to be told to close
        # Otherwise the busy dialog will prevent window activation for folder path
        xbmc.executebuiltin('Dialog.Close(busydialog)')

        # If a folder we need to resolve to dummy and then open folder
        if listitem.getProperty('is_folder') == 'true':
            if self.is_strm or not ADDON.getSettingBool('only_resolve_strm'):
                resolve_to_dummy(handle, self.dummy_duration, self.dummy_delay)
            xbmc.executebuiltin(action)
            kodi_log(['lib.player - finished executing action\n', action], 1)
            return

        # Set our playerstring for player monitor to update kodi watched status
        if self.playerstring:
            get_property('PlayerInfoString', set_property=self.playerstring)

        # If PlayMedia method chosen re-route to Player() unless expert settings on
        if action:
            if self.is_strm or not ADDON.getSettingBool('only_resolve_strm'):
                resolve_to_dummy(handle, self.dummy_duration, self.dummy_delay)  # If we're calling external we need to resolve to dummy
            xbmc.Player().play(action, listitem) if self.force_xbmcplayer else xbmc.executebuiltin(u'PlayMedia({})'.format(action))
            kodi_log([
                'lib.player - playing path with {}\n'.format('xbmc.Player()' if self.force_xbmcplayer else 'PlayMedia'),
                listitem.getPath()], 1)
            return

        # Otherwise we have a url we can resolve to
        xbmcplugin.setResolvedUrl(handle, True, listitem)
        kodi_log(['lib.player - finished resolving path to url\n', listitem.getPath()], 1)

        # Re-send local files to player due to "bug" (or maybe "feature") of setResolvedUrl
        # Because setResolvedURL doesn't set id/type (sets None, "unknown" instead) to player for plugins
        # If id/type not set to Player.GetItem things like Trakt don't work correctly.
        # Looking for better solution than this hack.
        if ADDON.getSettingBool('trakt_localhack') and listitem.getProperty('is_local') == 'true':
            xbmc.Player().play(listitem.getPath(), listitem) if self.force_xbmcplayer else xbmc.executebuiltin(u'PlayMedia({})'.format(listitem.getPath()))
            kodi_log([
                'Finished executing {}\n'.format('xbmc.Player()' if self.force_xbmcplayer else 'PlayMedia'),
                listitem.getPath()], 1)
