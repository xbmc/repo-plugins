# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys
import xbmc
import xbmcgui
import resources.lib.utils as utils
from resources.lib.downloader import Downloader
from resources.lib.traktapi import traktAPI
from resources.lib.plugin import Plugin
from resources.lib.player import Player


class Script(Plugin):
    def __init__(self):
        super(Script, self).__init__()
        self.home = xbmcgui.Window(10000)
        self.params = {}
        self.prefixpath = '{0}Path.'.format(self.prefixname)
        self.prefixlock = '{0}Locked'.format(self.prefixname)
        self.prefixcurrent = '{0}Current'.format(self.prefixpath)
        self.prefixposition = '{0}Position'.format(self.prefixname)
        self.position = self.home.getProperty(self.prefixposition)
        self.position = int(self.position) if self.position else 0
        self.prevent_del = True if self.home.getProperty(self.prefixlock) else False

    def get_params(self):
        for arg in sys.argv:
            if arg == 'script.py':
                pass
            elif '=' in arg:
                arg_split = arg.split('=', 1)
                if arg_split[0] and arg_split[1]:
                    key, value = arg_split
                    self.params.setdefault(key, value)
            else:
                self.params.setdefault(arg, True)

    def reset_props(self):
        self.home.clearProperty(self.prefixcurrent)
        self.home.clearProperty(self.prefixposition)
        self.home.clearProperty('{0}0'.format(self.prefixpath))
        self.home.clearProperty('{0}1'.format(self.prefixpath))

    def set_props(self, position=1, path=''):
        self.home.setProperty(self.prefixcurrent, path)
        self.home.setProperty('{0}{1}'.format(self.prefixpath, position), path)
        self.home.setProperty(self.prefixposition, str(position))

    def lock_path(self, condition):
        if condition:
            self.home.setProperty(self.prefixlock, 'True')
        else:
            self.unlock_path()

    def unlock_path(self):
        self.home.clearProperty(self.prefixlock)

    def call_window(self):
        if self.params.get('call_id'):
            xbmc.executebuiltin('Dialog.Close(12003)')
            xbmc.executebuiltin('ActivateWindow({0})'.format(self.params.get('call_id')))
        elif self.params.get('call_path'):
            xbmc.executebuiltin('Dialog.Close(12003)')
            xbmc.executebuiltin('ActivateWindow(videos, {0}, return)'.format(self.params.get('call_path')))
        elif self.params.get('call_update'):
            xbmc.executebuiltin('Dialog.Close(12003)')
            xbmc.executebuiltin('Container.Update({0})'.format(self.params.get('call_update')))
        elif self.params.get('call_player'):
            xbmc.executebuiltin('Dialog.Close(12003)')
            xbmc.executebuiltin('PlayMedia({0})'.format(self.params.get('call_player')))

    def update_players(self):
        players_url = self.addon.getSettingString('players_url')
        players_url = xbmcgui.Dialog().input('Enter URL to download players', defaultt=players_url)
        if not xbmcgui.Dialog().yesno('Download Players', 'Download players from URL?\n[B]{0}[/B]'.format(players_url)):
            return
        self.addon.setSettingString('players_url', players_url)
        downloader = Downloader(
            extract_to='special://profile/addon_data/plugin.video.themoviedb.helper/players',
            download_url=players_url)
        downloader.get_extracted_zip()

    def set_defaultplayer(self):
        player = Player()
        tmdbtype = self.params.get('set_defaultplayer')
        setting = 'default_player_episodes' if tmdbtype == 'tv' else 'default_player_{0}s'.format(tmdbtype)
        player.setup_players(tmdbtype=tmdbtype, clearsetting=True)
        idx = xbmcgui.Dialog().select(
            'Choose Default Player for {0}'.format(utils.type_convert(tmdbtype, 'plural')), player.itemlist)
        if idx == 0:
            self.addon.setSetting(setting, '')
        if idx > 0:
            selected = player.itemlist[idx].getLabel()
            self.addon.setSetting(setting, selected)

    def clear_defaultplayers(self):
        self.addon.setSetting('default_player_movies', '')
        self.addon.setSetting('default_player_episodes', '')

    def add_path(self):
        url = self.params.get('add_path', '')
        url = url.replace('info=play', 'info=details')
        url = url.replace('info=seasons', 'info=details')
        url = '{0}&{1}'.format(url, 'extended=True') if 'extended=True' not in url else url
        self.position = self.position + 1
        self.set_props(self.position, url)
        self.lock_path(self.params.get('prevent_del'))
        self.call_window()

    def add_query(self):
        with utils.busy_dialog():
            item = utils.dialog_select_item(self.params.get('add_query'))
            if not item:
                return
            tmdb_id = self.tmdb.get_tmdb_id(self.params.get('type'), query=item, selectdialog=True)
            if tmdb_id:
                self.position = self.position + 1
                add_paramstring = 'plugin://plugin.video.themoviedb.helper/?info=details&amp;type={0}&amp;tmdb_id={1}'.format(self.params.get('type'), tmdb_id)
                self.set_props(self.position, add_paramstring)
                self.lock_path(self.params.get('prevent_del'))
            else:
                utils.kodi_log('Unable to find TMDb ID!\nQuery: {0} Type: {1}'.format(self.params.get('add_query'), self.params.get('type')), 1)
                return
        self.call_window()

    def add_prop(self):
        item = utils.dialog_select_item(self.params.get('add_prop'))
        if not item:
            return
        prop_name = '{0}{1}'.format(self.prefixname, self.params.get('prop_id'))
        self.home.setProperty(prop_name, item)
        self.call_window()

    def del_path(self):
        if self.prevent_del:
            self.unlock_path()
        else:
            self.home.clearProperty('{0}{1}'.format(self.prefixpath, self.position))
            if self.position > 1:
                self.position = self.position - 1
                path = self.home.getProperty('{0}{1}'.format(self.prefixpath, self.position))
                self.set_props(self.position, path)
            else:
                self.reset_props()
        self.call_window()

    def router(self):
        if not self.params:
            """ If no params assume user wants to run plugin """
            # TODO: Maybe restart service here too?
            self.params = {'call_path': 'plugin://plugin.video.themoviedb.helper/'}
        if self.params.get('authenticate_trakt'):
            traktAPI(force=True)
        elif self.params.get('update_players'):
            self.update_players()
        elif self.params.get('set_defaultplayer'):
            self.set_defaultplayer()
        elif self.params.get('clear_defaultplayers'):
            self.clear_defaultplayers()
        elif self.params.get('add_path'):
            self.add_path()
        elif self.params.get('add_query') and self.params.get('type'):
            self.add_query()
        elif self.params.get('add_prop') and self.params.get('prop_id'):
            self.add_prop()
        elif self.params.get('del_path'):
            self.del_path()
        elif self.params.get('reset_path'):
            self.reset_props()
        else:
            self.call_window()
