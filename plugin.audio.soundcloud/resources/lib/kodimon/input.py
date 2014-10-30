__author__ = 'bromix'

try:
    from .impl.xbmc.xbmc_input import *
except ImportError:
    from .impl.mock.mock_input import *
    pass
