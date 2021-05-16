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
    THUMB_PATH = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'images')

    URL_BASE = "https://www.la7.it"
    URL_BASE_LA7D = "https://www.la7.it/la7d"
    URL_LIVE_LA7 = "https://www.la7.it/dirette-tv"
    URL_LIVE_LA7D = "https://www.la7.it/live-la7d"
    URL_TGLA7D = "https://tg.la7.it/listing/tgla7d"
    URL_RIVEDILA7 = "https://www.la7.it/rivedila7/0/la7"
    URL_RIVEDILA7D = "https://www.la7.it/rivedila7/0/la7d"
    URL_PROGRAMMI = "https://www.la7.it/programmi"
    URL_PROGRAMMILA7D = "https://www.la7.it/programmi-la7d"
    URL_TUTTI_PROGRAMMI = "https://www.la7.it/tutti-i-programmi"
    URL_TECHE_LA7 = "https://www.la7.it/i-protagonisti"

    FILTRO_OMNIBUS = 'Omnibus News'

    # DRM config
    DRM = 'com.widevine.alpha'
    DRM_PROTOCOL = 'mpd'
    KEY_WIDEVINE = "https://la7.prod.conax.cloud/widevine/license"
    HEADERS_SET = {
        'host_token': 'pat.la7.it',
        'host_license': 'la7.prod.conax.cloud',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        'accept': '*/*',
        'accept-language': 'en,en-US;q=0.9,it;q=0.8',
        'dnt': '1',
        'te': 'trailers',
        'origin': 'https://www.la7.it',
        'referer': 'https://www.la7.it/',
    }

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
        self.GIORNO = str(G.PARAMS.get("giorno", ""))
        self.LINK = str(G.PARAMS.get("link", ""))
        self.TITOLO = str(G.PARAMS.get("titolo", ""))
        self.THUMB = str(G.PARAMS.get("thumb", ""))
        self.PLOT = str(G.PARAMS.get("plot", ""))
        self.PLAY = str(G.PARAMS.get("play", ""))
        self.PAGENUM = 0
        self.LIST_PROGRAMMI = []
        self.OMNIBUS_NEWS = False

        if self.IS_ADDON_FIRSTRUN:
            # Global variables that do NOT need to be updated at every addon run
            self.ADDON_ID = self.ADDON.getAddonInfo('id')
            self.PLUGIN_NAME = self.ADDON.getAddonInfo('name')
            self.ICON = self.ADDON.getAddonInfo('icon')
            self.ADDON_DATA_PATH = self.ADDON.getAddonInfo('path')  # Add-on folder
            self.DATA_PATH = self.ADDON.getAddonInfo('profile')  # Add-on user data folder
            self.PLUGIN_HANDLE = int(argv[1])


def parameters_string_to_dict(parameters):
    # xbmc.log('PARAMETERS------: '+str(parameters),xbmc.LOGINFO)
    param_dict = dict(parse_qsl(parameters[1:]))
    return param_dict


# We initialize an instance importable of GlobalVariables from run_addon.py,
# where G.init_globals() MUST be called in the addon entry point.
G = GlobalVariables()
