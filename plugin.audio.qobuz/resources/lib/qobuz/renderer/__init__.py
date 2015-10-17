'''
    qobuz.renderer
    ~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from renderer.xbmc import QobuzXbmcRenderer as OurRenderer


def renderer(nType, params=None):
    return OurRenderer(nType, params)
