# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import os
import pickle

import xbmcvfs  # pylint: disable=import-error

from ..constants import ADDON_ID

PATH = xbmcvfs.translatePath('special://temp/%s/' % ADDON_ID)


def write_pickled(filename, data):
    try:
        xbmcvfs.mkdirs(PATH)
    except:  # pylint: disable=bare-except
        os.makedirs(PATH)

    filename = os.path.join(PATH, filename)

    pickled_data = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)

    with open(filename, 'wb') as file_handle:
        file_handle.write(pickled_data)


def read_pickled(filename, delete_after=True):
    filename = os.path.join(PATH, filename)

    if not xbmcvfs.exists(filename):
        return None

    with open(filename, 'rb') as file_handle:
        pickled_data = file_handle.read()

    if delete_after:
        try:
            xbmcvfs.delete(filename)
        except:  # pylint: disable=bare-except
            os.remove(filename)

    return pickle.loads(pickled_data)
