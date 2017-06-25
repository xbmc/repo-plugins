"""
    TED Talks
    rwparris2
"""
import sys
import resources.lib.plugin as plugin
import resources.lib.settings as settings
import resources.lib.model.arguments as arguments
import os
import xbmc
import xbmcaddon

LIB_DIR = xbmc.translatePath(
    os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'lib'))
sys.path.append(LIB_DIR)

if __name__ == "__main__":
    plugin.init()
    settings.init()
    import resources.lib.ted_talks as ted_talks

    args_map = arguments.parse_arguments(sys.argv[2])
    ted_talks.Main(args_map=args_map).run()

sys.modules.clear()
