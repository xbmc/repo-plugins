__author__ = 'bromix'

try:
    from .kodi.context import KodiContext as Context
except ImportError, ex:
    from .mock.context import MockContext as Context
    pass