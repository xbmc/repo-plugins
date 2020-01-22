#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcaddon

__addon__ = xbmcaddon.Addon()


def useApiCache():
    return __addon__.getSetting('useApiCache') == 'true'


def cacheExp():
    return int(__addon__.getSetting('cacheExp'))


def useWidevine():
    return __addon__.getSetting("drmToUse") == "0"


def debugLog():
    return __addon__.getSetting('debugLog') == 'true'
