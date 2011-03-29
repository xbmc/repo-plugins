import os
import sys
import unittest

sys.path.append("../script.module.danishaddons/")
sys.path.append("../script.module.danishaddons/xbmcstubs/")

import xbmc
import xbmcplugin
import danishaddons
import addon

class TestDrDkLive(unittest.TestCase):

    def setUp(self):
        danishaddons.init(['.', '12345', ''])
        xbmcplugin.items = list()

    def testShowHighQualityChannels(self):
        danishaddons.ADDON.setSetting('quality', 'high')
        addon.showChannels()
        self.assertEquals(len(addon.CHANNELS), len(xbmcplugin.items), msg = 'Got unexpected number of ListItem')

        for idx, channel in enumerate(addon.CHANNELS):
            item = xbmcplugin.items[idx]
            self.assertEquals(channel['name'], item.title)


if __name__ == '__main__':
    unittest.main()
