# Everything that is to be globally accessible must be defined in this module.
# Using the Kodi reuseLanguageInvoker feature, only the code in the addon.py module will be run every time the addon is called,
# all other modules (imports) are initialized only on the first invocation of the add-on.

from urllib.parse import parse_qsl

import os
import xbmcaddon


class GlobalVariables(object):
    """Encapsulation for global variables to work around quirks with
    Kodi's reuseLanguageInvoker behavior"""
    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=invalid-name, too-many-instance-attributes

    FANART_PATH = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'fanart.jpg')
    THUMB_PATH = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'media')

    def __init__(self):
        """Do nothing on constructing the object"""
        # The class initialization (GlobalVariables) will only take place at the first initialization of this module
        # on subsequent add-on invocations (invoked by reuseLanguageInvoker) will have no effect.
        # Define here only the variables necessary for the correct initialization of the other project modules
        self.IS_ADDON_FIRSTRUN = None
        self.ADDON = None
        self.ADDON_DATA_PATH = None
        self.DATA_PATH = None

    def init_globals(self, argv):
        """Initialized globally used module variables. Needs to be called at start of each plugin instance!"""
        # IS_ADDON_FIRSTRUN: specifies if the add-on has been initialized for the first time
        #                    (reuseLanguageInvoker not used yet)
        self.IS_ADDON_FIRSTRUN = self.IS_ADDON_FIRSTRUN is None
        # xbmcaddon.Addon must be created at every instance otherwise it does not read any new changes to the settings
        self.ADDON = xbmcaddon.Addon()
        self.LANGUAGE = self.ADDON.getLocalizedString
        self.PARAMS = parameters_string_to_dict(argv[2])
        self.MODE = str(G.PARAMS.get("mode", ""))

        if self.IS_ADDON_FIRSTRUN:
            # Global variables that do NOT need to be updated at every addon run
            self.ADDON_ID = self.ADDON.getAddonInfo('id')
            self.PLUGIN_NAME = self.ADDON.getAddonInfo('name')
            self.ICON = self.ADDON.getAddonInfo('icon')
            self.ADDON_DATA_PATH = self.ADDON.getAddonInfo('path')  # Add-on folder
            self.DATA_PATH = self.ADDON.getAddonInfo('profile')  # Add-on user data folder
            self.PLUGIN_HANDLE = int(argv[1])


def parameters_string_to_dict(parameters):
    param_dict = dict(parse_qsl(parameters[1:]))
    return param_dict


# We initialize an instance importable of GlobalVariables from run_addon.py,
# where G.init_globals() MUST be called in the addon entry point.
G = GlobalVariables()
