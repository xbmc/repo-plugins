# -*- coding: utf-8 -*-
# Created on: 03.06.2015
"""
SimplePlugin micro-framework for Kodi content plugins

**Author**: Roman Miroshnychenko aka Roman V.M.

**License**: `GPL v.3 <https://www.gnu.org/copyleft/gpl.html>`_
"""

import os
import sys
import re
import inspect
from datetime import datetime, timedelta
import cPickle as pickle
from urlparse import parse_qs
from urllib import urlencode
from functools import wraps
from collections import MutableMapping, namedtuple
from copy import deepcopy
from types import GeneratorType
from hashlib import md5
from shutil import move
from contextlib import contextmanager
from pprint import pformat
import xbmcaddon
import xbmc
import xbmcplugin
import xbmcgui

__all__ = ['SimplePluginError', 'Storage', 'MemStorage',
           'Addon', 'Plugin', 'Params', 'debug_exception']

ListContext = namedtuple('ListContext', ['listing', 'succeeded',
                                         'update_listing', 'cache_to_disk',
                                         'sort_methods', 'view_mode',
                                         'content', 'category'])
PlayContext = namedtuple('PlayContext', ['path', 'play_item', 'succeeded'])


class SimplePluginError(Exception):
    """Custom exception"""
    pass


def _format_vars(variables):
    """
    Format variables dictionary

    :param variables: variables dict
    :type variables: dict
    :return: formatted string with sorted ``var = val`` pairs
    :rtype: str
    """
    var_list = [(var, val) for var, val in variables.iteritems()]
    lines = []
    for var, val in sorted(var_list, key=lambda i: i[0]):
        if not (var.startswith('__') or var.endswith('__')):
            lines.append('{0} = {1}'.format(var, pformat(val)))
    return '\n'.join(lines)


@contextmanager
def debug_exception(logger=None):
    """
    Diagnostic helper context manager

    It controls execution within its context and writes extended
    diagnostic info to the Kodi log if an unhandled exception
    happens within the context. The info includes the following items:

    - Module path.
    - Code fragment where the exception has happened.
    - Global variables.
    - Local variables.

    After logging the diagnostic info the exception is re-raised.

    Example::

        with debug_exception():
            # Some risky code
            raise RuntimeError('Fatal error!')

    :param logger: logger function which must accept a single argument
        which is a log message. By default it is :func:`xbmc.log`
        with ``ERROR`` level.
    """
    try:
        yield
    except:
        if logger is None:
            logger = lambda msg: xbmc.log(msg, xbmc.LOGERROR)
        logger('Unhandled exception detected!')
        logger('*** Start diagnostic info ***')
        frame_info = inspect.trace(5)[-1]
        logger('File: {0}'.format(frame_info[1]))
        context = ''
        for i, line in enumerate(frame_info[4], frame_info[2] - frame_info[5]):
            if i == frame_info[2]:
                context += '{0}:>{1}'.format(str(i).rjust(5), line)
            else:
                context += '{0}: {1}'.format(str(i).rjust(5), line)
        logger('Code context:\n' + context)
        logger('Global variables:\n' + _format_vars(frame_info[0].f_globals))
        logger('Local variables:\n' + _format_vars(frame_info[0].f_locals))
        logger('**** End diagnostic info ****')
        raise


class Params(dict):
    """
    Params(**kwargs)

    A class that stores parsed plugin call parameters

    Parameters can be accessed both through :class:`dict` keys and
    instance properties.

    .. note:: For a missing parameter an instance property returns ``None``.

    Example:

    .. code-block:: python

        @plugin.action('foo')
        def action(params):
            foo = params['foo']  # Access by key
            bar = params.bar  # Access through property. Both variants are equal
    """
    def __getattr__(self, key):
        return self.get(key)

    def __str__(self):
        return '<Params {0}>'.format(super(Params, self).__repr__())

    def __repr__(self):
        return '<simpleplugin.Params object {0}>'.format(super(Params, self).__repr__())


