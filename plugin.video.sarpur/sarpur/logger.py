#!/usr/bin/env python
# encoding: UTF-8

import xbmc
import sarpur

def log(message):
    if sarpur.LOGGING_ENABLED:
        xbmc.log(message)
