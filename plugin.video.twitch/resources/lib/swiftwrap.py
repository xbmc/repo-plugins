# -*- coding: utf-8 -*-
"""

    Super Classed xbmcswift2 Plugin() - Based on xbmcswift2 Plugin
    Super Classed xbmcswift2 ListItem() - Based on xbmcswift2 ListItem

    Original sources included at the end of this file,
        https://github.com/jbeluch/xbmcswift2/
        https://raw.githubusercontent.com/jbeluch/xbmcswift2/master/xbmcswift2/plugin.py
        https://raw.githubusercontent.com/jbeluch/xbmcswift2/master/xbmcswift2/listitem.py
    --------------------------------------------------------------------------------------

    Allows 'art': {} to be set in ListItem dicts - enables setting art via Listitem.setArt()
    Allows 'is_folder': True/False to be set in ListItem dicts - enables isPlayable == isFolder

    usage:
        from swiftwrap import Plugin
        PLUGIN = Plugin()

    Copyright (C) 2016 anxdpanic

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from xbmcswift2.plugin import Plugin as swiftPlugin
from xbmcswift2.listitem import ListItem as swiftListItem


class Plugin(swiftPlugin):
    def __init__(self, name=None, addon_id=None, filepath=None, info_type=None):
        super(Plugin, self).__init__(name, addon_id, filepath, info_type)

    def _listitemify(self, item):
        # use ListItem() instead of xbmcswift2.listitem ListItem()
        info_type = self.info_type if hasattr(self, 'info_type') else 'video'

        if not hasattr(item, 'as_tuple'):
            if 'info_type' not in item.keys():
                item['info_type'] = info_type
            item = ListItem.from_dict(**item)
        return item


class ListItem(swiftListItem):
    def __init__(self, label=None, label2=None, icon=None, thumbnail=None, path=None):
        super(ListItem, self).__init__(label, label2, icon, thumbnail, path)

    def set_art(self, art):
        """
        add Listitem.setArt()
        :param art: dictionary - pairs of { label: value }.
                    - Some default art values (any string possible):
                    - thumb : string - image filename
                    - poster : string - image filename
                    - banner : string - image filename
                    - fanart : string - image filename
                    - clearart : string - image filename
                    - clearlogo : string - image filename
                    - landscape : string - image filename
        """
        self._listitem.setArt(art)

    @classmethod
    def from_dict(cls, label=None, label2=None, icon=None, thumbnail=None,
                  path=None, selected=None, info=None, properties=None,
                  context_menu=None, replace_context_menu=False,
                  is_playable=None, info_type='video', stream_info=None, is_folder=None, art=None):
        # add is_folder parameter and set listitem.is_folder if/when appropriate
        # add art parameter and call set_art() if/when appropriate
        listitem = cls(label, label2, icon, thumbnail, path)

        if selected is not None:
            listitem.select(selected)

        if info:
            if ('mediatype' not in info) and (info_type == 'video'):
                info['mediatype'] = 'video'
            listitem.set_info(info_type, info)

        if is_playable:
            listitem.set_is_playable(True)

        if is_folder:
            listitem.is_folder = True

        if properties:
            if hasattr(properties, 'items'):
                properties = properties.items()
            for key, val in properties:
                listitem.set_property(key, val)

        if stream_info:
            for stream_type, stream_values in stream_info.items():
                listitem.add_stream_info(stream_type, stream_values)

        if context_menu:
            listitem.add_context_menu_items(context_menu, replace_context_menu)

        if art:
            listitem.set_art(art)

        return listitem

"""
'''
    xbmcswift2.plugin
    -----------------

    This module contains the Plugin class. This class handles all of the url
    routing and interaction with XBMC for a plugin.

    :copyright: (c) 2012 by Jonathan Beluch
    :license: GPLv3, see LICENSE for more details.
'''
import os
import sys
import pickle
import xbmcswift2
from urllib import urlencode
from functools import wraps
from optparse import OptionParser
try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs

from listitem import ListItem
from logger import log, setup_log
from common import enum
from common import clean_dict
from urls import UrlRule, NotFoundException, AmbiguousUrlException
from xbmcswift2 import (xbmc, xbmcgui, xbmcplugin, xbmcaddon, Request,)