class Storage(MutableMapping):
    """
    Storage(storage_dir, filename='storage.pcl')

    Persistent storage for arbitrary data with a dictionary-like interface

    It is designed as a context manager and better be used
    with 'with' statement.

    :param storage_dir: directory for storage
    :type storage_dir: str
    :param filename: the name of a storage file (optional)
    :type filename: str

    Usage::

        with Storage('/foo/bar/storage/') as storage:
            storage['key1'] = value1
            value2 = storage['key2']

    .. note:: After exiting :keyword:`with` block a :class:`Storage` instance is invalidated.
        Storage contents are saved to disk only for a new storage or if the contents have been changed.
    """
    def __init__(self, storage_dir, filename='storage.pcl'):
        """
        Class constructor
        """
        self._storage = {}
        self._hash = None
        self._filename = os.path.join(storage_dir, filename)
        try:
            with open(self._filename, 'rb') as fo:
                contents = fo.read()
            self._storage = pickle.loads(contents)
            self._hash = md5(contents).hexdigest()
        except (IOError, pickle.PickleError, EOFError):
            pass

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.flush()

    def __getitem__(self, key):
        return self._storage[key]

    def __setitem__(self, key, value):
        self._storage[key] = value

    def __delitem__(self, key):
        del self._storage[key]

    def __iter__(self):
        return iter(self._storage)

    def __len__(self):
        return len(self._storage)

    def __str__(self):
        return '<Storage {0}>'.format(self._storage)

    def __repr__(self):
        return '<simpleplugin.Storage object {0}>'.format(self._storage)

    def flush(self):
        """
        Save storage contents to disk

        This method saves new and changed :class:`Storage` contents to disk
        and invalidates the Storage instance. Unchanged Storage is not saved
        but simply invalidated.
        """
        contents = pickle.dumps(self._storage)
        if self._hash is None or md5(contents).hexdigest() != self._hash:
            tmp = self._filename + '.tmp'
            try:
                with open(tmp, 'wb') as fo:
                    fo.write(contents)
            except:
                os.remove(tmp)
                raise
            move(tmp, self._filename)  # Atomic save
        del self._storage

    def copy(self):
        """
        Make a copy of storage contents

        .. note:: this method performs a *deep* copy operation.

        :return: a copy of storage contents
        :rtype: dict
        """
        return deepcopy(self._storage)


class MemStorage(MutableMapping):
    """
    MemStorage(storage_id)

    In-memory storage with dict-like interface

    The data is stored in the Kodi core so contents of a MemStorage instance
    with the same ID can be shared between different Python processes.

    .. note:: Keys are case-insensitive

    .. warning:: :class:`MemStorage` does not allow to modify mutable objects
        in place! You need to assign them to variables first, modify and
        store them back to a MemStorage instance.

    Example:

    .. code-block:: python

        storage = MemStorage('foo')
        some_list = storage['bar']
        some_list.append('spam')
        storage['bar'] = some_list

    :param storage_id: ID of this storage instance
    :type storage_id: str
    :param window_id: the ID of a Kodi Window object where storage contents
        will be stored.
    :type window_id: int
    """
    def __init__(self, storage_id, window_id=10000):
        self._id = storage_id
        self._window = xbmcgui.Window(window_id)
        try:
            self['__keys__']
        except KeyError:
            self['__keys__'] = []

    def _check_key(self, key):
        if not isinstance(key, str):
            raise TypeError('Storage key must be of str type!')

    def _format_contents(self):
        lines = []
        for key, val in self.iteritems():
            lines.append('{0}: {1}'.format(repr(key), repr(val)))
        return ', '.join(lines)

    def __str__(self):
        return '<MemStorage {{{0}}}>'.format(self._format_contents())

    def __repr__(self):
        return '<simpleplugin.MemStorage object {{{0}}}'.format(self._format_contents())

    def __getitem__(self, key):
        self._check_key(key)
        full_key = '{0}__{1}'.format(self._id, key)
        raw_item = self._window.getProperty(full_key)
        if raw_item:
            return pickle.loads(raw_item)
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        self._check_key(key)
        full_key = '{0}__{1}'.format(self._id, key)
        self._window.setProperty(full_key, pickle.dumps(value))
        if key != '__keys__':
            keys = self['__keys__']
            keys.append(key)
            self['__keys__'] = keys

    def __delitem__(self, key):
        self._check_key(key)
        full_key = '{0}__{1}'.format(self._id, key)
        item = self._window.getProperty(full_key)
        if item:
            self._window.clearProperty(full_key)
            if key != '__keys__':
                keys = self['__keys__']
                keys.remove(key)
                self['__keys__'] = keys
        else:
            raise KeyError(key)

    def __contains__(self, key):
        self._check_key(key)
        full_key = '{0}__{1}'.format(self._id, key)
        item = self._window.getProperty(full_key)
        if item:
            return True
        return False

    def __iter__(self):
        return iter(self['__keys__'])

    def __len__(self):
        return len(self['__keys__'])


