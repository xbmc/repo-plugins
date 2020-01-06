import sys, xbmc, xbmcgui, xbmcaddon, json
ADDON_ID = xbmcaddon.Addon().getAddonInfo('id')
ICON = xbmcaddon.Addon().getAddonInfo('icon')
asset = [{'type':'browse','logo':ICON,'path':'plugin://plugin.video.plutotv/?mode=1&name=Lineup','label':'Pluto.TV LiveTV','description':'LiveTV from Pluto.TV '}]
xbmcgui.Window(10000).setProperty('PseudoTV_Recommend.%s'%(ADDON_ID), json.dumps(asset))
sys.exit()

####### README #######
# type: 
#       file = single item
#       directory = single folder containing links (recursive).
#       browse = special case, seek example online.
#       network = special case, seek example online.
