# -*- coding: utf-8 -*-
from __future__ import absolute_import

# Standard Library Imports
from hashlib import sha1
import time
import sys
import os

try:
    # noinspection PyPep8Naming
    import cPickle as pickle
except ImportError:  # pragma: no cover
    import pickle

# Package imports
from resources.lib.codequick.script import Script
from resources.lib.codequick.utils import ensure_unicode, PY3

if PY3:
    # noinspection PyUnresolvedReferences, PyCompatibility
    from collections.abc import MutableMapping, MutableSequence
else:
    # noinspection PyUnresolvedReferences, PyCompatibility
    from collections import MutableMapping, MutableSequence

__all__ = ["PersistentDict", "PersistentList"]

# The addon profile directory
profile_dir = Script.get_info("profile")


class _PersistentBase(object):
    """
    Base class to handle persistent file handling.

    :param str name: Filename of persistence storage file.
    """

    def __init__(self, name):
        super(_PersistentBase, self).__init__()
        self._version_string = "__codequick_storage_version__"
        self._data_string = "__codequick_storage_data__"
        self._serializer_obj = object
        self._stream = None
        self._hash = None
        self._data = None

        # Filename is already a fullpath
        if os.path.sep in name:
            self._filepath = ensure_unicode(name)
            data_dir = os.path.dirname(self._filepath)
        else:
            # Filename must be relative, joining profile directory with filename
            self._filepath = os.path.join(profile_dir, ensure_unicode(name))
            data_dir = profile_dir

        # Ensure that filepath is bytes when platform type is linux/bsd
        if not sys.platform.startswith("win"):  # pragma: no branch
            self._filepath = self._filepath.encode("utf8")
            data_dir = data_dir.encode("utf8")

        # Create any missing data directory
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

    def _load(self):
        """Load in existing data from disk."""
        # Load storage file if exists
        if os.path.exists(self._filepath):
            self._stream = file_obj = open(self._filepath, "rb+")
            content = file_obj.read()

            # Calculate hash of current file content
            self._hash = sha1(content).hexdigest()

            # Load content and update storage
            return pickle.loads(content)

    def flush(self):
        """
        Synchronize data back to disk.

        Data will only be written to disk if content has changed.
        """

        # Serialize the storage data
        data = {self._version_string: 2, self._data_string: self._data}
        content = pickle.dumps(data, protocol=2)  # Protocol 2 is used for python2/3 compatibility
        current_hash = sha1(content).hexdigest()

        # Compare saved hash with current hash, to detect if content has changed
        if self._hash is None or self._hash != current_hash:
            # Check if FileObj Needs Creating First
            if self._stream:
                self._stream.seek(0)
                self._stream.truncate(0)
            else:
                self._stream = open(self._filepath, "wb+")

            # Dump data out to disk
            self._stream.write(content)
            self._hash = current_hash
            self._stream.flush()

    def close(self):
        """Flush content to disk & close file object."""
        self.flush()
        self._stream.close()
        self._stream = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def __len__(self):
        return len(self._data)

    def __getitem__(self, index):
        return self._data[index][0]

    def __setitem__(self, index, value):
        self._data[index] = (value, time.time())

    def __delitem__(self, index):
        del self._data[index]

    def __bool__(self):
        return bool(self._data)

    def __nonzero__(self):
        return bool(self._data)


class PersistentDict(_PersistentBase, MutableMapping):
    """
    Persistent storage with a :class:`dictionary<dict>` like interface.

    :param str name: Filename or path to storage file.
    :param int ttl: [opt] The amount of time in "seconds" that a value can be stored before it expires.

    .. note::

        ``name`` can be a filename, or the full path to a file.
        The add-on profile directory will be the default location for files, unless a full path is given.

    .. note:: If the ``ttl`` parameter is given, "any" expired data will be removed on initialization.

    .. note:: This class is also designed as a "Context Manager".

    .. note::

        Data will only be synced to disk when connection to file is
        "closed" or when "flush" method is explicitly called.

    :Example:
        >>> with PersistentDict("dictfile.pickle") as db:
        >>>     db["testdata"] = "testvalue"
        >>>     db.flush()
    """

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, dict(self.items()))

    def __init__(self, name, ttl=None):
        super(PersistentDict, self).__init__(name)
        data = self._load()
        self._data = {}

        if data:
            version = data.get(self._version_string, 1)
            if version == 1:
                self._data = {key: (val, time.time()) for key, val in data.items()}
            else:
                data = data[self._data_string]
                if ttl:
                    self._data = {key: item for key, item in data.items() if time.time() - item[1] < ttl}
                else:
                    self._data = data

    def items(self):
        return map(lambda x: (x[0], x[1][0]), self._data.items())


class PersistentList(_PersistentBase, MutableSequence):
    """
    Persistent storage with a :class:`list<list>` like interface.

    :param str name: Filename or path to storage file.
    :param int ttl: [opt] The amount of time in "seconds" that a value can be stored before it expires.

    .. note::

        ``name`` can be a filename, or the full path to a file.
        The add-on profile directory will be the default location for files, unless a full path is given.

    .. note:: If the ``ttl`` parameter is given, "any" expired data will be removed on initialization.

    .. note:: This class is also designed as a "Context Manager".

    .. note::

        Data will only be synced to disk when connection to file is
        "closed" or when "flush" method is explicitly called.

    :Example:
        >>> with PersistentList("listfile.pickle") as db:
        >>>     db.append("testvalue")
        >>>     db.extend(["test1", "test2"])
        >>>     db.flush()
    """

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, [val for val, _ in self._data])

    def __init__(self, name, ttl=None):
        super(PersistentList, self).__init__(name)
        data = self._load()
        self._data = []

        if data:
            if isinstance(data, list):
                self._data = [(val, time.time()) for val in data]
            else:
                data = data[self._data_string]
                if ttl:
                    self._data = [item for item in data if time.time() - item[1] < ttl]
                else:
                    self._data = data

    def insert(self, index, value):
        self._data.insert(index, (value, time.time()))

    def append(self, value):
        self._data.append((value, time.time()))
