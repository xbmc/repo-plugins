# -*- coding: utf-8 -*-
"""
The Kodi addons module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""
import os
import sys

# pylint: disable=import-error
import xbmc
import xbmcvfs
import xbmcgui
import xbmcaddon
import xbmcplugin
import resources.lib.mvutils as mvutils

try:
    # Python 3.x
    from urllib.parse import urlencode
    from urllib.parse import parse_qs
except ImportError:
    # Python 2.x
    from urllib import urlencode
    from urlparse import parse_qs

from resources.lib.kodi.kodilogger import KodiLogger


class KodiAddon(KodiLogger):
    """ The Kodi addon class """

    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.addon_id = self.addon.getAddonInfo('id')
        self.icon = self.addon.getAddonInfo('icon')
        self.fanart = self.addon.getAddonInfo('fanart')
        self.version = self.addon.getAddonInfo('version')
        self.path = mvutils.py2_decode(self.addon.getAddonInfo('path'))
        ##
        if self.getKodiVersion() > 18:
            self.datapath = mvutils.py2_decode(xbmcvfs.translatePath(self.addon.getAddonInfo('profile')))
        else:
            self.datapath = mvutils.py2_decode(xbmc.translatePath(self.addon.getAddonInfo('profile')))
        ##
        self.language = self.addon.getLocalizedString
        KodiLogger.__init__(self, self.addon_id, self.version)

    def getKodiVersion(self):
        """
        Get Kodi major version
        Returns:
            int: Kodi major version (e.g. 18)
        """
        xbmc_version = xbmc.getInfoLabel("System.BuildVersion")
        return int(xbmc_version.split('-')[0].split('.')[0])

    def get_addon_info(self, info_id):
        """
        Returns the value of an addon property as a string.

        Args:
            info_id(str): id of the property that the module needs to access.
        """
        argument = self.addon.getAddonInfo(info_id)
        argument = mvutils.py2_decode(argument)
        return argument

    def get_setting(self, setting_id):
        """
        Read a setting value

        Args:
            setting_id(int): id number of the setting
        """
        argument = self.addon.getSetting(setting_id)
        argument = mvutils.py2_decode(argument)
        return argument

    def set_setting(self, setting_id, value):
        """
        Write a setting value

        Args:
            setting_id(int): id number of the setting

            value(any): the value to write
        """
        return self.addon.setSetting(setting_id, value)

    def run_builtin(self, builtin):
        """
        Execute a builtin command

        Args:
            builtin(str): command to execute
        """
        self.debug('Execute builtin {}', builtin)
        xbmc.executebuiltin(builtin)

    def run_action(self, action):
        """
        Execute a specific action

        Args:
            action(str): action to execute
        """
        self.debug('Triggered action {}', action)
        xbmc.executebuiltin('Action({})'.format(action))


class KodiService(KodiAddon):
    """ The Kodi service addon class """

    def __init__(self):
        KodiAddon.__init__(self)


class KodiPlugin(KodiAddon):
    """ The Kodi plugin addon class """

    def __init__(self):
        KodiAddon.__init__(self)
        self.args = parse_qs(sys.argv[2][1:])
        self.base_url = sys.argv[0]
        self.addon_handle = int(sys.argv[1])

    def get_arg(self, argname, default):
        """
        Get one specific parameter passed to the plugin

        Args:
            argname(str): the name of the parameter

            default(str): the value to return if no such
                parameter was specified
        """
        try:
            argument = self.args[argname][0]
            argument = mvutils.py2_decode(argument)
            return argument
        except TypeError:
            return default
        except KeyError:
            return default

    def build_url(self, params):
        """
        Builds a valid plugin url passing the supplied
        parameters object

        Args:
            params(object): an object containing parameters
        """
        ### BUG in urlencode which is solved in python 3
        utfEnsuredParams = mvutils.dict_to_utf(params)
        return self.base_url + '?' + urlencode(utfEnsuredParams)

    def run_plugin(self, params):
        """
        Invoke the plugin with the specified parameters

        Args:
            params(object): an object containing parameters to
                pass to the plugin
        """
        xbmc.executebuiltin('RunPlugin({})'.format(self.build_url(params)))

    def set_resolved_url(self, succeeded, listitem):
        """
        Callback function to tell Kodi that the file plugin
        has been resolved to a url

        Args:
            succeeded(bool): If `True` the script completed successfully and
                a valid `listitem` with real URL is returned

            listitem(ListItem): item the file plugin resolved to for playback
        """
        xbmcplugin.setResolvedUrl(self.addon_handle, succeeded, listitem)

    def add_action_item(self, name, params, contextmenu=None, icon=None, thumb=None):
        """
        Adds an item to the directory that triggers a plugin action

        Args:
            name(str): String to show in the directory

            params(object): an object containing parameters to
                pass to the plugin

            contextmenu(array, optional): optional array of context
                menu items

            icon(str, optional): path to an optional icon

            thumb(str, optional): path to an optional thumbnail
        """
        self.add_directory_item(name, params, False, contextmenu, icon, thumb)

    def add_folder_item(self, name, params, contextmenu=None, icon=None, thumb=None):
        """
        Adds an item to the directory that opens a subdirectory

        Args:
            name(str): String to show in the directory

            params(object): an object containing parameters to
                pass to the plugin

            contextmenu(array, optional): optional array of context
                menu items

            icon(str, optional): path to an optional icon

            thumb(str, optional): path to an optional thumbnail
        """
        self.add_directory_item(name, params, True, contextmenu, icon, thumb)

    def add_directory_item(self, name, params, isfolder, contextmenu=None, icon=None, thumb=None):
        """
        Adds an item to the directory

        Args:
            name(str): String to show in the directory

            params(object): an object containing parameters to
                pass to the plugin

            isfolder(bool): if `True` the added item is a folder that
                opens a subsequent directory

            contextmenu(array, optional): optional array of context
                menu items

            icon(str, optional): path to an optional icon

            thumb(str, optional): path to an optional thumbnail
        """
        if isinstance(name, int):
            name = self.language(name)
        list_item = xbmcgui.ListItem(name)
        if contextmenu is not None:
            list_item.addContextMenuItems(contextmenu)
        if icon is not None or thumb is not None:
            if icon is None:
                icon = thumb
            if thumb is None:
                thumb = icon
            list_item.setArt({
                'thumb': icon,
                'icon': icon
            })
        xbmcplugin.addDirectoryItem(
            handle=self.addon_handle,
            url=self.build_url(params),
            listitem=list_item,
            isFolder=isfolder
        )

    def end_of_directory(self, succeeded=True, update_listing=False, cache_to_disc=True):
        """
        Callback function to tell Kodi that the end of the directory
        listing is reached.

        Args:
            succeeded(bool, optional): `True` if the script completed
                successfully. Default is `True`

            update_listing(bool, optional): `True` if this folder should
                update the current listing. Defaule is `False`

            cache_to_disc(bool, optional): If `True` folder will cache if
                extended time. Default is `True`
        """
        xbmcplugin.endOfDirectory(
            self.addon_handle,
            succeeded,
            update_listing,
            cache_to_disc
        )


class KodiInterlockedMonitor(xbmc.Monitor):
    """
    Kodi Monitor Class that gets notified about events
    and allows to work as a singleton

    Args:
        service(KodiService): The Kodi service instance

        setting_id(int): The setting id for storing the
            instance identification
    """

    def __init__(self, service, setting_id):
        super(KodiInterlockedMonitor, self).__init__()
        self.instance_id = ''.join(format(x, '02x')
                                   for x in bytearray(os.urandom(16)))
        self.setting_id = setting_id
        self.service = service

    def register_instance(self, waittime=1):
        """
        Tries to register an instance. If another
        instance (thread/process) is active, the method
        locks until the process is terminated or a
        timeout occurs

        Args:
            waittime(int, optional): Timeout for registering
                the instance. Default is 1 second
        """
        if self.bad_instance():
            self.service.info(
                'Found other instance with id {}', self.instance_id)
            self.service.info(
                'Startup delayed by {} second(s) waiting the other instance to shut down', waittime)
            self.service.set_setting(self.setting_id, self.instance_id)
            xbmc.Monitor.waitForAbort(self, waittime)
        else:
            self.service.set_setting(self.setting_id, self.instance_id)

    def unregister_instance(self):
        """ Unregisters the instance """
        self.service.set_setting(self.setting_id, '')

    def bad_instance(self):
        """
        Returns `True` if another instance is already registered
        """
        instance_id = self.service.get_setting(self.setting_id)
        return len(instance_id) > 0 and self.instance_id != instance_id

    def abort_requested(self):
        """
        Returns `True`if either this instance is not the registered
        instance or Kodi is shutting down
        """
        return self.bad_instance() or xbmc.Monitor.abortRequested(self)

    def wait_for_abort(self, timeout=None):
        """
        Waits until Kodi is shutting down or a specified timeout
        has occurred. Returns `True` if Kodi is shutting down.

        Args:
            timeout(int, optional): Number of seconds to wait.
                If not specified, the funtion waits forever.
        """
        if timeout is None:
            # infinite wait
            while not self.abort_requested():
                if xbmc.Monitor.waitForAbort(self, 1):
                    return True
            return True
        else:
            for _ in range(timeout):
                if self.bad_instance() or xbmc.Monitor.waitForAbort(self, 1):
                    return True
            return self.bad_instance()
