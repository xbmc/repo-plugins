import xbmc, xbmcgui, os, xbmcaddon, xbmcplugin, urllib2, re

__settings__ = xbmcaddon.Addon()
home = __settings__.getAddonInfo('path')
addon_handle = int(sys.argv[1])
icon = xbmc.translatePath(os.path.join(home, 'icon.png'))
li = xbmcgui.ListItem ('Live Stream')
li.setArt({ 'thumb': icon })
li.setInfo('video', {'plot':'Iran International TV Live Stream'})

livePageUrl = 'https://iranintl.com/live'
request = urllib2.Request(livePageUrl, headers={'User-Agent': 'Kodi'})

try:
    response = urllib2.urlopen(request)
    html = response.read()

    liveVideoUrls = re.findall('https://.*?.m3u8', html)

    if len(liveVideoUrls) > 0:
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=liveVideoUrls[0], listitem=li)

except urllib2.URLError as e:
    if hasattr(e, 'reason'):
        print ('We failed to reach a server. Reason: '), e.reason
    elif hasattr(e, 'code'):
        print ('The server couldn\'t fulfill the request. Error code: '), e.code

xbmcplugin.endOfDirectory(addon_handle)
