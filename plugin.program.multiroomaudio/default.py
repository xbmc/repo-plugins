"""
    Plugin for True Multiroom Audio & Video
"""

# main imports
import sys
import os

# plugin constants
__plugin__ = "plugin.program.multiroomaudio"
__author__ = "teshephe"
__url__ = ""
__svn_url__ = ""
__credits__ = "VortexRotor, XBMC Team, VLC, Author of Launcher Plugin"
__version__ = "1.1.1"


if ( __name__ == "__main__" ):
    import resources.lib.multiroomaudio_plugin as plugin
    plugin.Main()
sys.modules.clear()
