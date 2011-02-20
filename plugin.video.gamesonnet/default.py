#
# Imports
#

import sys

#
# Play
#
if ( "action=play" in sys.argv[ 2 ] ):
    import resources.lib.gamesonnet_play as plugin
#
# Main menu
#
else :
    import resources.lib.gamesonnet_list as plugin

plugin.Main()
