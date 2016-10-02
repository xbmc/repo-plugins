"""
Main module of Kodi (XBMC) addon to manage deejay.it's Reloaded shows.

This is the main module that takes care of receiving the information from the
parser and present it in Kodi creating the appropriate pages and feeding the
URL of the media content to the player.
"""
import sys
import urllib
import urlparse
import resources.lib.deejay_it_parser as deejay
import xbmcgui
import xbmcplugin
import xbmcaddon


__settings__ = xbmcaddon.Addon(id='plugin.audio.deejayIt.reloaded')
__language__ = __settings__.getLocalizedString


BASE_URL = sys.argv[0]
ADDON_HANDLE = int(sys.argv[1])
ARGS = urlparse.parse_qs(sys.argv[2][1:])
xbmcplugin.setContent(ADDON_HANDLE, 'episodes')
xbmcplugin.addSortMethod(ADDON_HANDLE,
    sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(ADDON_HANDLE,
    sortMethod=xbmcplugin.SORT_METHOD_DATE)
xbmcplugin.addSortMethod(ADDON_HANDLE,
    sortMethod=xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(ADDON_HANDLE,
    sortMethod=xbmcplugin.SORT_METHOD_PROGRAM_COUNT)


def build_url(query):
    """
    Taken from http://kodi.wiki/view/Audio/video_add-on_tutorial
    """
    return BASE_URL + '?' + urllib.urlencode(query)


MODE = ARGS.get('mode', None)

if MODE is None:
    LI = xbmcgui.ListItem('RELOADED')
    xbmcplugin.addDirectoryItem(
        handle=ADDON_HANDLE,
        url=build_url({'mode': 'reloaded'}),
        listitem=LI,
        isFolder=True
        )
    LI = xbmcgui.ListItem('PODCAST')
    xbmcplugin.addDirectoryItem(
        handle=ADDON_HANDLE,
        url=build_url({'mode': 'podcast'}),
        listitem=LI,
        isFolder=True
        )
elif MODE[0] == 'reloaded':
    try:
        LISTA = deejay.get_reloaded_list()
    #urllib2 errors are a subclass of IOError
    except IOError as e_urllib2:
        xbmcgui.Dialog().ok(
            __language__(30002),
            __language__(30003),
            str(e_urllib2.reason))
    else:
        for idx, prog in enumerate(LISTA):
            xbmc.log(msg='###############', level=xbmc.LOGDEBUG)
            xbmc.log(msg=str(idx), level=xbmc.LOGDEBUG)
            for pr in prog:
                xbmc.log(msg=pr, level=xbmc.LOGDEBUG)
            url = build_url({'mode': 'reloadedEpList',
                             'progName': prog[0],
                             'lastReloadedUrl': prog[2],
                             'showThumb': prog[1]})
            #showThumb, carried by LISTA, must be used in 'play' mode. It is
            #thus propagated through the calls
            li = xbmcgui.ListItem(prog[0], iconImage=prog[1])
            li.setInfo('music', {'date': prog[3], 'count': idx})
            xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE,
                                        url=url,
                                        listitem=li,
                                        isFolder=True)
elif MODE[0] in ('reloadedEpList', 'podcastEpList'):
    PROG_NAME = ARGS['progName'][0]
    LAST_RELOADED_URL = ARGS['lastReloadedUrl'][0]
    SHOW_THUMB = ARGS['showThumb'][0]
    FAN_ART = ARGS.get('fanArt')
    try:
        if MODE[0] == 'reloadedEpList':
            EPISODI, NEXTPAGE, IMG = deejay.get_episodi_reloaded(
                url=LAST_RELOADED_URL,
                oldimg=FAN_ART)
            MODO = 'playReloaded'
        else:
            EPISODI, NEXTPAGE, IMG = deejay.get_episodi_podcast(
                url=LAST_RELOADED_URL,
                oldimg=FAN_ART)
            MODO = 'playPodcast'
    #urllib2 errors are a subclass of IOError
    except IOError as e_urllib2:
        xbmcgui.Dialog().ok(
            __language__(30002),
            __language__(30004),
            str(e_urllib2.reason))
    else:
        for idx, ep in enumerate(EPISODI):
            #('http://www.deejay.it/audio/20071120-2/278354/',
            #   '20071120',
            #   'Puntata del 20 Novembre 2007')
            URL = build_url({'mode': MODO,
                             'epUrl': ep[0],
                             'showThumb': SHOW_THUMB,
                             'title': ep[2].encode('ascii', 'ignore'),
                             'progName': PROG_NAME})
            LI = xbmcgui.ListItem(ep[2],
                                  iconImage='DefaultAudio.png')
            LI.setProperty('IsPlayable', 'true')
            #Setting fanArt
            #not using setArt to keep Frodo's compatibility
            #LI.setArt({'fanart' : img})
            LI.setProperty('fanart_image', IMG)
            LI.setInfo('music', {'date': ep[1], 'count': idx})
            xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE,
                                        url=URL,
                                        listitem=LI)
        if NEXTPAGE:
            #Questo aggiunge la prossima pagina
            URL = build_url({'mode': MODE[0],
                             'progName': PROG_NAME,
                             'lastReloadedUrl': NEXTPAGE,
                             'showThumb': SHOW_THUMB,
                             'fanArt': IMG})
            LI = xbmcgui.ListItem('>>> '+__language__(30001)+' >>>')
            xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE,
                                        url=URL,
                                        listitem=LI,
                                        isFolder=True)

elif MODE[0] in ('playReloaded', 'playPodcast'):
    try:
        URL = deejay.get_epfile(ARGS['epUrl'][0])
    # urllib2 errors are a subclass of IOError
    except IOError as e_urllib2:
        xbmcgui.Dialog().ok(
            __language__(30002),
            __language__(30005),
            str(e_urllib2.reason))
    else:
        LI = xbmcgui.ListItem(path=URL)
        LI.setThumbnailImage(ARGS['showThumb'][0])
        LI.setInfo('music', {'title': ARGS['title'][0],
                               'album': ARGS['progName'][0],
                               'artist': 'Deejay '+MODE[0][4:]})
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, LI)

elif MODE[0] == 'podcast':
    try:
        LISTA = deejay.get_podcast_list()
    #urllib2 errors are a subclass of IOError
    except IOError as e_urllib2:
        xbmcgui.Dialog().ok(
            __language__(30002),
            __language__(30003),
            str(e_urllib2.reason))
    else:
        for idx, prog in enumerate(LISTA):
            url = build_url({'mode': 'podcastEpList',
                             'progName': prog[0],
                             'lastReloadedUrl': prog[2],
                             'showThumb': prog[1]})
            li = xbmcgui.ListItem(prog[0], iconImage=prog[1])
            li.setInfo('music', {'date': prog[3], 'count': idx})
            xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE,
                                        url=url,
                                        listitem=li,
                                        isFolder=True)
            for ep in prog[4]:
                URL = build_url({'mode': 'playPodcast',
                    'epUrl': ep[1],
                    'showThumb': prog[1],
                    'title': ep[0].encode('ascii', 'ignore'),
                    'progName': prog[0]})
                LI = xbmcgui.ListItem(u"\u2022"+' '+ep[0], iconImage=prog[1])
                # bullet list for episodes
                LI.setProperty('IsPlayable', 'true')
                LI.setInfo('music', {'date': prog[3], 'count': idx})
                xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE,
                    url=URL,
                    listitem=LI)

# e chiudiamo la lista per tutti i modi
xbmcplugin.endOfDirectory(ADDON_HANDLE)
