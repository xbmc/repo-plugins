__author__ = 'bromix'

def on_keyboard_input(title, default='', hidden=False):
    raise NotImplementedError()

try:
    from .system.xbmc.xbmc_input import *
except ImportError:
    from .system.mock.mock_input import *
    pass
