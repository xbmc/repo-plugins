import os
import sys
import unittest

sys.path.append("../script.module.danishaddons/")
sys.path.append("../script.module.danishaddons/xbmcstubs/")

import xbmc
import xbmcplugin
import xbmcaddon
import danishaddons
import addon

class TestDrDkNetradio(unittest.TestCase):

    def setUp(self):
        danishaddons.init([os.getcwd(), '12345', ''])
        xbmcplugin.items = list()

    def testShowChannelsHighQuality(self):
        xbmcaddon.settings['quality'] = 'High'
        addon.showChannels()
        self.assertNotEquals(0, len(xbmcplugin.items), msg = 'Expected at least one ListItem')
        self.assertEquals('P1', xbmcplugin.items[0].title)
        self.assertEquals('P2', xbmcplugin.items[1].title)
        self.assertEquals('P3', xbmcplugin.items[2].title)

        self.assertNotEqual(-1, xbmcplugin.items[0].url.find('_128.asx'))

    def testShowChannelsMediumQuality(self):
        xbmcaddon.settings['quality'] = 'Medium'
        addon.showChannels()
        self.assertNotEquals(0, len(xbmcplugin.items), msg = 'Expected at least one ListItem')
        self.assertEquals('P1', xbmcplugin.items[0].title)
        self.assertEquals('P2', xbmcplugin.items[1].title)
        self.assertEquals('P3', xbmcplugin.items[2].title)

        self.assertNotEqual(-1, xbmcplugin.items[0].url.find('_64.asx'))

    def testShowChannelsLowQuality(self):
        xbmcaddon.settings['quality'] = 'Low'
        addon.showChannels()
        self.assertNotEquals(0, len(xbmcplugin.items), msg = 'Expected at least one ListItem')
        self.assertEquals('P1', xbmcplugin.items[0].title)
        self.assertEquals('P2', xbmcplugin.items[1].title)
        self.assertEquals('P3', xbmcplugin.items[2].title)

        self.assertNotEqual(-1, xbmcplugin.items[0].url.find('_32.asx'))

    def testPlayFirstStream(self):
        xbmcaddon.settings['quality'] = 'High'
        addon.showChannels()

        self.assertNotEquals(0, len(xbmcplugin.items), msg = 'Expected at least one ListItem')
        index = xbmcplugin.items[0].url.find('url=') + 4
        url = xbmcplugin.items[0].url[index:]

        xbmcplugin.items = list()
        addon.playStream(url)
        self.assertEqual('http://wmscr1.dr.dk/e02ch01m?wmcontentbitrate=300000', xbmcplugin.items[0].url)


if __name__ == '__main__':
    unittest.main()
    