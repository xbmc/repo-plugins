from future import standard_library
standard_library.install_aliases()
from os.path import join
from sys import argv
import json
from time import gmtime, strftime, strptime
import urllib.error
from urllib.request import urlopen
from xbmc import translatePath
import xbmcaddon
from xbmcgui import Dialog, ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory
ADDON = xbmcaddon.Addon()
ADDONNAME = ADDON.getAddonInfo('name')
CWD = ADDON.getAddonInfo('path')
LANGUAGE = ADDON.getLocalizedString
class LoadLister:
        def __init__(self):
                request = urllib.request.Request('https://navaapi1.b-cdn.net/navaapi2/GetMp3?type=Featured&from=0&to=100', headers={'User-Agent' : 'Kodi'})
                response = urllib.request.urlopen(request)
                json_text = response.read()
                loaded_json = json.loads(json_text)
                for item in loaded_json:
                        self.addLink('[B]' + item['song_name'] + '[/B][CR]' + item['artist_name'], item['download'], item['image'], {'Artist': item['artist_name'],'Title': item['song_name'],'Album': 'Single'})
        def addLink(self, name, url, image = '', info = {}, totalItems = 0):
                item = ListItem(name)
                item.setArt({ 'thumb': image, 'icon': image, 'fanart': image})
                item.setProperty('mimetype', 'audio/mpeg')
                item.setInfo('music', info)
                return addDirectoryItem(int(argv[1]), url, item, False, totalItems)
        def run(self, handle):
                endOfDirectory(int(handle))
if __name__ == '__main__':
        try:
                appClass = LoadLister()
                appClass.run(argv[1])
        except:
                xbmcgui.Dialog().ok(ADDONNAME, LANGUAGE(30002), LANGUAGE(30000))