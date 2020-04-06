# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Thomas Amland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from collections import namedtuple
import xbmc
import xbmcvfs


DirEntry = namedtuple('DirEntry', ['name', 'is_dir'])
monitor = xbmc.Monitor()


def _listdir(path):
    try:
        return xbmcvfs.listdir(path)
    except NameError:
        pass

    # Emulate xbmcvfs.listdir
    assert isinstance(path, str)
    assert path.endswith('/')
    assert os.path.isdir(path)

    dirs = []
    files = []
    path = path.rstrip('/')
    try:
        for name in os.listdir(path):
            if os.path.isdir(os.path.join(path, name)):
                dirs.append(name)
            else:
                files.append(name)
    except OSError:
        pass
    return dirs, files


def walk(path, filter_dir=lambda *args: True):
    assert not isinstance(path, str)
    return _walk(path, '', filter_dir)


def listdir(path):
    assert not isinstance(path, str)
    if not path.endswith('/'):
        path += '/'

    dirs, files = _listdir(path)
    for name in dirs:
        yield DirEntry(name, True)
    for name in files:
        yield DirEntry(name, False)


def _walk(path_head, path_tail, filter_dir):
    try:
        if monitor.abortRequested():
            return
    except NameError:
        pass

    dirs, files = _listdir(join(path_head, path_tail))
    if ".nomedia" in files:
        return

    for name in files:
        yield DirEntry(join(path_tail, name), False)

    for name in dirs:
        if filter_dir(path_tail, name):
            yield DirEntry(join(path_tail, name), True)
            for entry in _walk(path_head, join(path_tail, name), filter_dir):
                yield entry


def join(base_path, *paths):
    """
    Join VFS paths. Uses / as separator if base_path is an url. otherwise os.sep
    """
    assert isinstance(base_path, str)
    assert base_path != ""
    result = base_path

    for path in paths:
        if result != "" and not result.endswith('/') and not path.startswith('/'):
            result += '/'
        result += path

    return result
