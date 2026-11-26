# -*- coding: utf-8 -*-
'''Test helpers: the Kodi modules are stubbed so the library code runs outside Kodi.'''

import os
import sys
import types

ADDON_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if ADDON_ROOT not in sys.path:
    sys.path.insert(0, ADDON_ROOT)

if 'xbmc' not in sys.modules:
    xbmc = types.ModuleType('xbmc')
    xbmc.log = lambda *args, **kwargs: None
    sys.modules['xbmc'] = xbmc
