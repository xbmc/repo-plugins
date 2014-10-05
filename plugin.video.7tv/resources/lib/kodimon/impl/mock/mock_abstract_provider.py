__author__ = 'bromix'

from ...abstract_provider import AbstractProvider


class MockAbstractProvider(AbstractProvider):
    def __init__(self, plugin=None):
        AbstractProvider.__init__(self, plugin)
        pass

    def refresh_container(self):
        from ... import log
        log("called 'refresh_container'")
        pass

    pass

