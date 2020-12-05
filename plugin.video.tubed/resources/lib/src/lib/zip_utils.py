# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import os
import zipfile

from ..constants import ADDON_ID


def compress(filename, file_list, mode='w'):
    with zipfile.ZipFile(filename, mode) as zip_handle:

        for source_path in file_list:
            if not os.path.exists(source_path) or ADDON_ID not in source_path:
                continue

            if os.path.isfile(source_path):
                arc_path = source_path.split(ADDON_ID)[1]
                zip_handle.write(source_path, arc_path)
                continue

            if os.path.isdir(source_path):
                for folder, _, filenames in os.walk(source_path):
                    for name in filenames:
                        file_path = os.path.join(folder, name)
                        arc_path = str(file_path.split(ADDON_ID)[1])
                        zip_handle.write(file_path, arc_path)
                continue


def decompress(filename, path):
    if not os.path.exists(filename) or not os.path.exists(path) or ADDON_ID not in path:
        raise Exception

    with zipfile.ZipFile(filename, 'r') as zip_handle:
        zip_handle.extractall(path=path)
