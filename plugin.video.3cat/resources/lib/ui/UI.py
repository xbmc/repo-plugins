import os
import re
import shutil
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib.tv3cat.TV3cat import TV3cat
from resources.lib.utils import Urls
from resources.lib.utils.Utils import USER_AGENT, buildUrl, fetch, getJson, notify
from resources.lib.video.FolderVideo import FolderVideo

PROTOCOL = 'mpd'
DRM = 'com.widevine.alpha'
# The generic license URL was causing issues on some devices
# 3cat doesn't use DRM for most content, so we'll set this to empty and only use when needed
LICENSE_URL = ''
STREAM_HEADERS = 'User-Agent=' + USER_AGENT

# values of the stream_format setting
FORMAT_ADAPTIVE = 0
FORMAT_MP4 = 1

SUBTITLES_DIR = 'special://temp/plugin.video.3cat/subtitles/'


class UI:

    def __init__(self, base_url, addon_handle, args):
        xbmc.log("plugin.video.3cat classe UI - start init() ")
        self.addon = xbmcaddon.Addon()
        addon_path = xbmcvfs.translatePath(self.addon.getAddonInfo('path'))
        self.tv3 = TV3cat(addon_path, self.addon)
        self.base_url = base_url
        self.addon_handle = addon_handle
        self.args = args
        self.mode = args.get('mode', None)
        self.url = args.get('url', [''])
        xbmc.log("plugin.video.3cat classe UI - finish init()")

    def getSettingInt(self, key, default):
        try:
            return self.addon.getSettings().getInt(key)
        except Exception:
            try:
                return int(self.addon.getSetting(key))
            except (TypeError, ValueError):
                return default

    def getSettingBool(self, key, default):
        try:
            return self.addon.getSettings().getBool(key)
        except Exception:
            value = self.addon.getSetting(key)
            return default if value == '' else value == 'true'

    def run(self, mode, url):
        xbmc.log("plugin.video.3cat classe UI - run()  mode = " + str(mode) + ", url " + str(url))
        mode = mode[0] if mode else None
        url = url[0] if url else ''

        if mode is None:
            self.listFolder(self.tv3.listHome())

        elif mode == 'pellicules':
            self.listFolder([
                FolderVideo(self.tv3.strs.get("novetats"), "novetats", "pellicules_categoria"),
                FolderVideo(self.tv3.strs.get("cataleg_complet"), "cataleg", "pellicules_categoria"),
                FolderVideo(self.tv3.strs.get("categories"), "", "pellicules_categories")
            ])

        elif mode == 'pellicules_categories':
            self.listFolder(self.tv3.getMovieCategories())

        elif mode == 'pellicules_categoria':
            self.listVideos(self.tv3.getMovies(url), 'movies')

        elif mode == 'directe':
            self.listVideos(self.tv3.listDirecte())

        elif mode == 'cercar':
            self.askSearch()

        elif mode == 'cerca':
            pagina, _, text = url.partition('|')
            results = self.tv3.search(text, pagina if pagina.isdigit() else 1)
            if not results:
                notify(self.tv3.strs.get('sense_resultats'), xbmcgui.NOTIFICATION_INFO)
            self.listVideos(results)

        elif mode == 'getlistvideos':
            self.listVideos(self.tv3.getListVideos(url), 'episodes')

        elif mode == 'getProgrames':
            xbmc.log("plugin.video.3cat - Programes")
            self.listFolder(self.tv3.listProgrames(url), 'tvshows')

        elif mode == 'getTemporades':
            xbmc.log("plugin.video.3cat - Temporades")
            lFolder = self.tv3.getListTemporades(url)

            if len(lFolder) > 0:
                self.listFolder(lFolder)
            else:
                self.run(['getlistvideos'], [url])

        elif mode == 'coleccions':
            xbmc.log("plugin.video.3cat - Coleccions")
            self.listFolder(self.tv3.listColeccions())

        elif mode == 'playVideo':
            self.playVideo(url)

        else:
            xbmc.log("plugin.video.3cat - unknown mode " + str(mode), xbmc.LOGWARNING)
            xbmcplugin.endOfDirectory(self.addon_handle, succeeded=False)

    def askSearch(self):
        keyboard = xbmc.Keyboard('', self.tv3.strs.get('cercar'))
        keyboard.doModal()
        text = keyboard.getText().strip() if keyboard.isConfirmed() else ''

        # Show the results under their own url. Listing them here would open the keyboard
        # again every time the user comes back to the results.
        xbmcplugin.endOfDirectory(self.addon_handle, succeeded=False)
        if text:
            xbmc.executebuiltin('Container.Update(' + buildUrl({'mode': 'cerca', 'url': '1|' + text}, self.base_url) + ')')

    def folderItem(self, folder):
        urlPlugin = buildUrl({'mode': folder.mode, 'url': folder.url}, self.base_url)
        liz = xbmcgui.ListItem(folder.name, offscreen=True)
        info_tag = liz.getVideoInfoTag()
        info_tag.setTitle(folder.name)
        if folder.plot:
            info_tag.setPlot(folder.plot)
        art = {'thumb': folder.thumbnailImage, 'icon': folder.iconImage, 'poster': folder.thumbnailImage,
               'fanart': folder.fanart}
        liz.setArt({k: v for k, v in art.items() if v})
        return urlPlugin, liz

    def videoItem(self, video):
        list_item = xbmcgui.ListItem(label=video.title, offscreen=True)
        art = {'thumb': video.thumbnailImage, 'icon': video.iconImage, 'poster': video.iconImage,
               'fanart': video.fanart}
        list_item.setArt({k: v for k, v in art.items() if v})
        list_item.setProperty('IsPlayable', 'true')

        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        info_tag = list_item.getVideoInfoTag()
        info_tag.setMediaType(video.mediatype)
        info_tag.setTitle(video.title)
        info_tag.setPlot(video.information)
        if video.duration:
            info_tag.setDuration(video.duration)
        if video.show:
            info_tag.setTvShowTitle(video.show)
        if video.season is not None and video.episode is not None:
            info_tag.setSeason(video.season)
            info_tag.setEpisode(video.episode)
        if video.aired:
            info_tag.setFirstAired(video.aired)
            info_tag.setPremiered(video.aired)
            info_tag.setYear(int(video.aired[:4]))

        xbmc.log("plugin.video.3cat - UI - directory item " + str(video.url))
        return buildUrl({'mode': 'playVideo', 'url': video.url}, self.base_url), list_item

    def listFolder(self, lFolderVideos, content=None):
        xbmc.log("plugin.video.3cat classe UI - listFolder")
        if content:
            xbmcplugin.setContent(self.addon_handle, content)
        for folder in lFolderVideos:
            urlPlugin, liz = self.folderItem(folder)
            xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=urlPlugin, listitem=liz, isFolder=True)
        xbmcplugin.endOfDirectory(self.addon_handle)

    def listVideos(self, lVideos, content='videos'):
        xbmc.log("plugin.video.3cat - UI - listVideos - Numero videos: " + str(len(lVideos)))
        xbmcplugin.setContent(self.addon_handle, content)

        for video in lVideos:
            # Folders (pagination, programmes in search results) can be mixed with videos
            if isinstance(video, FolderVideo):
                urlPlugin, liz = self.folderItem(video)
                xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=urlPlugin, listitem=liz, isFolder=True)
            else:
                urlPlugin, liz = self.videoItem(video)
                xbmcplugin.addDirectoryItem(self.addon_handle, urlPlugin, liz, False)

        # Add sort methods for the virtual folder items
        xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_DURATION)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.addon_handle)

    def playbackFailed(self, message):
        notify(message)
        xbmcplugin.setResolvedUrl(self.addon_handle, False, xbmcgui.ListItem())

    def playVideo(self, videoId):
        xbmc.log("plugin.video.3cat -UI - playVideo " + str(videoId))

        if str(videoId).lower().startswith("http"):
            # Live channels are direct stream links
            xbmc.log("plugin.video.3cat - UI - is stream link")
            self.resolve(self.buildPlayItem(videoId))
            return

        # For video IDs, fetch the stream URL from the API
        apiJsonUrl = Urls.url_api_media.format(videoId)
        xbmc.log("plugin.video.3cat - UI - playVideo apijson url" + str(apiJsonUrl))
        try:
            json_data = getJson(apiJsonUrl)
        except Exception as e:
            xbmc.log("plugin.video.3cat - UI - Error fetching video: " + str(e), level=xbmc.LOGERROR)
            self.playbackFailed(self.tv3.strs.get('error'))
            return

        media = json_data.get('media') if isinstance(json_data, dict) else None
        files = [u for u in (media or {}).get('url') or [] if isinstance(u, dict) and u.get('file')]
        if not files:
            xbmc.log("plugin.video.3cat - UI - Error: no stream in API response", level=xbmc.LOGERROR)
            self.playbackFailed(self.tv3.strs.get('no_disponible'))
            return

        streamUrl = self.chooseStream(files)
        xbmc.log("plugin.video.3cat - UI - playVideo stream URL: " + str(streamUrl))
        play_item = self.buildPlayItem(streamUrl)

        if self.getSettingBool('subtitles', True):
            subtitles = self.downloadSubtitles(json_data.get('subtitols'))
            if subtitles:
                play_item.setSubtitles(subtitles)

        self.resolve(play_item)

    def chooseStream(self, files):
        """Pick the stream to play from the 'url' list of the media API.

        3cat offers an adaptive DASH stream and a fixed 720p MP4. DASH is the default, but
        on slow devices it can stay at a low, pixelated quality, so the MP4 can be chosen
        in the settings.
        """
        def kind(f):
            path = urllib.parse.urlparse(f['file']).path.lower()
            return path.rsplit('.', 1)[-1] if '.' in path else ''

        def height(f):
            match = re.match(r'(\d+)', str(f.get('label', '')))
            return int(match.group(1)) if match else 0

        adaptive = [f for f in files if kind(f) in ('mpd', 'm3u8')]
        mp4 = sorted((f for f in files if kind(f) == 'mp4'), key=height, reverse=True)

        if self.getSettingInt('stream_format', FORMAT_ADAPTIVE) == FORMAT_MP4 and mp4:
            return mp4[0]['file']
        if adaptive:
            return adaptive[0]['file']
        if mp4:
            return mp4[0]['file']
        return files[0]['file']

    def resolve(self, play_item):
        xbmcplugin.setResolvedUrl(handle=self.addon_handle, succeeded=True, listitem=play_item)

    def buildPlayItem(self, streamUrl):
        path = urllib.parse.urlparse(streamUrl).path.lower()
        if path.endswith('.m3u8'):
            return self.hlsItem(streamUrl)
        if path.endswith('.mp4'):
            return self.mp4Item(streamUrl)
        # DASH, and adaptive streaming as fallback for anything else
        return self.mpdItem(streamUrl)

    def downloadSubtitles(self, subtitols):
        """Save the subtitles of a video in Kodi's temp folder and return their paths.

        Kodi takes the language of an external subtitle from its file name
        ("<name>.<lang>.vtt"); the 3cat urls are just numbers, so they are renamed.
        """
        if not isinstance(subtitols, list):
            return []

        folder = xbmcvfs.translatePath(SUBTITLES_DIR)
        shutil.rmtree(folder, ignore_errors=True)
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError as e:
            xbmc.log("plugin.video.3cat - UI - cannot create subtitles folder: " + str(e), xbmc.LOGWARNING)
            return []

        jobs = []
        names = set()
        for sub in subtitols:
            if not isinstance(sub, dict) or not str(sub.get('url', '')).startswith('http'):
                continue
            iso = re.sub(r'[^a-z]', '', str(sub.get('iso', '')).lower())
            text = str(sub.get('text', '')).lower()
            ext = re.sub(r'[^a-z0-9]', '', str(sub.get('format') or 'vtt').lower()) or 'vtt'
            if iso == 'sps':
                # subtítols per a persones sordes (subtitles for the deaf and hard of hearing)
                name, lang = 'SDH', 'ca'
            else:
                name, lang = ('auto' if 'autom' in text else '3Cat'), (iso or 'und')
            filename = name + '.' + lang + '.' + ext
            n = 2
            while filename in names:
                filename = name + str(n) + '.' + lang + '.' + ext
                n += 1
            names.add(filename)
            jobs.append((sub['url'], os.path.join(folder, filename)))

        def download(job):
            url, path = job
            try:
                data = fetch(url, timeout=10, retries=1)
                with open(path, 'wb') as f:
                    f.write(data)
                return path
            except Exception as e:
                xbmc.log("plugin.video.3cat - UI - subtitle download failed " + url + ": " + str(e), xbmc.LOGWARNING)
                return None

        if not jobs:
            return []
        with ThreadPoolExecutor(max_workers=4) as pool:
            paths = list(pool.map(download, jobs))
        return [p for p in paths if p]

    def mp4Item(self, streamUrl):
        """Play a simple MP4 stream"""
        xbmc.log("plugin.video.3cat - UI - Playing MP4: " + streamUrl)
        play_item = xbmcgui.ListItem(path=streamUrl)
        play_item.setMimeType('video/mp4')
        play_item.setContentLookup(False)
        return play_item

    def hlsItem(self, streamUrl):
        """Play an HLS stream using inputstream.adaptive"""
        xbmc.log("plugin.video.3cat - UI - Playing HLS: " + streamUrl)
        play_item = xbmcgui.ListItem(path=streamUrl)
        try:
            from inputstreamhelper import Helper
            if Helper('hls').check_inputstream():
                play_item.setProperty('inputstream', 'inputstream.adaptive')
                play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
                play_item.setProperty('inputstream.adaptive.stream_headers', STREAM_HEADERS)
                play_item.setMimeType('application/vnd.apple.mpegurl')
                play_item.setContentLookup(False)
        except ImportError:
            # Fallback to direct play if inputstreamhelper is not available
            xbmc.log("plugin.video.3cat - UI - inputstreamhelper not available, trying direct play", level=xbmc.LOGWARNING)
        return play_item

    def mpdItem(self, streamUrl):
        """Play an MPD (DASH) stream using inputstream.adaptive with optional DRM"""
        xbmc.log("plugin.video.3cat - UI - Playing MPD: " + streamUrl)
        play_item = xbmcgui.ListItem(path=streamUrl)
        try:
            from inputstreamhelper import Helper
        except ImportError:
            xbmc.log("plugin.video.3cat - UI - inputstreamhelper not available, trying direct play", level=xbmc.LOGWARNING)
            return play_item

        # Check if this stream might need DRM
        mpd_content = ''
        try:
            mpd_content = fetch(streamUrl, timeout=10, retries=0).decode('utf-8', errors='replace')
        except Exception as e:
            # If we can't check, assume no DRM is needed
            xbmc.log("plugin.video.3cat - UI - cannot read MPD to check DRM: " + str(e), level=xbmc.LOGWARNING)
        needs_drm = 'ContentProtection' in mpd_content
        if needs_drm:
            xbmc.log("plugin.video.3cat - UI - DRM content protection detected", level=xbmc.LOGINFO)

        # Initialize inputstream helper with or without DRM
        is_helper = Helper(PROTOCOL, drm=DRM) if needs_drm else Helper(PROTOCOL)
        if not is_helper.check_inputstream():
            # Fallback to direct play if inputstream.adaptive is not available
            xbmc.log("plugin.video.3cat - UI - inputstream.adaptive not available, trying direct play", level=xbmc.LOGWARNING)
            return play_item

        play_item.setProperty('inputstream', 'inputstream.adaptive')
        play_item.setProperty('inputstream.adaptive.stream_headers', STREAM_HEADERS)
        play_item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
        play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
        play_item.setMimeType('application/dash+xml')
        play_item.setContentLookup(False)

        # Only set DRM properties if needed
        if needs_drm:
            # Try to extract license URL from the MPD if available
            license_url = self.extract_license_url_from_mpd(mpd_content) or LICENSE_URL
            if license_url:
                play_item.setProperty('inputstream.adaptive.license_type', DRM)
                play_item.setProperty('inputstream.adaptive.license_key', license_url + '||R{SSM}|')
                xbmc.log("plugin.video.3cat - UI - Using license URL: " + license_url, level=xbmc.LOGINFO)

        return play_item

    def extract_license_url_from_mpd(self, mpd_content):
        """Try to extract license URL from MPD content if present"""
        license_url_match = re.search(r'licenseUrl="([^"]+)"', mpd_content)
        return license_url_match.group(1) if license_url_match else None