class Addon(object):
    """
    Base addon class

    Provides access to basic addon parameters

    :param id_: addon id, e.g. 'plugin.video.foo' (optional)
    :type id_: str
    """
    def __init__(self, id_=''):
        """
        Class constructor
        """
        self._addon = xbmcaddon.Addon(id_)
        self._configdir = xbmc.translatePath(self._addon.getAddonInfo('profile')).decode('utf-8')
        self._ui_strings_map = None
        if not os.path.exists(self._configdir):
            os.mkdir(self._configdir)

    def __getattr__(self, item):
        """
        Get addon setting as an Addon instance attribute

        E.g. addon.my_setting is equal to addon.get_setting('my_setting')

        :param item:
        :type item: str
        """
        return self.get_setting(item)

    def __str__(self):
        return '<Addon [{0}]>'.format(self.id)

    def __repr__(self):
        return '<simpleplugin.Addon object [{0}]>'.format(self.id)

    @property
    def addon(self):
        """
        Kodi Addon instance that represents this Addon

        :return: Addon instance
        :rtype: xbmcaddon.Addon
        """
        return self._addon

    @property
    def id(self):
        """
        Addon ID

        :return: Addon ID, e.g. 'plugin.video.foo'
        :rtype: str
        """
        return self._addon.getAddonInfo('id')

    @property
    def path(self):
        """
        Addon path

        :return: path to the addon folder
        :rtype: str
        """
        return self._addon.getAddonInfo('path').decode('utf-8')

    @property
    def icon(self):
        """
        Addon icon

        :return: path to the addon icon image
        :rtype: str
        """
        icon = os.path.join(self.path, 'icon.png')
        if os.path.exists(icon):
            return icon
        else:
            return ''

    @property
    def fanart(self):
        """
        Addon fanart

        :return: path to the addon fanart image
        :rtype: str
        """
        fanart = os.path.join(self.path, 'fanart.jpg')
        if os.path.exists(fanart):
            return fanart
        else:
            return ''

    @property
    def config_dir(self):
        """
        Addon config dir

        :return: path to the addon config dir
        :rtype: str
        """
        return self._configdir

    @property
    def version(self):
        """
        Addon version

        :return: addon version
        :rtype: str
        """
        return self._addon.getAddonInfo('version')

    def get_localized_string(self, id_):
        """
        Get localized UI string

        :param id_: UI string ID
        :type id_: int
        :return: UI string in the current language
        :rtype: str
        """
        return self._addon.getLocalizedString(id_).encode('utf-8')

    def get_setting(self, id_, convert=True):
        """
        Get addon setting

        If ``convert=True``, 'bool' settings are converted to Python :class:`bool` values,
        and numeric strings to Python :class:`long` or :class:`float` depending on their format.

        .. note:: Settings can also be read via :class:`Addon` instance poperties named as the respective settings.
            I.e. ``addon.foo`` is equal to ``addon.get_setting('foo')``.

        :param id_: setting ID
        :type id_: str
        :param convert: try to guess and convert the setting to an appropriate type
            E.g. ``'1.0'`` will be converted to float ``1.0`` number, ``'true'`` to ``True`` and so on.
        :type convert: bool
        :return: setting value
        """
        setting = self._addon.getSetting(id_)
        if convert:
            if setting == 'true':
                return True  # Convert boolean strings to bool
            elif setting == 'false':
                return False
            elif re.search(r'^-?\d+$', setting) is not None:
                return long(setting)  # Convert numeric strings to long
            elif re.search(r'^-?\d+\.\d+$', setting) is not None:
                return float(setting)  # Convert numeric strings with a dot to float
        return setting

    def set_setting(self, id_, value):
        """
        Set addon setting

        Python :class:`bool` type are converted to ``'true'`` or ``'false'``
        Non-string/non-unicode values are converted to strings.

        .. warning:: Setting values via :class:`Addon` instance properties is not supported!
            Values can only be set using :meth:`Addon.set_setting` method.

        :param id_: setting ID
        :type id_: str
        :param value: setting value
        """
        if isinstance(value, bool):
            value = 'true' if value else 'false'
        elif not isinstance(value, basestring):
            value = str(value)
        self._addon.setSetting(id_, value)

    def log(self, message, level=xbmc.LOGDEBUG):
        """
        Add message to Kodi log starting with Addon ID

        :param message: message to be written into the Kodi log
        :type message: str
        :param level: log level. :mod:`xbmc` module provides the necessary symbolic constants.
            Default: ``xbmc.LOGDEBUG``
        :type level: int
        """
        if isinstance(message, unicode):
            message = message.encode('utf-8')
        xbmc.log('{0} [v.{1}]: {2}'.format(self.id, self.version, message), level)

    def log_notice(self, message):
        """
        Add NOTICE message to the Kodi log

        :param message: message to write to the Kodi log
        :type message: str
        """
        self.log(message, xbmc.LOGNOTICE)

    def log_warning(self, message):
        """
        Add WARNING message to the Kodi log

        :param message: message to write to the Kodi log
        :type message: str
        """
        self.log(message, xbmc.LOGWARNING)

    def log_error(self, message):
        """
        Add ERROR message to the Kodi log

        :param message: message to write to the Kodi log
        :type message: str
        """
        self.log(message, xbmc.LOGERROR)

    def log_debug(self, message):
        """
        Add debug message to the Kodi log

        :param message: message to write to the Kodi log
        :type message: str
        """
        self.log(message, xbmc.LOGDEBUG)

    def get_storage(self, filename='storage.pcl'):
        """
        Get a persistent :class:`Storage` instance for storing arbitrary values between addon calls.

        A :class:`Storage` instance can be used as a context manager.

        Example::

            with plugin.get_storage() as storage:
                storage['param1'] = value1
                value2 = storage['param2']

        .. note:: After exiting :keyword:`with` block a :class:`Storage` instance is invalidated.

        :param filename: the name of a storage file (optional)
        :type filename: str
        :return: Storage object
        :rtype: Storage
        """
        return Storage(self.config_dir, filename)

    def get_mem_storage(self, storage_id='', window_id=10000):
        """
        Creates an in-memory storage for this addon with :class:`dict`-like
        interface

        The storage can store picklable Python objects as long as
        Kodi is running and storage contents can be shared between
        Python processes. Different addons have separate storages,
        so storages with the same names created with this method
        do not conflict.

        Example::

            addon = Addon()
            storage = addon.get_mem_storage()
            foo = storage['foo']
            storage['bar'] = bar

        :param storage_id: optional storage ID (case-insensitive).
        :type storage_id: str
        :param window_id: the ID of a Kodi Window object where storage contents
            will be stored.
        :type window_id: int
        :return: in-memory storage for this addon
        :rtype: MemStorage
        """
        if storage_id:
            storage_id = '{0}_{1}'.format(self.id, storage_id)
        return MemStorage(storage_id, window_id)

    def _get_cached_data(self, cache, func, duration, *args, **kwargs):
        """
        Get data from a cache object

        :param cache: cache object
        :param func: function to cache
        :param duration: cache duration
        :param args: function args
        :param kwargs: function kwargs
        :return: function return data
        """
        if duration <= 0:
            raise ValueError('Caching duration cannot be zero or negative!')
        current_time = datetime.now()
        key = func.__name__ + str(args) + str(kwargs)
        try:
            data, timestamp = cache[key]
            if current_time - timestamp > timedelta(minutes=duration):
                raise KeyError
            self.log_debug('Cache hit: {0}'.format(key))
        except KeyError:
            self.log_debug('Cache miss: {0}'.format(key))
            data = func(*args, **kwargs)
            cache[key] = (data, current_time)
        return data

    def cached(self, duration=10):
        """
        Cached decorator

        Used to cache function return data

        Usage::

            @plugin.cached(30)
            def my_func(*args, **kwargs):
                # Do some stuff
                return value

        :param duration: caching duration in min (positive values only)
        :type duration: int
        :raises ValueError: if duration is zero or negative
        """
        def outer_wrapper(func):
            @wraps(func)
            def inner_wrapper(*args, **kwargs):
                with self.get_storage('__cache__.pcl') as cache:
                    return self._get_cached_data(cache, func, duration, *args, **kwargs)
            return inner_wrapper
        return outer_wrapper

    def mem_cached(self, duration=10):
        """
        In-memory cache decorator

        Usage::

            @plugin.mem_cached(30)
            def my_func(*args, **kwargs):
                # Do some stuff
                return value

        :param duration: caching duration in min (positive values only)
        :type duration: int
        :raises ValueError: if duration is zero or negative
        """
        def outer_wrapper(func):
            @wraps(func)
            def inner_wrapper(*args, **kwargs):
                cache = self.get_mem_storage('***cache***')
                return self._get_cached_data(cache, func, duration, *args, **kwargs)
            return inner_wrapper
        return outer_wrapper

    def gettext(self, ui_string):
        """
        Get a translated UI string from addon localization files.

        This function emulates GNU Gettext for more convenient access
        to localized addon UI strings. To reduce typing this method object
        can be assigned to a ``_`` (single underscore) variable.

        For using gettext emulation :meth:`Addon.initialize_gettext` method
        needs to be called first. See documentation for that method for more info
        about Gettext emulation.

        :param ui_string: a UI string from English :file:`strings.po`.
        :type ui_string: str
        :return: a UI string from translated :file:`strings.po`.
        :rtype: unicode
        :raises SimplePluginError: if :meth:`Addon.initialize_gettext` wasn't called first
            or if a string is not found in English :file:`strings.po`.
        """
        if self._ui_strings_map is not None:
            try:
                return self.get_localized_string(self._ui_strings_map['strings'][ui_string])
            except KeyError:
                raise SimplePluginError('UI string "{0}" is not found in strings.po!'.format(ui_string))
        else:
            raise SimplePluginError('Addon localization is not initialized!')

    def initialize_gettext(self):
        """
        Initialize GNU gettext emulation in addon

        Kodi localization system for addons is not very convenient
        because you need to operate with numeric string codes instead
        of UI strings themselves which reduces code readability and
        may lead to errors. The :class:`Addon` class provides facilities
        for emulating GNU Gettext localization system.

        This allows to use UI strings from addon's English :file:`strings.po`
        file instead of numeric codes to return localized strings from
        respective localized :file:`.po` files.

        This method returns :meth:`Addon.gettext` method object that
        can be assigned to a short alias to reduce typing. Traditionally,
        ``_`` (a single underscore) is used for this purpose.

        Example::

            addon = simpleplugin.Addon()
            _ = addon.initialize_gettext()

            xbmcgui.Dialog().notification(_('Warning!'), _('Something happened'))

        In the preceding example the notification strings will be replaced
        with localized versions if these strings are translated.

        :return: :meth:`Addon.gettext` method object
        :raises SimplePluginError: if the addon's English :file:`strings.po` file is missing
        """
        strings_po = os.path.join(self.path, 'resources', 'language', 'resource.language.en_gb', 'strings.po')
        if not os.path.exists(strings_po):
            strings_po = os.path.join(self.path, 'resources', 'language', 'English', 'strings.po')
        if os.path.exists(strings_po):
            with open(strings_po, 'rb') as fo:
                raw_strings = fo.read()
            raw_strings_hash = md5(raw_strings).hexdigest()
            gettext_pcl = '__gettext__.pcl'
            with self.get_storage(gettext_pcl) as ui_strings_map:
                if (not os.path.exists(os.path.join(self._configdir, gettext_pcl)) or
                        raw_strings_hash != ui_strings_map['hash']):
                    ui_strings = self._parse_po(raw_strings.split('\n'))
                    self._ui_strings_map = {
                        'hash': raw_strings_hash,
                        'strings': ui_strings
                    }
                    ui_strings_map['hash'] = raw_strings_hash
                    ui_strings_map['strings'] = ui_strings.copy()
                else:
                    self._ui_strings_map = deepcopy(ui_strings_map)
        else:
            raise SimplePluginError('Unable to initialize localization because of missing English strings.po!')
        return self.gettext

    def _parse_po(self, strings):
        """
        Parses ``strings.po`` file into a dict of {'string': id} items.
        """
        ui_strings = {}
        string_id = None
        for string in strings:
            if string_id is None and 'msgctxt' in string:
                string_id = int(re.search(r'"#(\d+)"', string).group(1))
            elif string_id is not None and 'msgid' in string:
                ui_strings[re.search(r'"(.*?)"', string, re.U).group(1)] = string_id
                string_id = None
        return ui_strings


