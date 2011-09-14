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
        danishaddons.init(['.', '12345', ''])
        xbmcplugin.items = list()

    def testShowOverview(self):
	xbmcaddon.strings[30000] = 'Date: %s'
        addon.showOverview()

        self.assertNotEquals(0, len(xbmcplugin.items), msg = 'Expected at least one ListItem')

if __name__ == '__main__':
    unittest.main()
    
