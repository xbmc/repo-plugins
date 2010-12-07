import sys
import os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import urllib

# plugin handle
handle = int(sys.argv[1])

def addLink(name,url,iconimage):
        retval=True
        liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        retval = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return retval

def show_channellist():
    Addon = xbmcaddon.Addon( id="plugin.video.nederland24")
    channel_icons_path = os.path.join(Addon.getAddonInfo("path"),"icons")

    addLink("101TV", "http://livestreams.omroep.nl/npo/101tv-bb", os.path.join(channel_icons_path, "101tv.png"))
    addLink("Consumenten 24", "http://livestreams.omroep.nl/npo/consumenten24-bb", os.path.join(channel_icons_path, "consumenten24.png"))
    addLink("Cultura 24", "http://livestreams.omroep.nl/npo/cultura24-bb", os.path.join(channel_icons_path, "cultura24.png"))
    addLink("Geschiedenis 24", "http://livestreams.omroep.nl/npo/geschiedenis24-bb", os.path.join(channel_icons_path, "geschiedenis24.png"))
    addLink("Best 24", "http://livestreams.omroep.nl/npo/best24-bb", os.path.join(channel_icons_path, "best24.png"))
    addLink("Holland Doc 24", "http://livestreams.omroep.nl/npo/hollanddoc24-bb", os.path.join(channel_icons_path, "hollanddoc24.png"))
    addLink("Humor TV 24", "http://livestreams.omroep.nl/npo/humortv24-bb", os.path.join(channel_icons_path, "humortv24.png"))
    addLink("Journaal 24", "http://livestreams.omroep.nl/nos/journaal24-bb", os.path.join(channel_icons_path, "journaal24.png"))
    addLink("Politiek 24", "http://livestreams.omroep.nl/nos/politiek24-bb", os.path.join(channel_icons_path, "politiek24.png"))
    addLink("Spirit 24", "http://livestreams.omroep.nl/npo/spirit24-bb", os.path.join(channel_icons_path, "spirit24.png"))
    addLink("Sterren 24", "http://livestreams.omroep.nl/npo/sterren24-bb", os.path.join(channel_icons_path, "sterren24.png"))
    addLink("Z@ppelin/Familie 24", "http://livestreams.omroep.nl/npo/familie24-bb", os.path.join(channel_icons_path, "familie24.png"))
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
 
ok = show_channellist()

