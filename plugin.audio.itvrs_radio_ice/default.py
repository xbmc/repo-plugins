#!/usr/bin/python

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
		
        xbmc.Player().play('http://stream.zeno.fm/3611cwn8mbruv')

rr = itvrs_radio_ice()
del rr
