#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon

def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def debugLog(message,type):
    output = "[ORF TVTHEK] ("+type+") "+message;
    xbmc.log(msg=output, level=xbmc.LOGDEBUG)

def notifyUser(message):
    addon = xbmcaddon.Addon()
    name = addon.getAddonInfo('name')
    icon = addon.getAddonInfo('icon')
    xbmc.executebuiltin('Notification(%s, %s, %s, %s)'%(name,message, "", icon))
