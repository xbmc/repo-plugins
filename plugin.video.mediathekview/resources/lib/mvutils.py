# -*- coding: utf-8 -*-
"""
Utilities module

Copyright (c) 2017-2019, Leo Moll
SPDX-License-Identifier: MIT
"""

from __future__ import unicode_literals

import os
import sys
import stat
import string

# pylint: disable=import-error
try:
    # Python 3.x
    from urllib.parse import urlencode
    from urllib.request import urlopen
except ImportError:
    from urllib import urlencode
    from urllib2 import urlopen

from contextlib import closing
from resources.lib.exceptions import ExitRequested

# -- Kodi Specific Imports ----------------------------------
try:
    import xbmcvfs
    IS_KODI = True
except ImportError:
    IS_KODI = False


PY2 = sys.version_info[0] == 2

def py2_encode(s, encoding='utf-8'):
   """
   Encode Python 2 ``unicode`` to ``str``

   In Python 3 the string is not changed.   
   """
   if PY2 and isinstance(s, unicode):
       s = s.encode(encoding)
   return s


def py2_decode(s, encoding='utf-8'):
   """
   Decode Python 2 ``str`` to ``unicode``

   In Python 3 the string is not changed.
   """
   if PY2 and isinstance(s, str):
       s = s.decode(encoding)
   return s

def array_to_utf(a):
    autf = []
    i = 0
    for v in a:
        if PY2 and isinstance(v, unicode):
            autf.append(py2_encode(v))
        elif PY2 and isinstance(v, dict):
            autf.append(dict_to_utf(v))
        elif PY2 and isinstance(v, list):
            autf.append(array_to_utf(v))
        else:
            autf.append(v)
    return autf

def dict_to_utf(d):
    dutf = {}
    for k,v in list(d.items()):
        if PY2 and isinstance(v, unicode):
            dutf[k] = py2_encode(v)
        elif PY2 and isinstance(v, list):
            dutf[k] = array_to_utf(v)
        elif PY2 and isinstance(v, dict):
            dutf[k] = dict_to_utf(v)
        else:
            dutf[k] = v
    return dutf

def dir_exists(name):
    """
    Tests if a directory exists

    Args:
        name(str): full pathname of the directory
    """
    try:
        state = os.stat(name)
        return stat.S_ISDIR(state.st_mode)
    except OSError:
        return False


def file_exists(name):
    """
    Tests if a file exists

    Args:
        name(str): full pathname of the file
    """
    try:
        state = os.stat(name)
        return stat.S_ISREG(state.st_mode)
    except OSError:
        return False


def file_size(name):
    """
    Get the size of a file

    Args:
        name(str): full pathname of the file
    """
    try:
        state = os.stat(name)
        return state.st_size
    except OSError:
        return 0


def file_remove(name):
    """
    Delete a file

    Args:
        name(str): full pathname of the file
    """
    if file_exists(name):
        try:
            os.remove(name)
            return True
        except OSError:
            pass
    return False


def file_rename(srcname, dstname):
    """
    Rename a file

    Args:
        srcname(str): name of the source file
        dstname(str): name of the file after the rename operation
    """
    if file_exists(srcname):
        try:
            os.rename(srcname, dstname)
            return True
        except OSError:
            # maybe windows on overwrite. try non atomic rename
            try:
                os.remove(dstname)
                os.rename(srcname, dstname)
                return True
            except OSError:
                return False
    return False


def find_gzip():
    """
    Return the full pathname to the gzip decompressor
    executable
    """
    for gzbin in ['/bin/gzip', '/usr/bin/gzip', '/usr/local/bin/gzip', '/system/bin/gzip']:
        if file_exists(gzbin):
            return gzbin
    return None


def find_xz():
    """
    Return the full pathname to the xz decompressor
    executable
    """
    for xzbin in ['/bin/xz', '/usr/bin/xz', '/usr/local/bin/xz', '/system/bin/xz']:
        if file_exists(xzbin):
            return xzbin
    return None


def make_search_string(val):
    """
    Reduces a string to a simplified representation
    containing only a well defined set of characters
    for a simplified search
    """
    cset = string.ascii_letters + string.digits + ' _-#'
    search = ''.join([c for c in val if c in cset])
    return search.upper().strip()


def make_duration(val):
    """
    Converts a string in `hh:mm:ss` representation
    to the equivalent number of seconds

    Args:
        val(str): input string in format `hh:mm:ss`
    """
    if val == "00:00:00":
        return None
    elif val is None:
        return None
    parts = val.split(':')
    if len(parts) != 3:
        return None
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])


def cleanup_filename(val):
    """
    Strips strange characters from a string in order
    to create a valid filename

    Args:
        val(str): input string
    """
    cset = string.ascii_letters + string.digits + \
        u' _-#äöüÄÖÜßáàâéèêíìîóòôúùûÁÀÉÈÍÌÓÒÚÙçÇœ'
    search = ''.join([c for c in val if c in cset])
    return search.strip()


def url_retrieve(url, filename, reporthook, chunk_size=8192, aborthook=None):
    """
    Copy a network object denoted by a URL to a local file

    Args:
        url(str): the source url of the object to retrieve

        filename(str): the destination filename

        reporthook(function): a hook function that will be called once on
            establishment of the network connection and once after each
            block read thereafter. The hook will be passed three arguments;
            a count of blocks transferred so far, a block size in bytes,
            and the total size of the file.

        chunk_size(int, optional): size of the chunks read by the function.
            Default is 8192

        aborthook(function, optional): a hook function that will be called
            once on establishment of the network connection and once after
            each block read thereafter. If specified the operation will be
            aborted if the hook function returns `True`
    """
    with closing(urlopen(url, timeout = 10)) as src, closing(open(filename, 'wb')) as dst:
        _chunked_url_copier(src, dst, reporthook, chunk_size, aborthook)


def url_retrieve_vfs(url, filename, reporthook, chunk_size=8192, aborthook=None):
    """
    Copy a network object denoted by a URL to a local file using
    Kodi's VFS functions

    Args:
        url(str): the source url of the object to retrieve

        filename(str): the destination filename

        reporthook(function): a hook function that will be called once on
            establishment of the network connection and once after each
            block read thereafter. The hook will be passed three arguments;
            a count of blocks transferred so far, a block size in bytes,
            and the total size of the file.

        chunk_size(int, optional): size of the chunks read by the function.
            Default is 8192

        aborthook(function, optional): a hook function that will be called
            once on establishment of the network connection and once after
            each block read thereafter. If specified the operation will be
            aborted if the hook function returns `True`
    """
    with closing(urlopen(url, timeout = 10)) as src, closing(xbmcvfs.File(filename, 'wb')) as dst:
        _chunked_url_copier(src, dst, reporthook, chunk_size, aborthook)


def build_url(query):
    """
    Builds a valid plugin url based on the supplied query object

    Args:
        query(object): a query object
    """
    return sys.argv[0] + '?' + urlencode(query)


def _chunked_url_copier(src, dst, reporthook, chunk_size, aborthook):
    aborthook = aborthook if aborthook is not None else lambda: False
    total_size = int(
        src.info().get('Content-Length').strip()
    ) if src.info() and src.info().get('Content-Length') else 0
    total_chunks = 0

    while not aborthook():
        reporthook(total_chunks, chunk_size, total_size)
        byteStringchunk = src.read(chunk_size)
        if not byteStringchunk:
            # operation has finished
            return
        dst.write(bytearray(byteStringchunk))
        total_chunks += 1
    # abort requested
    raise ExitRequested('Reception interrupted.')