class Plugin(Addon):
    """
    Plugin class

    :param id_: plugin's id, e.g. 'plugin.video.foo' (optional)
    :type id_: str

    This class provides a simplified API to create virtual directories of playable items
    for Kodi content plugins.
    :class:`simpleplugin.Plugin` uses a concept of callable plugin actions (functions or methods)
    that are defined using :meth:`Plugin.action` decorator.
    A Plugin instance must have at least one action that is named ``'root'``.

    Minimal example:

    .. code-block:: python

        from simpleplugin import Plugin

        plugin = Plugin()

        @plugin.action()
        def root():  # Mandatory item!
            return [{'label': 'Foo',
                    'url': plugin.get_url(action='some_action', label='Foo')},
                    {'label': 'Bar',
                    'url': plugin.get_url(action='some_action', label='Bar')}]

        @plugin.action()
        def some_action(params):
            return [{'label': params.label]}]

        plugin.run()

    An action callable may receive 1 optional parameter which is
    a dict-like object containing plugin call parameters (including action string)
    The action callable can return
    either a list/generator of dictionaries representing Kodi virtual directory items
    or a resolved playable path (:class:`str` or :obj:`unicode`) for Kodi to play.

    Example 1::

        @plugin.action()
        def list_action(params):
            listing = get_listing(params)  # Some external function to create listing
            return listing

    The ``listing`` variable is a Python list/generator of dict items.
    Example 2::

        @plugin.action()
        def play_action(params):
            path = get_path(params)  # Some external function to get a playable path
            return path

    Each dict item can contain the following properties:

    - label -- item's label (default: ``''``).
    - label2 -- item's label2 (default: ``''``).
    - thumb -- item's thumbnail (default: ``''``).
    - icon -- item's icon (default: ``''``).
    - path -- item's path (default: ``''``).
    - fanart -- item's fanart (optional).
    - art -- a dict containing all item's graphic (see :meth:`xbmcgui.ListItem.setArt` for more info) -- optional.
    - stream_info -- a dictionary of ``{stream_type: {param: value}}`` items
      (see :meth:`xbmcgui.ListItem.addStreamInfo`) -- optional.
    - info --  a dictionary of ``{media: {param: value}}`` items
      (see :meth:`xbmcgui.ListItem.setInfo`) -- optional
    - context_menu - a list that contains 2-item tuples ``('Menu label', 'Action')``.
      The items from the tuples are added to the item's context menu.
    - url -- a callback URL for this list item.
    - is_playable -- if ``True``, then this item is playable and must return a playable path or
     be resolved via :meth:`Plugin.resolve_url` (default: ``False``).
    - is_folder -- if ``True`` then the item will open a lower-level sub-listing. if ``False``,
      the item either is a playable media or a general-purpose script
      which neither creates a virtual folder nor points to a playable media (default: C{True}).
      if ``'is_playable'`` is set to ``True``, then ``'is_folder'`` value automatically assumed to be ``False``.
    - subtitles -- the list of paths to subtitle files (optional).
    - mime -- item's mime type (optional).
    - list_item -- an 'class:`xbmcgui.ListItem` instance (optional).
      It is used when you want to set all list item properties by yourself.
      If ``'list_item'`` property is present, all other properties,
      except for ``'url'`` and ``'is_folder'``, are ignored.
    - properties -- a dictionary of list item properties
      (see :meth:`xbmcgui.ListItem.setProperty`) -- optional.
    - cast -- a list of cast info (actors, roles, thumbnails) for the list item
      (see :meth:`xbmcgui.ListItem.setCast`) -- optional.
    - offscreen -- if ``True`` do not lock GUI (used for Python scrapers and subtitle plugins) --
      optional.
    - content_lookup -- if ``False``, do not HEAD requests to get mime type. Optional.
    - online_db_ids -- a :class:`dict` of ``{'label': 'value'}`` pairs representing
      the item's IDs in popular online databases. Possible labels: 'imdb', 'tvdb',
      'tmdb', 'anidb', see :meth:`xbmcgui.ListItem.setUniqueIDs`. Optional.
    - ratings -- a :class:`list` of :class:`dict`s with the following keys:
      'type' (:class:`str`), 'rating' (:class:`float`),
      'votes' (:class:`int`, optional), 'defaultt' (:class:`bool`, optional).
      This list sets item's ratings in popular online databases.
      Possible types: 'imdb', 'tvdb', tmdb', 'anidb'.
      See :meth:`xbmcgui.ListItem.setRating`. Optional.


    Example 3::

        listing = [{    'label': 'Label',
                        'label2': 'Label 2',
                        'thumb': 'thumb.png',
                        'icon': 'icon.png',
                        'fanart': 'fanart.jpg',
                        'art': {'clearart': 'clearart.png'},
                        'stream_info': {'video': {'codec': 'h264', 'duration': 1200},
                                        'audio': {'codec': 'ac3', 'language': 'en'}},
                        'info': {'video': {'genre': 'Comedy', 'year': 2005}},
                        'context_menu': [('Menu Item', 'Action')],
                        'url': 'plugin:/plugin.video.test/?action=play',
                        'is_playable': True,
                        'is_folder': False,
                        'subtitles': ['/path/to/subtitles.en.srt', '/path/to/subtitles.uk.srt'],
                        'mime': 'video/mp4'
                        }]

    Alternatively, an action callable can use :meth:`Plugin.create_listing` and :meth:`Plugin.resolve_url`
    static methods to pass additional parameters to Kodi.

    Example 4::

        @plugin.action()
        def list_action(params):
            listing = get_listing(params)  # Some external function to create listing
            return Plugin.create_listing(listing, sort_methods=(2, 10, 17), view_mode=500)

    Example 5::

        @plugin.action()
        def play_action(params):
            path = get_path(params)  # Some external function to get a playable path
            return Plugin.resolve_url(path, succeeded=True)

    If an action callable performs any actions other than creating a listing or
    resolving a playable URL, it must return ``None``.
    """
    def __init__(self, id_=''):
        """
        Class constructor
        """
        super(Plugin, self).__init__(id_)
        self._url = 'plugin://{0}/'.format(self.id)
        self._handle = None
        self.actions = {}

    def __str__(self):
        return '<Plugin {0}>'.format(sys.argv)

    def __repr__(self):
        return '<simpleplugin.Plugin object {0}>'.format(sys.argv)

    @staticmethod
    def get_params(paramstring):
        """
        Convert a URL-encoded paramstring to a Python dict

        :param paramstring: URL-encoded paramstring
        :type paramstring: str
        :return: parsed paramstring
        :rtype: Params
        """
        raw_params = parse_qs(paramstring)
        params = Params()
        for key, value in raw_params.iteritems():
            params[key] = value[0] if len(value) == 1 else value
        return params

    def get_url(self, plugin_url='', **kwargs):
        """
        Construct a callable URL for a virtual directory item

        If plugin_url is empty, a current plugin URL is used.
        kwargs are converted to a URL-encoded string of plugin call parameters
        To call a plugin action, 'action' parameter must be used,
        if 'action' parameter is missing, then the plugin root action is called
        If the action is not added to :class:`Plugin` actions, :class:`PluginError` will be raised.

        :param plugin_url: plugin URL with trailing / (optional)
        :type plugin_url: str
        :param kwargs: pairs of key=value items
        :return: a full plugin callback URL
        :rtype: str
        """
        url = plugin_url or self._url
        if kwargs:
            return '{0}?{1}'.format(url, urlencode(kwargs, doseq=True))
        return url

    def action(self, name=None):
        """
        Action decorator

        Defines plugin callback action. If action's name is not defined explicitly,
        then the action is named after the decorated function.

        .. warning:: Action's name must be unique.

        A plugin must have at least one action named ``'root'`` implicitly or explicitly.

        Example:

        .. code-block:: python

            @plugin.action()  # The action is implicitly named 'root' after the decorated function
            def root(params):
                pass

            @plugin.action('foo')  # The action name is set explicitly
            def foo_action(params):
                pass

        :param name: action's name (optional).
        :type name: str
        :raises SimplePluginError: if the action with such name is already defined.
        """
        def wrap(func, name=name):
            if name is None:
                name = func.__name__
            if name in self.actions:
                raise SimplePluginError('Action "{0}" already defined!'.format(name))
            self.actions[name] = func
            return func
        return wrap

    def run(self, category=None):
        """
        Run plugin

        :raises SimplePluginError: if unknown action string is provided.
        """
        if category:
            self.log_warning(
                'Deprecation warning: Plugin category is no longer set via Plugin.run(). '
                'Use "category" parameter of Plugin.create_listing() instead.'
            )
        self._handle = int(sys.argv[1])
        params = self.get_params(sys.argv[2][1:])
        action = params.get('action', 'root')
        self.log_debug(str(self))
        self.log_debug('Actions: {0}'.format(str(self.actions.keys())))
        self.log_debug('Called action "{0}" with params "{1}"'.format(
            action, str(params))
        )
        try:
            action_callable = self.actions[action]
        except KeyError:
            raise SimplePluginError('Invalid action: "{0}"!'.format(action))
        else:
            # inspect.isfunction is needed for tests
            if inspect.isfunction(action_callable) and not inspect.getargspec(action_callable).args:
                result = action_callable()
            else:
                result = action_callable(params)
            self.log_debug('Action return value: {0}'.format(str(result)))
            if isinstance(result, (list, GeneratorType)):
                self._add_directory_items(self.create_listing(result))
            elif isinstance(result, basestring):
                self._set_resolved_url(self.resolve_url(result))
            elif isinstance(result, ListContext):
                self._add_directory_items(result)
            elif isinstance(result, PlayContext):
                self._set_resolved_url(result)
            else:
                self.log_debug('The action "{0}" has not returned any valid data to process.'.format(action))

    @staticmethod
    def create_listing(listing, succeeded=True, update_listing=False, cache_to_disk=False, sort_methods=None,
                       view_mode=None, content=None, category=None):
        """
        Create and return a context dict for a virtual folder listing

        :param listing: the list of the plugin virtual folder items
        :type listing: list or types.GeneratorType
        :param succeeded: if ``False`` Kodi won't open a new listing and stays on the current level.
        :type succeeded: bool
        :param update_listing: if ``True``, Kodi won't open a sub-listing but refresh the current one.
        :type update_listing: bool
        :param cache_to_disk: cache this view to disk.
        :type cache_to_disk: bool
        :param sort_methods: the list of integer constants representing virtual folder sort methods.
        :type sort_methods: tuple
        :param view_mode: a numeric code for a skin view mode.
            View mode codes are different in different skins except for ``50`` (basic listing).
        :type view_mode: int
        :param content: string - current plugin content, e.g. 'movies' or 'episodes'.
            See :func:`xbmcplugin.setContent` for more info.
        :type content: str
        :param category: str - plugin sub-category, e.g. 'Comedy'.
            See :func:`xbmcplugin.setPluginCategory` for more info.
        :type category: str
        :return: context object containing necessary parameters
            to create virtual folder listing in Kodi UI.
        :rtype: ListContext
        """
        return ListContext(listing, succeeded, update_listing, cache_to_disk,
                           sort_methods, view_mode, content, category)

    @staticmethod
    def resolve_url(path='', play_item=None, succeeded=True):
        """
        Create and return a context dict to resolve a playable URL

        :param path: the path to a playable media.
        :type path: str or unicode
        :param play_item: a dict of item properties as described in the class docstring.
            It allows to set additional properties for the item being played, like graphics, metadata etc.
            if ``play_item`` parameter is present, then ``path`` value is ignored, and the path must be set via
            ``'path'`` property of a ``play_item`` dict.
        :type play_item: dict
        :param succeeded: if ``False``, Kodi won't play anything
        :type succeeded: bool
        :return: context object containing necessary parameters
            for Kodi to play the selected media.
        :rtype: PlayContext
        """
        return PlayContext(path, play_item, succeeded)

    @staticmethod
    def create_list_item(item):
        """
        Create an :class:`xbmcgui.ListItem` instance from an item dict

        :param item: a dict of ListItem properties
        :type item: dict
        :return: ListItem instance
        :rtype: xbmcgui.ListItem
        """
        major_version = xbmc.getInfoLabel('System.BuildVersion')[:2]
        if major_version >= '18':
            list_item = xbmcgui.ListItem(label=item.get('label', ''),
                                         label2=item.get('label2', ''),
                                         path=item.get('path', ''),
                                         offscreen=item.get('offscreen', False))
        else:
            list_item = xbmcgui.ListItem(label=item.get('label', ''),
                                         label2=item.get('label2', ''),
                                         path=item.get('path', ''))
        if major_version >= '16':
            art = item.get('art', {})
            art['thumb'] = item.get('thumb', '')
            art['icon'] = item.get('icon', '')
            art['fanart'] = item.get('fanart', '')
            item['art'] = art
            cont_look = item.get('content_lookup')
            if cont_look is not None:
                list_item.setContentLookup(cont_look)
        else:
            list_item.setThumbnailImage(item.get('thumb', ''))
            list_item.setIconImage(item.get('icon', ''))
            list_item.setProperty('fanart_image', item.get('fanart', ''))
        if item.get('art'):
            list_item.setArt(item['art'])
        if item.get('stream_info'):
            for stream, stream_info in item['stream_info'].iteritems():
                list_item.addStreamInfo(stream, stream_info)
        if item.get('info'):
            for media, info in item['info'].iteritems():
                list_item.setInfo(media, info)
        if item.get('context_menu') is not None:
            list_item.addContextMenuItems(item['context_menu'])
        if item.get('subtitles'):
            list_item.setSubtitles(item['subtitles'])
        if item.get('mime'):
            list_item.setMimeType(item['mime'])
        if item.get('properties'):
            for key, value in item['properties'].iteritems():
                list_item.setProperty(key, value)
        if major_version >= '17':
            cast = item.get('cast')
            if cast is not None:
                list_item.setCast(cast)
            db_ids = item.get('online_db_ids')
            if db_ids is not None:
                list_item.setUniqueIDs(db_ids)
            ratings = item.get('ratings')
            if ratings is not None:
                for rating in ratings:
                    list_item.setRating(**rating)
        return list_item

    def _add_directory_items(self, context):
        """
        Create a virtual folder listing

        :param context: context object
        :type context: ListContext
        :raises SimplePluginError: if sort_methods parameter is not int, tuple or list
        """
        self.log_debug('Creating listing from {0}'.format(str(context)))
        if context.category is not None:
            xbmcplugin.setPluginCategory(self._handle, context.category)
        if context.content is not None:
            xbmcplugin.setContent(self._handle, context.content)  # This must be at the beginning
        for item in context.listing:
            is_folder = item.get('is_folder', True)
            if item.get('list_item') is not None:
                list_item = item['list_item']
            else:
                list_item = self.create_list_item(item)
                if item.get('is_playable'):
                    list_item.setProperty('IsPlayable', 'true')
                    is_folder = False
            xbmcplugin.addDirectoryItem(self._handle, item['url'], list_item, is_folder)
        if context.sort_methods is not None:
            if isinstance(context.sort_methods, int):
                xbmcplugin.addSortMethod(self._handle, context.sort_methods)
            elif isinstance(context.sort_methods, (tuple, list)):
                for method in context.sort_methods:
                    xbmcplugin.addSortMethod(self._handle, method)
            else:
                raise TypeError(
                    'sort_methods parameter must be of int, tuple or list type!')
        xbmcplugin.endOfDirectory(self._handle,
                                  context.succeeded,
                                  context.update_listing,
                                  context.cache_to_disk)
        if context.view_mode is not None:
            xbmc.executebuiltin('Container.SetViewMode({0})'.format(context.view_mode))

    def _set_resolved_url(self, context):
        """
        Resolve a playable URL

        :param context: context object
        :type context: PlayContext
        """
        self.log_debug('Resolving URL from {0}'.format(str(context)))
        if context.play_item is None:
            list_item = xbmcgui.ListItem(path=context.path)
        else:
            list_item = self.create_list_item(context.play_item)
        xbmcplugin.setResolvedUrl(self._handle, context.succeeded, list_item)
