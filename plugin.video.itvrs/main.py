# -*- coding: utf-8 -*-

from resources.lib import itvrs

import logging
import xbmcaddon


ADDON = xbmcaddon.Addon()
kodilogging.config()


if __name__ == '__main__':
    itvrs.run()
    
