# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys
import xbmc
import xbmcgui
import xbmcaddon
import resources.lib.utils as utils
from resources.lib.globals import LANGUAGES, APPEND_TO_RESPONSE
from resources.lib.tmdb import TMDb
from resources.lib.traktapi import traktAPI
_homewindow = xbmcgui.Window(10000)
_prefixname = 'TMDbHelper.'
_addon = xbmcaddon.Addon()
_addonname = 'plugin.video.themoviedb.helper'
_languagesetting = _addon.getSettingInt('language')
_language = LANGUAGES[_languagesetting]
_cache_long = _addon.getSettingInt('cache_details_days')
_cache_short = _addon.getSettingInt('cache_list_days')
_tmdb_apikey = _addon.getSetting('tmdb_apikey')
_tmdb = TMDb(api_key=_tmdb_apikey, language=_language, cache_long=_cache_long, cache_short=_cache_short,
             append_to_response=APPEND_TO_RESPONSE, addon_name=_addonname)


class Script:
    def __init__(self):
        self.params = {}
        self.prefixpath = '{0}Path.'.format(_prefixname)
        self.prefixlock = '{0}Locked'.format(_prefixname)
        self.prefixcurrent = '{0}Current'.format(self.prefixpath)
        self.prefixposition = '{0}Position'.format(_prefixname)
        self.position = _homewindow.getProperty(self.prefixposition)
        self.position = int(self.position) if self.position else 0
        self.prevent_del = _homewindow.getProperty(self.prefixlock)
        self.prevent_del = True if self.prevent_del else False

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
        _homewindow.clearProperty(self.prefixcurrent)
        _homewindow.clearProperty(self.prefixposition)
        _homewindow.clearProperty('{0}0'.format(self.prefixpath))
        _homewindow.clearProperty('{0}1'.format(self.prefixpath))

    def set_props(self, position=1, path=''):
        _homewindow.setProperty(self.prefixcurrent, path)
        _homewindow.setProperty('{0}{1}'.format(self.prefixpath, position), path)
        _homewindow.setProperty(self.prefixposition, str(position))

    def lock_path(self, condition):
        if condition:
            _homewindow.setProperty(self.prefixlock, 'True')
        else:
            self.unlock_path()

    def unlock_path(self):
        _homewindow.clearProperty(self.prefixlock)

    def call_window(self):
        if self.params.get('call_id'):
            xbmc.executebuiltin('Dialog.Close(12003)')
            xbmc.executebuiltin('ActivateWindow({0})'.format(self.params.get('call_id')))
        elif self.params.get('call_path'):
            xbmc.executebuiltin('Dialog.Close(12003)')
            xbmc.executebuiltin('ActivateWindow(videos, {0}, return)'.format(self.params.get('call_path')))

    def router(self):
        if self.params:
            if self.params.get('authenticate_trakt'):
                traktAPI(force=True)
            elif self.params.get('add_path'):
                self.position = self.position + 1
                self.set_props(self.position, self.params.get('add_path'))
                self.lock_path(self.params.get('prevent_del'))
            elif self.params.get('add_query') and self.params.get('type'):
                with utils.busy_dialog():
                    item = utils.dialog_select_item(self.params.get('add_query'))
                    if not item:
                        return
                    tmdb_id = _tmdb.get_tmdb_id(self.params.get('type'), query=item, selectdialog=True)
                    if tmdb_id:
                        self.position = self.position + 1
                        add_paramstring = 'plugin://plugin.video.themoviedb.helper/?info=details&amp;type={0}&amp;tmdb_id={1}'.format(self.params.get('type'), tmdb_id)
                        self.set_props(self.position, add_paramstring)
                        self.lock_path(self.params.get('prevent_del'))
                    else:
                        utils.kodi_log('Unable to find TMDb ID!\nQuery: {0} Type: {1}'.format(self.params.get('add_query'), self.params.get('type')), 1)
                        return
            elif self.params.get('add_prop') and self.params.get('prop_id'):
                item = utils.dialog_select_item(self.params.get('add_prop'))
                if not item:
                    return
                prop_name = '{0}{1}'.format(_prefixname, self.params.get('prop_id'))
                _homewindow.setProperty(prop_name, item)
            elif self.params.get('del_path'):
                if self.prevent_del:
                    self.unlock_path()
                else:
                    _homewindow.clearProperty('{0}{1}'.format(self.prefixpath, self.position))
                    if self.position > 1:
                        self.position = self.position - 1
                        path = _homewindow.getProperty('{0}{1}'.format(self.prefixpath, self.position))
                        self.set_props(self.position, path)
                    else:
                        self.reset_props()
            elif self.params.get('reset_path'):
                self.reset_props()
            self.call_window()


if __name__ == '__main__':
    TMDbScript = Script()
    TMDbScript.get_params()
    TMDbScript.router()
