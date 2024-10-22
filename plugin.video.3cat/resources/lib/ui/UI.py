import json
from builtins import str
from builtins import object

import urllib.request, urllib.parse, urllib.error

from resources.lib.utils.Utils import buildUrl
from resources.lib.tv3cat.TV3cat import TV3cat
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmc
import xbmcvfs
import urllib.parse

PROTOCOL = 'mpd'
DRM = 'com.widevine.alpha'
LICENSE_URL = 'https://cwip-shaka-proxy.appspot.com/no_auth'


class UI(object):

    def __init__(self, base_url, addon_handle, args):
        xbmc.log("plugin.video.3cat classe UI - start init() ")
        addon = xbmcaddon.Addon()
        addon_path = xbmcvfs.translatePath(addon.getAddonInfo('path'))
        self.tv3 = TV3cat(addon_path, addon)
        self.base_url = base_url
        self.addon_handle = addon_handle
        self.args = args
        self.mode = args.get('mode', None)
        self.url = args.get('url', [''])
        xbmc.log("plugin.video.3cat classe UI - finish init()")


    def run(self, mode, url):
        xbmc.log("plugin.video.3cat classe UI - run()  mode = " + str(mode) + ", url " + str(url))

        if mode == None:
            xbmc.log("plugin.video.3cat classe UI - mode = None")
            lFolder = self.tv3.listHome()

            if len(lFolder) > 0:
                self.listFolder(lFolder)
            else:
                xbmc.log("plugin.video.3cat - UI.run() Home - No existeixen elements")

        elif mode[0] == 'programes':

            lFolder = self.tv3.dirSections()

            if len(lFolder) > 0:
                self.listFolder(lFolder)
            else:
                xbmc.log("plugin.video.3cat - UI.run() programes - No existeixen elements")

        elif mode[0] == 'sections':

            lFolder = self.tv3.programsSections(url[0])

            if len(lFolder) > 0:
                self.listFolder(lFolder)
            else:
                xbmc.log("plugin.video.3cat - UI.run() sections - No existeixen elements")

        elif mode[0] == 'directe':

            lVideos = self.tv3.listDirecte()
            self.listVideos(lVideos)

        elif mode[0] == 'cercar':

            lVideos = self.tv3.search()

            if len(lVideos) > 0:
                self.listVideos(lVideos)
            else:
                xbmc.log("plugin.video.3cat - UI.run() cercar - No s'ha trobat cap video")


        elif mode[0] == 'getlistvideos':
            lVideos = self.tv3.getListVideos(url[0])
            self.listVideos(lVideos)

        elif mode[0] == 'getProgrames':
            xbmc.log("plugin.video.3cat - Programes")
            lFolder = self.tv3.listProgrames(url[0])
            self.listFolder(lFolder)

        elif mode[0] == 'getTemporades':
            xbmc.log("plugin.video.3cat - Temporades")
            lFolder = self.tv3.getListTemporades(url[0])
            self.listFolder(lFolder)

        elif mode[0] == 'coleccions':
            xbmc.log("plugin.video.3cat - Coleccions")
            lFolder = self.tv3.listColeccions()
            self.listFolder(lFolder)

        elif mode[0] == 'playVideo':
            self.playVideo(url[0])

    def listFolder(self, lFolderVideos):
        xbmc.log("plugin.video.3cat classe UI - listFolder")
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
        xbmcplugin.endOfDirectory(self.addon_handle)

    def listVideos(self, lVideos):
        xbmc.log("plugin.video.3cat - UI - listVideos - Numero videos: " + str(len(lVideos)))

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
            xbmc.log("plugin.video.3cat - UI - directory item " + str(url))
            urlPlugin = buildUrl({'mode': 'playVideo', 'url': url}, self.base_url)

            xbmcplugin.addDirectoryItem(self.addon_handle, urlPlugin, list_item, is_folder)
            # Add sort methods for the virtual folder items
        xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.addon_handle)

    def playVideo(self,videoId):
        xbmc.log("plugin.video.3cat -UI - playVideo " + str(videoId))

        if str(videoId).lower().startswith("http"):
            xbmc.log("plugin.video.3cat - UI - is stream link")
            # Simple MP4 playback
            xbmc.Player().play(videoId)
            return

        apiJsonUrl = "https://api-media.3cat.cat/pvideo/media.jsp?media=video&versio=vast&idint={}&profile=pc_3cat&format=dm".format(
            videoId)
        xbmc.log("plugin.video.3cat - UI - playVideo apijson url" + str(apiJsonUrl))
        streamUrl = ""
        with urllib.request.urlopen(apiJsonUrl) as response:
            data = response.read()
            json_data = json.loads(data)
            streamUrl = json_data['media']['url'][0]['file']

        xbmc.log("plugin.video.3cat - UI - playVideo mpd/mp4 file " + str(streamUrl))
        is_mp4 = streamUrl.lower().endswith('.mp4')

        if is_mp4:
            xbmc.log("plugin.video.3cat - UI - is mp4")
            # Simple MP4 playback
            xbmc.Player().play(streamUrl)
        else:
            from inputstreamhelper import Helper  # pylint: disable=import-outside-toplevel

            is_helper = Helper(PROTOCOL, drm=DRM)
            if is_helper.check_inputstream():
                play_item = xbmcgui.ListItem(path=streamUrl)
                play_item.setProperty('inputstream', 'inputstream.adaptive')
                play_item.setProperty('inputstream.adaptive.stream_headers',
                                      'User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
                play_item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
                play_item.setProperty('inputstream.adaptive.manifest_update_interval', '10')
                play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                play_item.setProperty('inputstream.adaptive.license_type', DRM)
                play_item.setProperty('inputstream.adaptive.license_key', LICENSE_URL + '||R{SSM}|')
                xbmcplugin.setResolvedUrl(handle=self.addon_handle, succeeded=True, listitem=play_item)