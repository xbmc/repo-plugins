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
import xbmcgui
import xbmcplugin
import xbmcvfs
import resources.lib.mvutils as mvutils
import resources.lib.appContext as appContext

try:
    # Python 3.x
    from urllib.parse import urlencode
    from urllib.parse import parse_qs
except ImportError:
    # Python 2.x
    from urllib import urlencode
    from urlparse import parse_qs


class KodiAddon(object):
    """ The Kodi addon class """

    def __init__(self):
        self.addon = appContext.ADDONCLASS
        self.addon_id = self.addon.getAddonInfo('id')
        self.icon = self.addon.getAddonInfo('icon')
        self.fanart = self.addon.getAddonInfo('fanart')
        self.version = self.addon.getAddonInfo('version')
        self.path = mvutils.py2_decode(self.addon.getAddonInfo('path'))
        #
        if self.getKodiVersion() > 18:
            self.datapath = mvutils.py2_decode(xbmcvfs.translatePath(self.addon.getAddonInfo('profile')))
        else:
            self.datapath = mvutils.py2_decode(xbmc.translatePath(self.addon.getAddonInfo('profile')))
        #
        self.language = self.addon.getLocalizedString
        self.kodiVersion = -1

    def getKodiVersion(self):
        """
        Get Kodi major version
        Returns:
            int: Kodi major version (e.g. 18)
        """
        xbmc_version = xbmc.getInfoLabel("System.BuildVersion")
        return int(xbmc_version.split('-')[0].split('.')[0])

    # TODO REMOVE THIS - USE SETTINGS INSTEAD
    def get_kodi_version(self):
        """
        Get Kodi major version
    
        Returns:
            int: Kodi major version (e.g. 18)
        """
        if self.kodiVersion > 0:
            return self.kodiVersion
        xbmc_version = xbmc.getInfoLabel("System.BuildVersion")
        self.kodiVersion = int(xbmc_version.split('-')[0].split('.')[0])
        return self.kodiVersion

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
        # self.logger.debug('Execute builtin {}', builtin)
        xbmc.executebuiltin(builtin)

    def getCaption(self, msgid):
        return self.language(msgid);

    def getSkinName(self):
        return xbmc.getSkinDir();

    def getCurrentViewId(self):
        window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        return window.getFocusId()

    def setViewId(self, viewId):
        if viewId > -1:
            # xbmc.sleep(1000)
            self.run_builtin('Container.SetViewMode({})'.format(viewId))
            self.run_builtin('Container.SetViewMode({})'.format(viewId))

    def resolveViewId(self, pViewname):
        skinName = self.getSkinName()
        viewId = -1
        # Kill switch
        self.logger.debug('static View Id {}', self.addon.getSetting('staticViewIds'))
        if self.addon.getSetting('staticViewIds') == False or self.addon.getSetting('staticViewIds') == 'false':
            return viewId

        if skinName == 'skin.estuary' and pViewname == 'MAIN':
            viewId = 55
        elif skinName == 'skin.estuary' and pViewname == 'SHOWS':
            viewId = 55
        elif skinName == 'skin.estuary' and pViewname == 'LIST':
            viewId = 55
        elif skinName == 'skin.estuary' and pViewname == 'THUMBNAIL':
            viewId = 500
        elif skinName == 'skin.estouchy' and pViewname == 'MAIN':
            viewId = 500
        elif skinName == 'skin.estouchy' and pViewname == 'SHOWS':
            viewId = 500
        elif skinName == 'skin.estouchy' and pViewname == 'LIST':
            viewId = 550
        elif skinName == 'skin.estouchy' and pViewname == 'THUMBNAIL':
            viewId = 55
        elif skinName == 'skin.confluence' and pViewname == 'MAIN':
            viewId = 51
        elif skinName == 'skin.confluence' and pViewname == 'SHOWS':
            viewId = 51
        elif skinName == 'skin.confluence' and pViewname == 'LIST':
            viewId = 504
        elif skinName == 'skin.confluence' and pViewname == 'THUMBNAIL':
            viewId = 500
        self.logger.debug('proposed view id {} for {} in mode {}', viewId, skinName, pViewname)
        return viewId;


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
        # BUG in urlencode which is solved in python 3
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
        #
        if self.get_kodi_version() > 17:
            list_item = xbmcgui.ListItem(label=name, offscreen=True)
        else:
            list_item = xbmcgui.ListItem(label=name)
        #
        if contextmenu is not None:
            list_item.addContextMenuItems(contextmenu)
        if icon is not None or thumb is not None:
            if icon is None:
                icon = thumb
            if thumb is None:
                thumb = icon
            list_item.setArt({
                'thumb': icon,
                'icon': icon,
                'banner': icon,
                'fanart': icon,
                'clearart': icon,
                'clearlogo': icon
            })
        xbmcplugin.addDirectoryItem(
            handle=self.addon_handle,
            url=self.build_url(params),
            listitem=list_item,
            isFolder=isfolder
        )

    def end_of_directory(self, succeeded=True, update_listing=False, cache_to_disc=False):
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

    def set_content(self, pContent=''):
        xbmcplugin.setContent(self.addon_handle, pContent)
