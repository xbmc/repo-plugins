# -*- coding: utf-8 -*-
"""Convert kodi settings to python types.

get_string / set_string - get and set settings without conversion.
get_boolean / set_boolean - get and set boolean settings using python booleans.
get_number / set_number: get and set number settings, converting to and from numbers.
"""


def str2bool(string):
    """Convert the words "tru" and "false" into the corresponding boolean values."""
    return {"true": True, "false": False}[string]


def bool2str(boolean):
    """Convert a boolean value into the word "true" or "false"."""
    if boolean:
        return "true"
    return "false"


def str2num(string):
    """Convert a number string into a number."""
    return float(string)


def num2str(num):
    """Convert a number into a string."""
    return str(num)


class Settings(object):
    def __init__(self, handle, xbmc, xbmcplugin):
        """Create a settings object for this addon."""
        self.handle = handle
        self.xbmc = xbmc
        self.xbmcplugin = xbmcplugin

    def get_string(self, key):
        """Get string setting key and convert it to a Python boolean."""
        return self.xbmcplugin.getSetting(self.handle, key)

    def set_string(self, key, value):
        """Set string setting key."""
        self.xbmcplugin.setSetting(self.handle, key, value)

    def get_boolean(self, key):
        """Get boolean setting key and convert it to a Python boolean."""
        return str2bool(self.xbmcplugin.getSetting(self.handle, key))

    def set_boolean(self, key, value):
        """Set boolean setting key."""
        self.xbmcplugin.setSetting(self.handle, key, bool2str(value))

    def get_number(self, key):
        """Get number setting key and convert it to a Python number.

        This will work for all setting types that are stored as a number, e.g. selectors, sliders, etc.
        """
        return str2num(self.xbmcplugin.getSetting(self.handle, key))

    def set_number(self, key, value):
        """Set a number setting key."""
        self.xbmcplugin.setSetting(self.handle, key, num2str(value))

    # TODO once I need them:
    # - date
    # - time
    # - ip