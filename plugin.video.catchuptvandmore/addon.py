# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import importlib
from codequick import run
from resources.lib.kodi_utils import import_needed_module


def main():
    """Entry point function executed by Kodi for each menu of the addon

    """

    """
    Before calling run() function of
    codequick, we need to check if there
    is any module to load on the fly
    """
    import_needed_module()

    """
    Then we let CodeQuick check for
    functions to register and call
    the correct function according to
    the Kodi URL
    """
    exception = run()
    if isinstance(exception, Exception):
        main = importlib.import_module('resources.lib.main')
        main.error_handler(exception)


if __name__ == "__main__":
    main()
