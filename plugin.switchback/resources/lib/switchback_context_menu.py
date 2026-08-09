import xbmc
from bossanova808.logger import Logger


# This is 'main'...
# noinspection PyUnusedLocal
def run(args):
    Logger.start(f"(Context Menu) {args}")
    if args[0] == "switchback":
        xbmc.executebuiltin("PlayMedia(plugin://plugin.switchback/?mode=switchback,resume)")
    else:
        xbmc.executebuiltin("RunAddon(plugin.switchback)")
    Logger.stop("(Context Menu)")
