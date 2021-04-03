# coding: utf-8
from __future__ import print_function, division, absolute_import

import re

try:
    import xbmc
except ImportError:
    xbmc = None


def major_version():
    verstr = xbmc.getInfoLabel('System.BuildVersion')
    match = re.match(r'(\d+)\.', verstr)
    if match:
        return int(match.group(1))
    return None


def log(msg):
    if xbmc:
        xbmc.log(msg)
    else:
        print(msg)
