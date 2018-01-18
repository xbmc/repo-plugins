# -*- coding: utf-8 -*-

import xbmcaddon

addon = xbmcaddon.Addon()

if __name__ == '__main__':
    addon.setSetting('startup', 'true')
