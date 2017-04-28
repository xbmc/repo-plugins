import os
import cPickle as pickle
import xbmcgui
from collections import MutableMapping, namedtuple
from hashlib import md5
from shutil import move

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
            self._window.setProperty(full_key, '')
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
