__author__ = 'bromix'

from ...abstract_provider import AbstractProvider
from ...log import *


class MockAbstractProvider(AbstractProvider):
    def __init__(self, plugin=None):
        AbstractProvider.__init__(self, plugin)
        pass

    def refresh_container(self):
        log("called 'refresh_container'")
        pass

    def show_notification(self, message, header='', image_uri='', time_milliseconds=5000):
        log('=======NOTIFICATION=======')
        log('Message  : %s' % message)
        log('header   : %s' % header)
        log('image_uri: %s' % image_uri)
        log('Time     : %d' % time_milliseconds)
        log('==========================')
        pass

    pass

