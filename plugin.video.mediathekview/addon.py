# -*- coding: utf-8 -*-
"""
The main addon module

Copyright (c) 2017-2018, Leo Moll
SPDX-License-Identifier: MIT

"""

# -- Imports ------------------------------------------------
from resources.lib.plugin import MediathekViewPlugin

# -- Main Code ----------------------------------------------
if __name__ == '__main__':
    PLUGIN = MediathekViewPlugin()
    PLUGIN.init()
    PLUGIN.run()
    PLUGIN.exit()
    del PLUGIN
