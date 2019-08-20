#!/usr/bin/python

import neverwise as nw
import os
import xbmcaddon
import xbmcgui

addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')
line1 = 'ITVRS - Radio Ice'
line2 = '  '
line3 = 'Use Left Menu To Pause Or Stop'

xbmcgui.Dialog().ok(addonname, line1, line2, line3)


class itvrs_radio_ice:

    def __init__(self):

        li = nw.createListItem(nw.addonName,
                               thumbnailImage='{0}/resources/icon.png'.format(os.path.dirname(os.path.abspath(__file__))),
                               streamtype='music',
                               infolabels={'title': 'ITVRS - Radio Ice'})
        xbmc.Player().play('http://stream.zeno.fm/3611cwn8mbruv', li)


rr = itvrs_radio_ice()
del rr
