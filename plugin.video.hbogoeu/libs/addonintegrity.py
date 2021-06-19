# encoding: utf-8
# Copyright (C) 2021 ArvVoid (https://github.com/arvvoid)
# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import absolute_import, division

import hashlib
import os
import sys

from kodi_six import xbmc, xbmcaddon  # type: ignore


class AddOnIntegrity(object):

    @staticmethod
    def debug(msg):
        try:
            xbmc.log("[" + xbmcaddon.Addon().getAddonInfo('id') + "] " + msg, xbmc.LOGDEBUG)
        except TypeError:
            xbmc.log("[" + xbmcaddon.Addon().getAddonInfo('id') + "] " + msg.decode('utf-8'), xbmc.LOGDEBUG)

    # create a list of file and sub directories
    @staticmethod
    def get_list_source_files(dirname):
        files = os.listdir(dirname)
        all_files = list()
        for entry in files:
            # Create full path
            fullpath = os.path.join(dirname, entry)
            # If entry is a directory then get the list of files in this directory
            if os.path.isdir(fullpath):
                all_files = all_files + AddOnIntegrity.get_list_source_files(fullpath)
            else:
                if entry.endswith(".py") or entry.endswith(".xml"):
                    all_files.append([fullpath, entry])

        return all_files

    # The purpose of this function is to generate a checksum of all source files of the add-on
    # and a global add-on checksum and output them on the debug log.
    # This should run only if debug is explicitly turned on in add-on settings.
    # A LIST OF INTEGRITY CHECKSUMS PER RELEASED VERSION
    # IS AVAILABLE AT https://github.com/arvvoid/plugin.video.hbogoeu/wiki/Releses-checksum
    @staticmethod
    def gen_integrity():
        tot_hash = ""
        add_on_path = xbmcaddon.Addon().getAddonInfo('path')
        AddOnIntegrity.debug("Add on installed: " + add_on_path)
        for file in AddOnIntegrity.get_list_source_files(add_on_path):
            file_hash = ""
            with open(file[0], "rb") as f:
                source_data = f.read()  # read entire file as bytes
                file_hash = hashlib.md5(source_data).hexdigest()
            AddOnIntegrity.debug("Add-on file: " + file[1] + " Checksum: " + file_hash)
            tot_hash += file_hash
        checksum = ""
        if sys.version_info < (3, 0):
            checksum = hashlib.md5(tot_hash).hexdigest()
        else:
            checksum = hashlib.md5(bytes(tot_hash, 'utf8')).hexdigest()
        AddOnIntegrity.debug("Integrity Checksum: " + checksum)

        return checksum