from xbmcmixin import XBMCMixin
from common import Modes, DEBUG_MODES


class Plugin(XBMCMixin):
    '''The Plugin objects encapsulates all the properties and methods necessary
    for running an XBMC plugin. The plugin instance is a central place for
    registering view functions and keeping track of plugin state.

    Usually the plugin instance is created in the main addon.py file for the
    plugin. Typical creation looks like this::

        from xbmcswift2 import Plugin
        plugin = Plugin('Hello XBMC')


    .. versionchanged:: 0.2
        The *addon_id* and *filepath* parameters are now optional. They will
        now default to the correct values.

    :param name: The name of the plugin, e.g. 'Academic Earth'.

    :param addon_id: The XBMC addon ID for the plugin, e.g.
                     'plugin.video.academicearth'. This parameter is now
                     optional and is really only useful for testing purposes.
                     If it is not provided, the correct value will be parsed
                     from the addon.xml file.

    :param filepath: Optional parameter. If provided, it should be the path to
                     the addon.py file in the root of the addon directoy. This
                     only has an effect when xbmcswift2 is running on the
                     command line. Will default to the current working
                     directory since xbmcswift2 requires execution in the root
                     addon directoy anyway. The parameter still exists to ease
                     testing.
    '''

    def __init__(self, name=None, addon_id=None, filepath=None, info_type=None):
        self._name = name
        self._routes = []
        self._view_functions = {}

        # addon_id is no longer required as it can be parsed from addon.xml
        if addon_id:
            self._addon = xbmcaddon.Addon(id=addon_id)
        else:
            self._addon = xbmcaddon.Addon()

        self._addon_id = addon_id or self._addon.getAddonInfo('id')
        self._name = name or self._addon.getAddonInfo('name')

        self._info_type = info_type
        if not self._info_type:
            types = {
                'video': 'video',
                'audio': 'music',
                'image': 'pictures',
            }
            self._info_type = types.get(self._addon_id.split('.')[1], 'video')

        # Keeps track of the added list items
        self._current_items = []

        # Gets initialized when self.run() is called
        self._request = None

        # A flag to keep track of a call to xbmcplugin.endOfDirectory()
        self._end_of_directory = False

        # Keep track of the update_listing flag passed to
        # xbmcplugin.endOfDirectory()
        self._update_listing = False

        # The plugin's named logger
        self._log = setup_log(self._addon_id)

        # The path to the storage directory for the addon
        self._storage_path = xbmc.translatePath(
            'special://profile/addon_data/%s/.storage/' % self._addon_id)
        if not os.path.isdir(self._storage_path):
            os.makedirs(self._storage_path)

        # If we are runing in CLI, we need to load the strings.xml manually
        # Since xbmcswift2 currently relies on execution from an addon's root
        # directly, we can rely on cwd for now...
        if xbmcswift2.CLI_MODE:
            from xbmcswift2.mockxbmc import utils
            if filepath:
                addon_dir = os.path.dirname(filepath)
            else:
                addon_dir = os.getcwd()
            strings_fn = os.path.join(addon_dir, 'resources', 'language',
                                      'English', 'strings.xml')
            utils.load_addon_strings(self._addon, strings_fn)

    @property
    def info_type(self):
        return self._info_type

    @property
    def log(self):
        '''The log instance for the plugin. Returns an instance of the
        stdlib's ``logging.Logger``. This log will print to STDOUT when running
        in CLI mode and will forward messages to XBMC's log when running in
        XBMC. Some examples::

            plugin.log.debug('Debug message')
            plugin.log.warning('Warning message')
            plugin.log.error('Error message')
        '''
        return self._log

    @property
    def id(self):
        '''The id for the addon instance.'''
        return self._addon_id

    @property
    def storage_path(self):
        '''A full path to the storage folder for this plugin's addon data.'''
        return self._storage_path

    @property
    def addon(self):
        '''This plugin's wrapped instance of xbmcaddon.Addon.'''
        return self._addon

    @property
    def added_items(self):
        '''The list of currently added items.

        Even after repeated calls to :meth:`~xbmcswift2.Plugin.add_items`, this
        property will contain the complete list of added items.
        '''
        return self._current_items

    def clear_added_items(self):
        # TODO: This shouldn't be exposed probably...
        self._current_items = []

    @property
    def handle(self):
        '''The current plugin's handle. Equal to ``plugin.request.handle``.'''
        return self.request.handle

    @property
    def request(self):
        '''The current :class:`~xbmcswift2.Request`.

        Raises an Exception if the request hasn't been initialized yet via
        :meth:`~xbmcswift2.Plugin.run()`.
        '''
        if self._request is None:
            raise Exception('It seems the current request has not been '
                            'initialized yet. Please ensure that '
                            '`plugin.run()` has been called before attempting '
                            'to access the current request.')
        return self._request

    @property
    def name(self):
        '''The addon's name'''
        return self._name

    def _parse_request(self, url=None, handle=None):
        '''Handles setup of the plugin state, including request
        arguments, handle, mode.

        This method never needs to be called directly. For testing, see
        plugin.test()
        '''
        # To accomdate self.redirect, we need to be able to parse a full url as
        # well
        if url is None:
            url = sys.argv[0]
            if len(sys.argv) == 3:
                url += sys.argv[2]
        if handle is None:
            handle = sys.argv[1]
        return Request(url, handle)

    def register_module(self, module, url_prefix):
        '''Registers a module with a plugin. Requires a url_prefix that
        will then enable calls to url_for.

        :param module: Should be an instance `xbmcswift2.Module`.
        :param url_prefix: A url prefix to use for all module urls,
                           e.g. '/mymodule'
        '''
        module._plugin = self
        module._url_prefix = url_prefix
        for func in module._register_funcs:
            func(self, url_prefix)

    def cached_route(self, url_rule, name=None, options=None, TTL=None):
        '''A decorator to add a route to a view and also apply caching. The
        url_rule, name and options arguments are the same arguments for the
        route function. The TTL argument if given will passed along to the
        caching decorator.
        '''
        route_decorator = self.route(url_rule, name=name, options=options)
        if TTL:
            cache_decorator = self.cached(TTL)
        else:
            cache_decorator = self.cached()

        def new_decorator(func):
            return route_decorator(cache_decorator(func))
        return new_decorator

    def route(self, url_rule, name=None, options=None):
        '''A decorator to add a route to a view. name is used to
        differentiate when there are multiple routes for a given view.'''
        # TODO: change options kwarg to defaults
        def decorator(f):
            view_name = name or f.__name__
            self.add_url_rule(url_rule, f, name=view_name, options=options)
            return f
        return decorator

    def add_url_rule(self, url_rule, view_func, name, options=None):
        '''This method adds a URL rule for routing purposes. The
        provided name can be different from the view function name if
        desired. The provided name is what is used in url_for to build
        a URL.

        The route decorator provides the same functionality.
        '''
        rule = UrlRule(url_rule, view_func, name, options)
        if name in self._view_functions.keys():
            # TODO: Raise exception for ambiguous views during registration
            log.warning('Cannot add url rule "%s" with name "%s". There is '
                        'already a view with that name', url_rule, name)
            self._view_functions[name] = None
        else:
            log.debug('Adding url rule "%s" named "%s" pointing to function '
                      '"%s"', url_rule, name, view_func.__name__)
            self._view_functions[name] = rule
        self._routes.append(rule)

    def url_for(self, endpoint, **items):
        '''Returns a valid XBMC plugin URL for the given endpoint name.
        endpoint can be the literal name of a function, or it can
        correspond to the name keyword arguments passed to the route
        decorator.

        Raises AmbiguousUrlException if there is more than one possible
        view for the given endpoint name.
        '''
        try:
            rule = self._view_functions[endpoint]
        except KeyError:
            try:
                rule = (rule for rule in self._view_functions.values() if rule.view_func == endpoint).next()
            except StopIteration:
                raise NotFoundException(
                    '%s doesn\'t match any known patterns.' % endpoint)

        # rule can be None since values of None are allowed in the
        # _view_functions dict. This signifies more than one view function is
        # tied to the same name.
        if not rule:
            # TODO: Make this a regular exception
            raise AmbiguousUrlException

        pathqs = rule.make_path_qs(items)
        return 'plugin://%s%s' % (self._addon_id, pathqs)

    def _dispatch(self, path):
        for rule in self._routes:
            try:
                view_func, items = rule.match(path)
            except NotFoundException:
                continue
            log.info('Request for "%s" matches rule for function "%s"',
                     path, view_func.__name__)
            listitems = view_func(**items)

            # Only call self.finish() for UI container listing calls to plugin
            # (handle will be >= 0). Do not call self.finish() when called via
            # RunPlugin() (handle will be -1).
            if not self._end_of_directory and self.handle >= 0:
                if listitems is None:
                    self.finish(succeeded=False)
                else:
                    listitems = self.finish(listitems)

            return listitems
        raise NotFoundException, 'No matching view found for %s' % path

    def redirect(self, url):
        '''Used when you need to redirect to another view, and you only
        have the final plugin:// url.'''
        # TODO: Should we be overriding self.request with the new request?
        new_request = self._parse_request(url=url, handle=self.request.handle)
        log.debug('Redirecting %s to %s', self.request.path, new_request.path)
        return self._dispatch(new_request.path)

    def run(self, test=False):
        '''The main entry point for a plugin.'''
        self._request = self._parse_request()
        log.debug('Handling incoming request for %s', self.request.path)
        items = self._dispatch(self.request.path)

        # Close any open storages which will persist them to disk
        if hasattr(self, '_unsynced_storages'):
            for storage in self._unsynced_storages.values():
                log.debug('Saving a %s storage to disk at "%s"',
                          storage.file_format, storage.filename)
                storage.close()

        return items


