"""
    Plugin for Launching HyperSpin
"""


import sys
import os

# plugin constants
__plugin__ = "HyperSpin"
__author__ = "Francesco Dicarlo"

__version__ = "1"

if ( __name__ == "__main__" ):
    import resources.lib.hyperspin_plugin as plugin
    plugin.Main()

