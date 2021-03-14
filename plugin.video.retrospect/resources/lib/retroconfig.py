# SPDX-License-Identifier: GPL-3.0-or-later

import os
import xml.dom.minidom

import xbmc
import xbmcvfs

# Code to map the old translatePath
try:
    translatePath = xbmcvfs.translatePath
except AttributeError:
    translatePath = xbmc.translatePath

from .version import Version


class Config:
    """Class with all the configuration constants"""

    def __init__(self):
        pass

    try:
        import xbmcaddon
        # calling xbmcaddon.Addon() only works on newer XBMC's. Should see if it keeps working
        # if not, then the addonId should be hard coded here.
        __addon = xbmcaddon.Addon()
        __path = __addon.getAddonInfo('path')
        __addon = None  # : Free up the static variable to make sure it is garbage collected
        pathDetection = "addon.getAddonInfo('path')"
    except:
        # This was a xbmc.LOGWARNING, but that is not allowed according to the Kodi add-on rules.
        xbmc.log("Retrospect: using os.getcwd()", xbmc.LOGDEBUG)
        __path = os.getcwd()
        pathDetection = "os.getcwd()"

    if isinstance(__path, bytes):
        # the Kodi libs return unicode info, so we need to convert this
        #noinspection PyArgumentEqualDefault
        __path = __path.decode('utf-8')

    # get rootDir, addonsDir and profileDir
    rootDir = __path.replace(";", "").rstrip(os.sep)         # : The root directory where Retrospect resides.
    addonDir = os.path.split(rootDir)[-1]                    # : The add-on directory of Kodi.
    rootDir = os.path.join(rootDir, '')                      # : The root directory where Retrospect resides.
    icon = os.path.join(rootDir, "resources", "media", "icon.png")
    fanart = os.path.join(rootDir, "resources", "media", "fanart.jpg")
    poster = os.path.join(rootDir, "resources", "media", "poster.jpg")

    # determine the profile directory, where user data is stored.
    if xbmc.getCondVisibility("system.platform.xbox"):
        profileDir = os.path.join(translatePath("special://profile/script_data/"), addonDir)
        profileUri = os.path.join("special://profile/script_data/", addonDir)
    else:
        profileDir = os.path.join(translatePath("special://profile/addon_data/"), addonDir)
        profileUri = os.path.join("special://profile/addon_data/", addonDir)

    # the XBMC libs return unicode info, so we need to convert this
    if isinstance(profileDir, bytes):
        profileDir = profileDir.decode('utf-8')
    if isinstance(profileUri, bytes):
        profileUri = profileUri.decode('utf-8')

    cacheDir = os.path.join(profileDir, 'cache', '')         # : The cache directory.
    favouriteDir = os.path.join(profileDir, 'favourites')    # : The favourites directory

    appName = "Retrospect"                                   # : Name of the XOT application (could be overwritten from the addon.xml)
    cacheValidTime = 7 * 24 * 3600                           # : Time the cache files are valid in seconds.

    logLevel = 10                                            # : Minimum log level that is being logged. (from logger.py) Defaults to Debug
    logFileNameAddon = "retrospect.log"                      # : Filename of the log file of the plugin

    # must be single quotes for build script
    __addonXmlPath = os.path.join(rootDir, 'addon.xml')
    __addonXmlcontents = xml.dom.minidom.parse(__addonXmlPath)
    for addonentry in __addonXmlcontents.getElementsByTagName("addon"):
        addonId = str(addonentry.getAttribute("id"))          # : The ID the addon has in Kodi (from addon.xml)
        __version = addonentry.getAttribute("version")        # : The Version of the addon (from addon.xml) in text
        version = Version(version=__version)                  # : The Version of the addon (from addon.xml)
        #noinspection PyRedeclaration
        appName = str(addonentry.getAttribute("name"))        # : The name from the addon (from addon.xml)

    updateUrl = "https://api.github.com/repos/retrospect-addon/plugin.video.retrospect/releases"

    textureMode = "Resources"                                 # : The mode for the textures: Local, Remote, Cached or Resources
    textureUrl = "https://cdn.rieter.net/" \
                 "resource.images.retrospect/resources"       # : The URL for the remote texture location
    textureResource = "resource.images.retrospect"            # : The resource add-on to use for textures

    logSenderApi = "1786d25d01392d572659bba76f95174f"         # : The Retrospect logsender API (Google Shortner API or PasteBinAPI)
