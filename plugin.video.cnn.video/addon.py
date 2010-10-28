"""
    Plugin for streaming video content from CNN
"""

# main imports
import sys


if ( __name__ == "__main__" ):
    # view changelog/readme/credits/updates
    if ( sys.argv[ 1 ] in [ "view=updates", "view=changelog", "view=readme", "view=credits" ] ):
        from resources.lib.utils import Viewer
        Viewer( kind=sys.argv[ 1 ].split( "=" )[ 1 ] )
    elif ( not sys.argv[ 2 ] ):
        # we need to check compatible()
        from resources.lib.utils import check_compatible
        # only run if compatible
        if ( check_compatible() ):
            import resources.lib.categories as plugin
            plugin.Main()
    elif( "category=" in sys.argv[ 2 ] ):
        import resources.lib.categories as plugin
        plugin.Main()
    else:
        import resources.lib.videos as plugin
        plugin.Main()
