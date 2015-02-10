#!/usr/bin/env python
# encoding: UTF-8

import xbmcgui, xbmcplugin
from urllib import quote_plus as quote

class GUI(object):
    """
    A very simple class that wraps the interface functions in XBMC
    """
    def __init__(self, addon_handle, base_url):
        """
        .. py_function:: __init__(self, addon_handle, base_url)

        :param addon_handle: An identifier that XBMC uses to identify the addon
                             (created in default.py)
        :param base_url: The root internal url used in all calls in the addon
        """
        self.addon_handle = addon_handle
        self.base_url = base_url

    def _addDir(self, name, action_key, action_value, iconimage, is_folder):
        """
        .. py_function:: _addDir(self, name, action_key, action_value,
                            iconimage, is_folder)

        Creates a link in xbmc.

        :param name: Name of the link
        :param action_key: Name of the action to take when link selected
        :param action_value: Parameter to use with the action
        :param iconimage: Icon to use for the link
        :param is_folder: Does the link lead to a folder or playable item

        """
        formatparams = {
            "base_url": self.base_url,
            "key": quote(str(action_key)),
            "value": quote(str(action_value)),
            "name": quote(str(name))
        }

        url = "{base_url}?action_key={key}&action_value={value}&name={name}".format(**formatparams)

        listitem = xbmcgui.ListItem(name,
                                    iconImage=iconimage,
                                    thumbnailImage='')
        listitem.setInfo(type="Video", infoLabels={"Title": name})

        xbmcplugin.addDirectoryItem(
            handle=self.addon_handle,
            url=url,
            listitem=listitem,
            isFolder=is_folder)

    def addDir(self, name, action_key, action_value,
               iconimage='DefaultFolder.png'):
        """
        .. py_function:: addDir(self, name, action_key, action_value[,
               iconimage='DefaultFolder.png'])

        Create folder (wrapper function for _addDir).

        :param name: The name of the folder
        :param action_key: Action to take
        :param action_value: Parameter to action
        :iconimage: Image to use with the folder
        """
        self._addDir(name,
                     action_key,
                     action_value,
                     iconimage,
                     is_folder=True)

    def addItem(self, name, action_key, action_value,
                iconimage='DefaultMovies.png'):
        """
        .. py_function:: addItem(self, name, action_key, action_value,
                iconimage='DefaultMovies.png')

        Create link to playable item (wrapper function for _addDir).

        :param name: The name of the folder
        :param action_key: Action to take
        :param action_value: Parameter to action
        :iconimage: Image to use for the item
        """
        self._addDir(name,
                     action_key,
                     action_value,
                     iconimage,
                     is_folder=False)

    def infobox(self, title, message):
        """
        .. py_function:: infobox(self, title, message)

        Display a pop up message.

        :param title: The title of the pop up window
        :param message: Message you want to display to the user
        """
        xbmcgui.Dialog().ok(title, message)
