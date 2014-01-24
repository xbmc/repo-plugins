from resources.lib.constants import *


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def show_notification(title, message, duration=10000):
    xbmc.executebuiltin('Notification(%s, %s, %d)' % (title, message, duration))
