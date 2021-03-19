# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

import importlib
from codequick import run


def main():
    """Entry point function executed by Kodi for each menu of the addon"""

    # Let CodeQuick check for functions to register and call
    # the correct function according to the Kodi URL
    exception = run()
    if isinstance(exception, Exception):
        main = importlib.import_module('resources.lib.main')
        main.error_handler(exception)


if __name__ == "__main__":
    main()
