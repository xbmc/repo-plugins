import json

import urllib.request, urllib.parse, urllib.error

from resources.lib.utils.Utils import buildUrl
from resources.lib.tv3cat.TV3cat import TV3cat
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmc
import xbmcvfs
import urllib.parse

from resources.lib.video.FolderVideo import FolderVideo

PROTOCOL = 'mpd'
DRM = 'com.widevine.alpha'
# The generic license URL was causing issues on some devices
# 3cat doesn't use DRM for most content, so we'll set this to empty and only use when needed
LICENSE_URL = ''


class UI:

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

        elif mode[0] == 'pellicules':
            self.listFolder([
                FolderVideo(self.tv3.strs.get("novetats"), "novetats", "pellicules_categoria"),
                FolderVideo(self.tv3.strs.get("cataleg_complet"), "cataleg", "pellicules_categoria"),
                FolderVideo(self.tv3.strs.get("categories"), "", "pellicules_categories")
            ])

        elif mode[0] == 'pellicules_categories':
            self.listFolder(self.tv3.getMovieCategories())

        elif mode[0] == 'pellicules_categoria':
            self.listVideos(self.tv3.getMovies(url[0]))

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

            if len(lFolder) > 0:
                self.listFolder(lFolder)
            else:
                self.run(['getlistvideos'], url)

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
            # If this is a folder item (e.g. for pagination)
            if isinstance(video, FolderVideo):
                mode = video.mode
                name = video.name
                url = video.url

                urlPlugin = buildUrl({'mode': mode, 'url': url}, self.base_url)
                liz = xbmcgui.ListItem(name)
                liz.setInfo(type="Video", infoLabels={"title": name})

                xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=urlPlugin, listitem=liz, isFolder=True)
                continue

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
        xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.addon_handle)

    def playVideo(self,videoId):
        xbmc.log("plugin.video.3cat -UI - playVideo " + str(videoId))

        if str(videoId).lower().startswith("http"):
            xbmc.log("plugin.video.3cat - UI - is stream link")
            # For direct stream links (like live TV)
            if videoId.lower().endswith('.m3u8'):
                # HLS stream
                self.playHLSStream(videoId)
            elif videoId.lower().endswith('.mp4'):
                # Simple MP4 playback
                self.playMP4Stream(videoId)
            else:
                # Try to play directly as fallback
                xbmc.Player().play(videoId)
            return

        # For video IDs, fetch the stream URL from the API
        apiJsonUrl = "https://api-media.3cat.cat/pvideo/media.jsp?media=video&versio=vast&idint={}&profile=pc_3cat&format=dm".format(
            videoId)
        xbmc.log("plugin.video.3cat - UI - playVideo apijson url" + str(apiJsonUrl))
        
        try:
            with urllib.request.urlopen(apiJsonUrl) as response:
                data = response.read()
                json_data = json.loads(data)
                
                # Check if we have valid media data
                if 'media' not in json_data or 'url' not in json_data['media'] or not json_data['media']['url']:
                    xbmc.log("plugin.video.3cat - UI - Error: Invalid API response", level=xbmc.LOGERROR)
                    xbmcgui.Dialog().notification('Error', 'Could not get video URL from 3cat', xbmcgui.NOTIFICATION_ERROR)
                    return
                
                streamUrl = json_data['media']['url'][0]['file']
                xbmc.log("plugin.video.3cat - UI - playVideo stream URL: " + str(streamUrl))
                
                # Determine stream type and play accordingly
                if streamUrl.lower().endswith('.mp4'):
                    self.playMP4Stream(streamUrl)
                elif streamUrl.lower().endswith('.m3u8'):
                    self.playHLSStream(streamUrl)
                elif streamUrl.lower().endswith('.mpd'):
                    self.playMPDStream(streamUrl)
                else:
                    # Try adaptive streaming as fallback
                    self.playMPDStream(streamUrl)
        except Exception as e:
            xbmc.log("plugin.video.3cat - UI - Error fetching video: " + str(e), level=xbmc.LOGERROR)
            xbmcgui.Dialog().notification('Error', 'Could not play video: ' + str(e), xbmcgui.NOTIFICATION_ERROR)

    def playMP4Stream(self, streamUrl):
        """Play a simple MP4 stream"""
        xbmc.log("plugin.video.3cat - UI - Playing MP4: " + streamUrl)
        play_item = xbmcgui.ListItem(path=streamUrl)
        play_item.setProperty('IsPlayable', 'true')
        xbmcplugin.setResolvedUrl(handle=self.addon_handle, succeeded=True, listitem=play_item)

    def playHLSStream(self, streamUrl):
        """Play an HLS stream using inputstream.adaptive"""
        xbmc.log("plugin.video.3cat - UI - Playing HLS: " + streamUrl)
        try:
            from inputstreamhelper import Helper
            is_helper = Helper('hls')
            if is_helper.check_inputstream():
                play_item = xbmcgui.ListItem(path=streamUrl)
                play_item.setProperty('inputstream', 'inputstream.adaptive')
                play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
                play_item.setProperty('inputstream.adaptive.stream_headers',
                                    'User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
                xbmcplugin.setResolvedUrl(handle=self.addon_handle, succeeded=True, listitem=play_item)
            else:
                # Fallback to direct play if inputstream.adaptive is not available
                play_item = xbmcgui.ListItem(path=streamUrl)
                xbmcplugin.setResolvedUrl(handle=self.addon_handle, succeeded=True, listitem=play_item)
        except ImportError:
            # Fallback if inputstreamhelper is not available
            play_item = xbmcgui.ListItem(path=streamUrl)
            xbmcplugin.setResolvedUrl(handle=self.addon_handle, succeeded=True, listitem=play_item)

    def playMPDStream(self, streamUrl):
        """Play an MPD (DASH) stream using inputstream.adaptive with optional DRM"""
        xbmc.log("plugin.video.3cat - UI - Playing MPD: " + streamUrl)
        try:
            from inputstreamhelper import Helper
            
            # Check if this stream might need DRM
            needs_drm = False
            try:
                # Try to fetch the MPD manifest to check for ContentProtection elements
                with urllib.request.urlopen(streamUrl) as response:
                    mpd_content = response.read().decode('utf-8')
                    if 'ContentProtection' in mpd_content:
                        needs_drm = True
                        xbmc.log("plugin.video.3cat - UI - DRM content protection detected", level=xbmc.LOGINFO)
            except:
                # If we can't check, assume no DRM is needed
                pass
            
            # Initialize inputstream helper with or without DRM
            if needs_drm:
                is_helper = Helper(PROTOCOL, drm=DRM)
            else:
                is_helper = Helper(PROTOCOL)
                
            if is_helper.check_inputstream():
                play_item = xbmcgui.ListItem(path=streamUrl)
                play_item.setProperty('inputstream', 'inputstream.adaptive')
                play_item.setProperty('inputstream.adaptive.stream_headers',
                                    'User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
                play_item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
                play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                
                # Only set DRM properties if needed
                if needs_drm:
                    # Try to extract license URL from the MPD if available
                    license_url = self.extract_license_url_from_mpd(mpd_content) if 'mpd_content' in locals() else None
                    
                    if not license_url and LICENSE_URL:
                        license_url = LICENSE_URL
                    
                    if license_url:
                        play_item.setProperty('inputstream.adaptive.license_type', DRM)
                        play_item.setProperty('inputstream.adaptive.license_key', license_url + '||R{SSM}|')
                        xbmc.log("plugin.video.3cat - UI - Using license URL: " + license_url, level=xbmc.LOGINFO)
                
                xbmcplugin.setResolvedUrl(handle=self.addon_handle, succeeded=True, listitem=play_item)
            else:
                # Fallback to direct play if inputstream.adaptive is not available
                xbmc.log("plugin.video.3cat - UI - inputstream.adaptive not available, trying direct play", level=xbmc.LOGWARNING)
                play_item = xbmcgui.ListItem(path=streamUrl)
                xbmcplugin.setResolvedUrl(handle=self.addon_handle, succeeded=True, listitem=play_item)
        except ImportError:
            # Fallback if inputstreamhelper is not available
            xbmc.log("plugin.video.3cat - UI - inputstreamhelper not available, trying direct play", level=xbmc.LOGWARNING)
            play_item = xbmcgui.ListItem(path=streamUrl)
            xbmcplugin.setResolvedUrl(handle=self.addon_handle, succeeded=True, listitem=play_item)
    
    def extract_license_url_from_mpd(self, mpd_content):
        """Try to extract license URL from MPD content if present"""
        try:
            import re
            # Look for license URL in the MPD
            license_url_match = re.search(r'licenseUrl="([^"]+)"', mpd_content)
            if license_url_match:
                return license_url_match.group(1)
        except:
            pass
        return None