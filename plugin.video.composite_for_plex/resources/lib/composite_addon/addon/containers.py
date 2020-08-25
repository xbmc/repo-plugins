# -*- coding: utf-8 -*-
"""

    Copyright (C) 2019-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcgui  # pylint: disable=import-error


class Context:
    """
    Context values are set during creation, used to simplify passing objects to functions/methods
    """

    def __init__(self):
        self._params = None
        self._settings = None
        self._plex_network = None

    @property
    def params(self):
        if not self._params:
            raise ContextPropertyUnavailable
        return self._params

    @params.setter
    def params(self, value):
        """
        :param value: sys.argv[2] dict
        """
        self._params = value

    @property
    def settings(self):
        if not self._settings:
            raise ContextPropertyUnavailable
        return self._settings

    @settings.setter
    def settings(self, value):
        """
        :param value: resources/lib/composite_addon/addon/settings.AddonSettings()
        """
        self._settings = value

    @property
    def plex_network(self):
        if not self._plex_network:
            raise ContextPropertyUnavailable
        return self._plex_network

    @plex_network.setter
    def plex_network(self, value):
        """
        :param value: resources/lib/composite_addon/plex/plex.Plex()
        """
        self._plex_network = value


class GUIItem:
    """
    Used to simplify passing items to functions/methods
    """
    CONSTRUCTOR = xbmcgui.ListItem

    def __init__(self, url=None, info_labels=None, extra=None, menu=None):
        self._context_menu = menu
        self._extra = extra
        self._info_labels = info_labels
        self._is_folder = True
        self._url = url

    @property
    def context_menu(self):
        return self._context_menu

    @context_menu.setter
    def context_menu(self, value):
        """
        :param value:
        """
        self._context_menu = value

    @property
    def extra(self):
        if self._extra is None:
            raise ItemPropertyUnavailable
        return self._extra

    @extra.setter
    def extra(self, value):
        """
        :param value:
        """
        self._extra = value

    @property
    def info_labels(self):
        if self._info_labels is None:
            raise ItemPropertyUnavailable
        return self._info_labels

    @info_labels.setter
    def info_labels(self, value):
        """
        :param value:
        """
        self._info_labels = value

    @property
    def is_folder(self):
        return self._is_folder

    @is_folder.setter
    def is_folder(self, value):
        """
        :param value:
        """
        self._is_folder = value

    @property
    def url(self):
        if self._url is None:
            raise ItemPropertyUnavailable
        return self._url

    @url.setter
    def url(self, value):
        """
        :param value:
        """
        self._url = value


class Item:
    """
    Used to simplify passing items to functions/methods
    """

    def __init__(self, server=None, url=None, tree=None, data=None, up_next=True):
        self._data = data
        self._server = server
        self._tree = tree
        self._url = url
        self._up_next = up_next

    @property
    def data(self):
        if self._data is None:
            raise ItemPropertyUnavailable
        return self._data

    @data.setter
    def data(self, value):
        """
        :param value:
        """
        self._data = value

    @property
    def server(self):
        if not self._server:
            raise ItemPropertyUnavailable
        return self._server

    @server.setter
    def server(self, value):
        """
        :param value:
        """
        self._server = value

    @property
    def tree(self):
        if self._tree is None:
            raise ItemPropertyUnavailable
        return self._tree

    @tree.setter
    def tree(self, value):
        """
        :param value:
        """
        self._tree = value

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        """
        :param value:
        """
        self._url = value

    @property
    def up_next(self):
        return self._up_next

    @up_next.setter
    def up_next(self, value):
        """
        :param value:
        """
        self._up_next = bool(value)


class ItemPropertyUnavailable(Exception):
    pass


class ContextPropertyUnavailable(Exception):
    pass
