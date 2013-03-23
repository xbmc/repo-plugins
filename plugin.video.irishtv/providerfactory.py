# -*- coding: utf-8 -*-
import xbmc
from xbmc import log
from xbmcaddon import Addon
from loggingexception import LoggingException

from rte import RTEProvider
from tv3 import TV3Provider
from aertv import AerTVProvider
from tg4 import TG4Provider
# Provider names

__providers__ = [RTEProvider(), TV3Provider(), AerTVProvider(), TG4Provider()]


def getProvider(name):
    log("ProviderFactory(" + str(name) + ")", xbmc.LOGDEBUG)

    for provider in __providers__:
        if name == provider.GetProviderId():
            return provider

    return None

def getProviderList():
    return __providers__
