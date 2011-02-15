import os
import sys
import unittest

sys.path.append("../script.module.danishaddons/")
sys.path.append("../script.module.danishaddons/xbmcstubs/")
sys.path.append("../script.module.feedparser/")

import xbmc
import xbmcplugin
import danishaddons
import addon

class TestDrDkBonanza(unittest.TestCase):

    def setUp(self):
        danishaddons.init([os.getcwd(), '12345', ''])
        xbmcplugin.items = list()

    def testSearch(self):
        xbmc.textValue = 'bamse'
        addon.search()

        self.assertNotEquals(0, len(xbmcplugin.items), msg = 'Expected at least one ListItem')

    def testShowCategories(self):
        addon.showCategories()

        self.assertNotEquals(0, len(xbmcplugin.items), msg = 'Expected at least one ListItem')
        self.assertNotEquals(-1, xbmcplugin.items[0].url.find('mode=search'))
        self.assertNotEquals(-1, xbmcplugin.items[1].url.find('mode=recommend'))
        self.assertNotEquals(-1, xbmcplugin.items[0].url.find('mode=search'))

if __name__ == '__main__':
    unittest.main()
    