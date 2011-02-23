import os
import re
import sys
import unittest

sys.path.append("../script.module.danishaddons/")
sys.path.append("../script.module.danishaddons/xbmcstubs/")

import xbmcplugin
import xbmcaddon
import danishaddons
import addon

class TestGametestDk(unittest.TestCase):

    def setUp(self):
        danishaddons.init([os.getcwd(), '12345', ''])
        xbmcplugin.items = list()

    def testShowOverview(self):
        addon.showOverview()

        self.assertNotEquals(0, len(xbmcplugin.items), msg = 'Expected at least one ListItem')

if __name__ == '__main__':
    unittest.main()
    