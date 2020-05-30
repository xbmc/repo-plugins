# -*- coding: utf-8 -*-
"""
The custom exception module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""


class DatabaseCorrupted(RuntimeError):
    """This exception is raised when the database throws errors during update"""


class DatabaseLost(RuntimeError):
    """This exception is raised when the connection to the database is lost during update"""


class ExitRequested(Exception):
    """This exception is thrown if the addon is shut down by Kodi or by another same addon"""
