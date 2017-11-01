import xbmc, xbmcgui, os, xbmcaddon, urllib2
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon()
__language__ = __settings__.getLocalizedString
home = __settings__.getAddonInfo('path')
addonname = __settings__.getAddonInfo('name')
icon = xbmc.translatePath(os.path.join(home, 'icon.png'))
li = xbmcgui.ListItem ('manoto')
li.setArt({ 'thumb': icon })
li.setInfo('video', {'plot': 'Live Stream'})

livePageUrl = "https://www.manototv.com/live"

request = urllib2.Request(livePageUrl, headers={'User-Agent' : "Kodi"})
try:
    response = urllib2.urlopen(request)
    html = response.read()

    soup = BeautifulSoup(html)
    stream = soup.find('source', type='application/x-mpegURL')

    if stream is not None and stream['src'] is not None:
            xbmc.Player().play(stream['src'], li, False)
    else:
        xbmcgui.Dialog().ok(addonname,  __language__(30002), __language__(30010))
except urllib2.HTTPError, err:
        xbmcgui.Dialog().ok(addonname,  __language__(30000) % err.code, __language__(30010))
except:
        xbmcgui.Dialog().ok(addonname,  __language__(30001), __language__(30010))
