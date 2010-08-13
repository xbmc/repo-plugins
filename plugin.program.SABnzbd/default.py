"""
    Plugin for adding nzb files to sabnzbd from RSS feeds
"""

# main imports
import sys
import xbmcaddon

# plugin constants
__plugin__ = "SABnzbd Plugin"
__author__ = "switch, Kricker, maruchan"
__url__ = "http://sabnzbd.org"
__svn_url__ = ""
__credits__ = "Team SABnzbd & Team XBMC"
__version__ = "2.1.3"

__settings__ = xbmcaddon.Addon(id='plugin.program.SABnzbd')
__language__ = __settings__.getLocalizedString

if ( __name__ == "__main__" ):
    print 'arguments:%s' % sys.argv[1:]
    from nzb import item_list as plugin
    plugin.Main()
