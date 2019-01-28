import xbmc, xbmcgui, os, xbmcaddon, urllib2
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon()
__language__ = __settings__.getLocalizedString
home = __settings__.getAddonInfo('path')
addonname = __settings__.getAddonInfo('name')
icon = xbmc.translatePath(os.path.join(home, 'icon.png'))
li = xbmcgui.ListItem ('IRIB TV3')
li.setArt({ 'thumb': icon })
li.setInfo('video', {'plot': 'Live Stream'})

livePageUrl = "https://www.tv3.ir/live"

request = urllib2.Request(livePageUrl, headers={'User-Agent' : "Kodi"})

response = urllib2.urlopen(request)
html = response.read()

soup = BeautifulSoup(html)
stream = soup.find('video', preload='auto')

if stream is not None and stream['data-source'] is not None:
        xbmc.Player().play(stream['data-source'], li, False)