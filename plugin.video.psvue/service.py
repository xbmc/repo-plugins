from resources.lib.mainservice import MainService
import xbmcaddon

if xbmcaddon.Addon().getSetting(id='disable_epg') == 'false':
    MainService()
