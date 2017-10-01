import xbmc
import xbmcgui
import xbmcplugin
from urllib import urlencode
from resources.lib.vrtplayer import vrtplayer
from resources.lib.vrtplayer import urltostreamservice
from resources.lib.kodiwrappers import sortmethod

class KodiWrapper:

    def __init__(self, handle, url, addon):
        self._handle = handle
        self._url = url
        self._addon = addon

    def show_listing(self, list_items, sort=None):
        listing = []
        for title_item in list_items:
            list_item = xbmcgui.ListItem(label=title_item.title)
            url = self._url + '?' + urlencode(title_item.url_dictionary)
            list_item.setProperty('IsPlayable', str(title_item.is_playable))

            if title_item.thumbnail is not None:
                list_item.setArt({'thumb': title_item.thumbnail})

            list_item.setInfo('video', title_item.video_dictionary)

            listing.append((url, list_item, not title_item.is_playable))
        xbmcplugin.addDirectoryItems(self._handle, listing, len(listing))

        if sort is not None:
            kodi_sorts = {sortmethod.ALPHABET: xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE}
            kodi_sortmethod = kodi_sorts.get(sort)
            xbmcplugin.addSortMethod(self._handle, kodi_sortmethod)

        xbmcplugin.endOfDirectory(self._handle)

    def play_video(self, path):
        stream_service = urltostreamservice.UrlToStreamService(vrtplayer.VRTPlayer._VRT_BASE,
                                                               vrtplayer.VRTPlayer._VRTNU_BASE_URL,
                                                               self._addon)
        stream = stream_service.get_stream_from_url(path)
        if stream is not None:
            play_item = xbmcgui.ListItem(path=stream.stream_url)
            if stream.subtitle_url is not None:
                play_item.setSubtitles([stream.subtitle_url])
            xbmcplugin.setResolvedUrl(self._handle, True, listitem=play_item)

    def play_livestream(self, path):
        play_item = xbmcgui.ListItem(path=path)
        xbmcplugin.setResolvedUrl(self._handle, True, listitem=play_item)
