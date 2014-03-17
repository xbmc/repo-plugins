import sys
import urllib
import urlparse

import xbmcgui
import xbmcplugin
import xbmc
import resources.lib.deejayItParser as deejay

import xbmcaddon
__settings__ = xbmcaddon.Addon(id='plugin.audio.deejayIt.reloaded')
__language__ = __settings__.getLocalizedString


base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'episodes')


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


mode = args.get('mode', None)

if mode is None:
    for prog in deejay.programmi:
        url = build_url({'mode': 'epList',
                         'progName': prog[0],
                         'lastReloadedUrl': prog[2]})
        li = xbmcgui.ListItem(prog[0], iconImage=prog[1])
        xbmcplugin.addDirectoryItem(handle=addon_handle,
                                    url=url,
                                    listitem=li,
                                    isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'epList':
    progName = args['progName'][0]
    lastReloadedUrl = args['lastReloadedUrl'][0]
    episodi, nextpage = deejay.get_episodi(lastReloadedUrl)
    #print nextpage

    for ep in episodi:
        #       ('http://www.deejay.it/audio/20121203-2/271391/', 'Puntata del 3 Dicembre 201
        url = build_url({'mode': 'play',
                         'epUrl': ep[0]})
        li = xbmcgui.ListItem(ep[1],
                              iconImage='DefaultAudio.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle,
                                    url=url,
                                    listitem=li)

    if nextpage:
        #Questo aggiunge la prossima pagina
        url = build_url({'mode': 'epList',
                         'progName': progName,
                         'lastReloadedUrl': nextpage})

        li = xbmcgui.ListItem('>>> '+__language__(30001)+' >>>')
        xbmcplugin.addDirectoryItem(handle=addon_handle,
                                    url=url,
                                    listitem=li,
                                    isFolder=True)

    # e chiudiamo la lista
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'play':
    dialog=xbmcgui.DialogProgress()
    dialog.create('Starting playback','...')
    epUrl = args['epUrl'][0]
    dialog.close()
    xbmc.Player().play(deejay.get_epfile(epUrl))

