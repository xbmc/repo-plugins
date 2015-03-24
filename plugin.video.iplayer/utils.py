#!/usr/bin/python

import os, sys, re
import xbmc, xbmcaddon

__addonid__ = "plugin.video.iplayer"
__plugin_handle__ = int(sys.argv[1])

enhanceddebugging = False

def get_addoninfo():
    global enhanceddebugging

    dict = {}
    dict["id"]       = __addonid__
    dict["addon"]    = xbmcaddon.Addon(__addonid__)
    dict["language"] = dict["addon"].getLocalizedString
    dict["version"]  = dict["addon"].getAddonInfo("version")
    dict["path"]     = dict["addon"].getAddonInfo("path")
    dict["profile"]  = xbmc.translatePath(dict["addon"].getAddonInfo('profile'))

    enhanceddebugging = (dict["addon"].getSetting('enhanceddebug') == 'true')

    return dict

def get_os():
    try: xbmc_os = os.environ.get("OS")
    except: xbmc_os = "unknown"
    return xbmc_os

def log(message,loglevel=xbmc.LOGNOTICE):
    if enhanceddebugging:
      xbmc.log(encode("%s: %s" % (__addonid__,message)),level=xbmc.LOGNOTICE)
    else:
      xbmc.log(encode("%s: %s" % (__addonid__,message)),level=loglevel)

def encode(string):
    return string.encode('UTF-8','replace')

def xml_strip_namespace(xml):
    # remove namespace
    xml = re.sub(' xmlns="[^"]+"', '', xml, count = 1)
    return xml