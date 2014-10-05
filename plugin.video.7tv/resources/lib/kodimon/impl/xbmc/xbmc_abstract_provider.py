__author__ = 'bromix'

import xbmc

from ...abstract_provider import AbstractProvider


class XbmcAbstractProvider(AbstractProvider):
    def __init__(self, plugin=None):
        AbstractProvider.__init__(self, plugin)
        pass

    def refresh_container(self):
        xbmc.executebuiltin("Container.Refresh")
        pass

    pass
