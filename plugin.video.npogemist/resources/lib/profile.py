# -*- coding: utf-8 -*-
"""Manage Kodi profile data.

Store python objects using set_data
Retrieve python objects using get_data.

Data is pickled into a file in the plugin profile directory, with the filename provided.
"""
import os.path
import pickle

FILE_NAME_FORMAT = "{0}.pkl"

class Profile(object):
    def __init__(self, addon, xbmc):
        """Create a profile for this addon. Create directory if necessary."""
        self.xbmc = xbmc
        self.profile_path = xbmc.translatePath(addon.getAddonInfo("profile")).decode("utf-8")
        if not os.path.isdir(self.profile_path):
            os.makedirs(self.profile_path)

    def get_data(self, data_key):
        """Return the data structure stored under this key."""
        filename = os.path.join(self.profile_path, FILE_NAME_FORMAT.format(data_key))
        try:
            with open(filename, "rb") as f:
                data = pickle.load(f)
                self.xbmc.log(u"retrieving {0} from {1}".format(data, filename))
                return data
        except IOError:
            return None

    def set_data(self, data_key, data):
        """Store the data structure 'data' under this key.

        If it fails, don't crash.
        """
        filename = os.path.join(self.profile_path, FILE_NAME_FORMAT.format(data_key))
        self.xbmc.log(u"storing {0} in {1}".format(data, filename))
        try:
            with open(filename, "wb") as f:
                pickle.dump(data, f)
        except IOError:
            pass
