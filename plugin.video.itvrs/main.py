# -*- coding: utf-8 -*-

from resources.lib import kodilogging
from resources.lib import plugin

import logging
import xbmcaddon

ADDON = xbmcaddon.Addon()
kodilogging.config()

plugin.run()
