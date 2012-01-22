"""
    Plugin for Launching programs
"""

# main imports
import sys
import os

# plugin constants
__plugin__ = "Advanced Launcher"
__author__ = "Angelscry"
__url__ = "http://code.google.com/p/xbmc-advanced-launcher/"
__svn_url__ = "http://xbmc-advanced-launcher.googlecode.com/svn/trunk/plugin.program.advanced.launcher/"
__credits__ = "Leo212, CinPoU, JustSomeUser, Zerqent, Zosky, Atsumori"
__version__ = "1.7.4"

if ( __name__ == "__main__" ):
    import resources.lib.launcher_plugin as plugin
    plugin.Main()

