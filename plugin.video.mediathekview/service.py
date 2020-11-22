# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
The main service module

MIT License

Copyright (c) 2017-2020, Leo Moll
"""



# -- Imports ------------------------------------------------
from resources.lib.service import MediathekViewService

# -- Main Code ----------------------------------------------
if __name__ == '__main__':
    SERVICE = MediathekViewService()
    SERVICE.init()
    SERVICE.run()
    SERVICE.exit()
    del SERVICE
