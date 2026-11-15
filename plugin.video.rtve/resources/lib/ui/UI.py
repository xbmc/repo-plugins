from builtins import str
from builtins import object
from logging import DEBUG

from resources.lib.utils.Utils import buildUrl, getJsonData
from resources.lib.rtve.rtve import rtve
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmc
import xbmcvfs
import time

class UI(object):

    def __init__(self, base_url, addon_handle, args):
        xbmc.log("plugin.video.rtve classe UI - start init() ", xbmc.LOGDEBUG)
        addon = xbmcaddon.Addon()
        self.rtve = rtve(addon)
        self.base_url = base_url
        self.addon_handle = addon_handle
        self.args = args
        self.mode = args.get('mode', None)
        self.url = args.get('url', [''])
        xbmc.log("plugin.video.rtve classe UI - finish init()", xbmc.LOGDEBUG)


    def run(self, mode, url):
        xbmc.log("plugin.video.rtve classe UI - run()  mode = " + str(mode) + ", url " + str(url), xbmc.LOGDEBUG)

        if mode == None:
            xbmc.log("plugin.video.rtve classe UI - mode = None", xbmc.LOGDEBUG)
            lFolder = self.rtve.listHome()

            if len(lFolder) > 0:
                self.listFolder(lFolder)
            else:
                xbmc.log("plugin.video.rtve - UI.run() Home - No existeixen elements", xbmc.LOGDEBUG)

        elif mode[0] == 'getProgrames':
            xbmc.log("plugin.video.rtve - Programes", xbmc.LOGDEBUG)
            (folders, videos) = self.rtve.listProgrames(url[0])
            self.listFolder(folders, False)
            self.listVideos(videos)

        elif mode[0] == 'playVideo':
            self.playVideo(url[0])

    def listVideos(self, lVideos):
        xbmc.log("plugin.video.rtve - UI - listVideos - Numero videos: " + str(len(lVideos)), xbmc.LOGDEBUG)

        for video in lVideos:
            # Create a list item with a text label
            list_item = xbmcgui.ListItem(label=video.title)
            # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
            # Here we use only poster for simplicity's sake.
            # In a real-life plugin you may need to set multiple image types.
            list_item.setArt({'poster': video.iconImage})
            list_item.setProperty('IsPlayable', 'true')
            # Set additional info for the list item via InfoTag.
            # 'mediatype' is needed for skin to display info for this ListItem correctly.
            info_tag = list_item.getVideoInfoTag()
            info_tag.setMediaType('movie')
            info_tag.setTitle(video.title)
            info_tag.setPlot(video.information)
            # Set 'IsPlayable' property to 'true'.

            url =  video.url
            # Add the list item to a virtual Kodi folder.
            # is_folder = False means that this item won't open any sub-list.
            is_folder = False
            # Add our item to the Kodi virtual folder listing.
            xbmc.log("plugin.video.rtve - UI - directory item " + str(url), xbmc.LOGDEBUG)
            urlPlugin = buildUrl({'mode': 'playVideo', 'url': url}, self.base_url)

            xbmcplugin.addDirectoryItem(self.addon_handle, urlPlugin, list_item, is_folder)
            # Add sort methods for the virtual folder items
        xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)

        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.addon_handle)

    def listFolder(self, lFolderVideos, enddirectory=True):
        xbmc.log("plugin.video.rtve classe UI - listFolder", xbmc.LOGDEBUG)
        for folder in lFolderVideos:

            mode = folder.mode
            name = folder.name
            url = folder.url
            iconImage = folder.iconImage
            thumbImage = folder.thumbnailImage

            urlPlugin = buildUrl({'mode': mode, 'url': url}, self.base_url)
            liz = xbmcgui.ListItem(name)
            liz.setInfo(type="Video", infoLabels={"title": name})
            liz.setArt({'thumb': thumbImage, 'icon' : iconImage})

            xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=urlPlugin, listitem=liz, isFolder=True)

        if enddirectory:
            xbmcplugin.endOfDirectory(self.addon_handle)

    class DRMStreamPlayer(xbmc.Player):
        def __init__(self):
            super().__init__()
            self.is_playing = False
            self.playback_error = False

        def onPlayBackStarted(self):
            self.is_playing = True
            xbmc.log('Playback started successfully', xbmc.LOGDEBUG)

        def onPlayBackError(self):
            self.playback_error = True
            xbmc.log('Playback error occurred', xbmc.LOGERROR)

        def onPlayBackStopped(self):
            self.is_playing = False

    def playVideo(self,videoId):
        xbmc.log("plugin.video.rtve -UI - playVideo " + str(videoId), xbmc.LOGDEBUG)

        stream_url = "https://ztnr.rtve.es/ztnr/{}.mpd".format(videoId)
        xbmc.log("plugin.video.rtve - UI - playVideo apijson url" + str(stream_url), xbmc.LOGDEBUG)

        license_url = ""
        try:
            tokenUrl = "https://api.rtve.es/api/token/{}".format(videoId)
            tokenJson = getJsonData(tokenUrl)

            xbmc.log("plugin.video.rtve - UI - playVideo token json" + str(tokenJson), xbmc.LOGDEBUG)

            license_url = tokenJson['widevineURL']
            xbmc.log("plugin.video.rtve - UI - playVideo widevine url" + str(license_url), xbmc.LOGDEBUG)
        except Exception as e:
            xbmc.log(f'Error playing DRM stream: {str(e)}', xbmc.LOGERROR)


        from inputstreamhelper import Helper  # pylint: disable=import-outside-toplevel
        from urllib.parse import quote

        # Constants
        PROTOCOL = 'mpd'
        DRM = 'com.widevine.alpha'

        # HTTP headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Referer': 'https://www.rtve.es/',
            'Origin': 'https://www.rtve.es',
            'Accept': '*/*'
        }

        # Convert headers to Kodi format
        headers_string = '&'.join([f'{k}={quote(v)}' for k, v in headers.items()])

        try:
            # Initialize custom player
            player = self.DRMStreamPlayer()

            # Create and configure the ListItem
            play_item = xbmcgui.ListItem(path=stream_url)

            # Set required properties for DRM playback
            play_item.setProperty('inputstream', 'inputstream.adaptive')
            play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
            play_item.setProperty('inputstream.adaptive.manifest_headers', headers_string)
            play_item.setProperty('inputstream.adaptive.stream_headers', headers_string)

            # Configure license key with proper formatting and increased timeout
            if license_url:
                play_item.setProperty('inputstream.adaptive.license_type', DRM)
                play_item.setProperty('inputstream.adaptive.license_key', license_url)

            # Set additional properties
            play_item.setMimeType('application/dash+xml')
            play_item.setContentLookup(False)

            # Add properties to help with buffering
            play_item.setProperty('inputstream.adaptive.stream_selection_type', 'adaptive')

            # Adjust these buffering settings
            play_item.setProperty('inputstream.adaptive.stream_buffer_size', '524288')  # Doubled buffer
            play_item.setProperty('inputstream.adaptive.initial_buffer_duration', '15')
            play_item.setProperty('inputstream.adaptive.persistent_storage', 'true')
            play_item.setProperty('inputstream.adaptive.max_bandwidth', '20000000')
            play_item.setProperty('inputstream.adaptive.min_bandwidth', '500000')

            # Start playback
            xbmcplugin.setResolvedUrl(handle=self.addon_handle, succeeded=True, listitem=play_item)

            # Log success
            xbmc.log('DRM Stream playback initiated successfully', xbmc.LOGDEBUG)

        except Exception as e:
            xbmc.log(f'Error playing DRM stream: {str(e)}', xbmc.LOGERROR)
            xbmcgui.Dialog().notification('Error', 'Failed to play DRM stream', xbmcgui.NOTIFICATION_ERROR)