'''
    xbmcswift2.listitem
    ------------------

    This module contains the ListItem class, which acts as a wrapper
    for xbmcgui.ListItem.

    :copyright: (c) 2012 by Jonathan Beluch
    :license: GPLv3, see LICENSE for more details.
'''
from xbmcswift2 import xbmcgui


class ListItem(object):
    '''A wrapper for the xbmcgui.ListItem class. The class keeps track
    of any set properties that xbmcgui doesn't expose getters for.
    '''
    def __init__(self, label=None, label2=None, icon=None, thumbnail=None,
                 path=None):
        '''Defaults are an emtpy string since xbmcgui.ListItem will not
        accept None.
        '''
        kwargs = {
            'label': label,
            'label2': label2,
            'iconImage': icon,
            'thumbnailImage': thumbnail,
            'path': path,
        }
        #kwargs = dict((key, val) for key, val in locals().items() if val is
        #not None and key != 'self')
        kwargs = dict((key, val) for key, val in kwargs.items()
                      if val is not None)
        self._listitem = xbmcgui.ListItem(**kwargs)

        # xbmc doesn't make getters available for these properties so we'll
        # keep track on our own
        self._icon = icon
        self._path = path
        self._thumbnail = thumbnail
        self._context_menu_items = []
        self.is_folder = True
        self._played = False

    def __repr__(self):
        return ("<ListItem '%s'>" % self.label).encode('utf-8')

    def __str__(self):
        return ('%s (%s)' % (self.label, self.path)).encode('utf-8')

    def get_context_menu_items(self):
        '''Returns the list of currently set context_menu items.'''
        return self._context_menu_items

    def add_context_menu_items(self, items, replace_items=False):
        '''Adds context menu items. If replace_items is True all
        previous context menu items will be removed.
        '''
        for label, action in items:
            assert isinstance(label, basestring)
            assert isinstance(action, basestring)
        if replace_items:
            self._context_menu_items = []
        self._context_menu_items.extend(items)
        self._listitem.addContextMenuItems(items, replace_items)

    def get_label(self):
        '''Sets the listitem's label'''
        return self._listitem.getLabel()

    def set_label(self, label):
        '''Returns the listitem's label'''
        return self._listitem.setLabel(label)

    label = property(get_label, set_label)

    def get_label2(self):
        '''Returns the listitem's label2'''
        return self._listitem.getLabel2()

    def set_label2(self, label):
        '''Sets the listitem's label2'''
        return self._listitem.setLabel2(label)

    label2 = property(get_label2, set_label2)

    def is_selected(self):
        '''Returns True if the listitem is selected.'''
        return self._listitem.isSelected()

    def select(self, selected_status=True):
        '''Sets the listitems selected status to the provided value.
        Defaults to True.
        '''
        return self._listitem.select(selected_status)

    selected = property(is_selected, select)

    def set_info(self, type, info_labels):
        '''Sets the listitems info'''
        return self._listitem.setInfo(type, info_labels)

    def get_property(self, key):
        '''Returns the property associated with the given key'''
        return self._listitem.getProperty(key)

    def set_property(self, key, value):
        '''Sets a property for the given key and value'''
        return self._listitem.setProperty(key, value)

    def add_stream_info(self, stream_type, stream_values):
        '''Adds stream details'''
        return self._listitem.addStreamInfo(stream_type, stream_values)

    def get_icon(self):
        '''Returns the listitem's icon image'''
        return self._icon

    def set_icon(self, icon):
        '''Sets the listitem's icon image'''
        self._icon = icon
        return self._listitem.setIconImage(icon)

    icon = property(get_icon, set_icon)

    def get_thumbnail(self):
        '''Returns the listitem's thumbnail image'''
        return self._thumbnail

    def set_thumbnail(self, thumbnail):
        '''Sets the listitem's thumbnail image'''
        self._thumbnail = thumbnail
        return self._listitem.setThumbnailImage(thumbnail)

    thumbnail = property(get_thumbnail, set_thumbnail)

    def get_path(self):
        '''Returns the listitem's path'''
        return self._path

    def set_path(self, path):
        '''Sets the listitem's path'''
        self._path = path
        return self._listitem.setPath(path)

    path = property(get_path, set_path)

    def get_is_playable(self):
        '''Returns True if the listitem is playable, False if it is a
        directory
        '''
        return not self.is_folder

    def set_is_playable(self, is_playable):
        '''Sets the listitem's playable flag'''
        value = 'false'
        if is_playable:
            value = 'true'
        self.set_property('isPlayable', value)
        self.is_folder = not is_playable

    playable = property(get_is_playable, set_is_playable)

    def set_played(self, was_played):
        '''Sets the played status of the listitem. Used to
        differentiate between a resolved video versus a playable item.
        Has no effect on XBMC, it is strictly used for xbmcswift2.
        '''
        self._played = was_played

    def get_played(self):
        '''Returns True if the video was played.'''
        return self._played

    def as_tuple(self):
        '''Returns a tuple of list item properties:
            (path, the wrapped xbmcgui.ListItem, is_folder)
        '''
        return self.path, self._listitem, self.is_folder

    def as_xbmc_listitem(self):
        '''Returns the wrapped xbmcgui.ListItem'''
        return self._listitem

    @classmethod
    def from_dict(cls, label=None, label2=None, icon=None, thumbnail=None,
                  path=None, selected=None, info=None, properties=None,
                  context_menu=None, replace_context_menu=False,
                  is_playable=None, info_type='video', stream_info=None):
        '''A ListItem constructor for setting a lot of properties not
        available in the regular __init__ method. Useful to collect all
        the properties in a dict and then use the **dct to call this
        method.
        '''
        listitem = cls(label, label2, icon, thumbnail, path)

        if selected is not None:
            listitem.select(selected)

        if info:
            listitem.set_info(info_type, info)

        if is_playable:
            listitem.set_is_playable(True)

        if properties:
            # Need to support existing tuples, but prefer to have a dict for
            # properties.
            if hasattr(properties, 'items'):
                properties = properties.items()
            for key, val in properties:
                listitem.set_property(key, val)

        if stream_info:
            for stream_type, stream_values in stream_info.items():
                listitem.add_stream_info(stream_type, stream_values)

        if context_menu:
            listitem.add_context_menu_items(context_menu, replace_context_menu)

        return listitem
"""
