"""
Import switch for the real deal or for the mock.
"""
from abstract_api import *
try:
    from impl.xbmc.xbmc_api import *
    from impl.xbmc.xbmc_plugin import XbmcPlugin as Plugin
    from impl.xbmc.xbmc_abstract_provider import XbmcAbstractProvider as AbstractProvider
except ImportError, ex:
    from impl.mock.mock_api import *
    from impl.mock.mock_plugin import MockPlugin as Plugin
    from impl.mock.mock_abstract_provider import MockAbstractProvider as AbstractProvider
    pass


class KodimonException(Exception):
    pass


class RegisterPath(object):
    def __init__(self, re_path):
        self._kodimon_re_path = re_path
        pass

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            # only use a wrapper if you need extra code to be run here
            return func(*args, **kwargs)
        wrapper.kodimon_re_path = self._kodimon_re_path
        return wrapper

    pass


from base_item import BaseItem
from video_item import VideoItem
from audio_item import AudioItem
from directory_item import DirectoryItem