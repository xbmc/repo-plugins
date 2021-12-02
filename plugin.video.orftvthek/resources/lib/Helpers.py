#!/usr/bin/python
# -*- coding: utf-8 -*-

from kodi_six.utils import py2_encode, py2_decode

import xbmc
import xbmcgui
import xbmcaddon
import sys

PY3 = sys.version_info.major >=3
if PY3:
    from urllib.parse import unquote, urlencode
    from urllib.request import urlopen as OpenRequest
    from urllib.request import Request as HTTPRequest
    from urllib.error import HTTPError
else:
    from urllib import unquote, urlencode
    from urllib2 import HTTPError
    from urllib2 import urlopen as OpenRequest
    from urllib2 import Request as HTTPRequest


def unqoute_url(url):
    try:
        return unquote(url)
    except:
        return unquote(url.encode('utf-8'))


def build_kodi_url(parameters):
    return sys.argv[0] + '?' + encode_parameters(parameters)


def encode_parameters(parameters):
    parameters = { k: v if v is not None else ""
                   for k, v in parameters.items() }
    try:
        return urlencode(parameters)
    except:
        parameters = {k: unicode(v).encode("utf-8") for k, v in list(parameters.items())}
        return urlencode(parameters)


def url_get_request(url, authorization=False):
    if authorization:
        request = HTTPRequest(url)
        request.add_header('Authorization', 'Basic %s' % authorization)
    else:
        request = url
    return OpenRequest(request)


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def debugLog(message, loglevel=xbmc.LOGDEBUG):
    output = py2_encode(message)
    xbmc.log("[plugin.video.orftvthek] %s" % output, level=loglevel)


def userNotification(message, title="ORF TVThek"):
    output = py2_encode(message)
    xbmcgui.Dialog().notification(title, output, icon=xbmcgui.NOTIFICATION_ERROR)
