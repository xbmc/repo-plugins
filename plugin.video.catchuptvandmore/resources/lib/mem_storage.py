# -*- coding: utf-8 -*-
# Created on: 03.06.2015
"""
SimplePlugin micro-framework for Kodi content plugins
**Author**: Roman Miroshnychenko aka Roman V.M.
**License**: `GPL v.3 <https://www.gnu.org/copyleft/gpl.html>`_
"""


try:
    import pickle as pickle
except ImportError:
    import pickle
try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping
from kodi_six import xbmcgui
from six import string_types


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
        """
        :type storage_id: str
        :type window_id: int
        """
        self._id = storage_id
        self._window = xbmcgui.Window(window_id)
        try:
            self['__keys__']
        except KeyError:
            self['__keys__'] = []

    def _check_key(self, key):
        """
        :type key: str
        """
        if isinstance(key, string_types):
            pass
        else:
            raise TypeError('Storage key must be of str type!')

    def _format_contents(self):
        """
        :rtype: str
        """
        lines = []
        for key, val in list(self.items()):
            lines.append('{0}: {1}'.format(repr(key), repr(val)))
        return ', '.join(lines)

    def __str__(self):
        return '<MemStorage {{{0}}}>'.format(self._format_contents())

    def __repr__(self):
        return '<simpleplugin.MemStorage object {{{0}}}'.format(
            self._format_contents())

    def __getitem__(self, key):
        self._check_key(key)
        full_key = '{0}__{1}'.format(self._id, key)
        raw_item = self._window.getProperty(full_key)
        if not raw_item:
            raise KeyError(key)
        return pickle.loads(raw_item.encode('latin-1'))

    def __setitem__(self, key, value):
        self._check_key(key)
        full_key = '{0}__{1}'.format(self._id, key)
        self._window.setProperty(full_key, pickle.dumps(value, protocol=0).decode('latin-1'))
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
