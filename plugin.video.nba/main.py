import xbmc,xbmcaddon
import sys,os

my_addon = xbmcaddon.Addon('plugin.video.nba')
addon_dir = xbmc.translatePath( my_addon.getAddonInfo('path') ).decode('utf-8')

sys.path.append(os.path.join(addon_dir, 'src'))

from leaguepass import *
