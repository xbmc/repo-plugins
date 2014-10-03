#!/usr/bin/env python
# encoding: UTF-8

import xbmcgui, xbmcplugin
from urllib import quote_plus as quote

class GUI(object):
    def __init__(self, addon_handle, base_url):
        self.addon_handle = addon_handle
        self.base_url = base_url

    def _addDir(self, name, action_key, action_value, iconimage, is_folder):
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
        self._addDir(name,
                     action_key,
                     action_value,
                     iconimage,
                     is_folder=True)

    def addItem(self, name, action_key, action_value,
                iconimage='DefaultMovies.png'):
        self._addDir(name,
                     action_key,
                     action_value,
                     iconimage,
                     is_folder=False)

    def infobox(self, title, message):
        xbmcgui.Dialog().ok(title, message)


