import base64
import json
import os
import re
import struct
import sys
import time
from urllib.error import URLError
from urllib.parse import quote, unquote, urljoin
from urllib.request import Request, urlopen
from xml.etree import ElementTree

import xbmcaddon
from xbmc import PlayList, PLAYLIST_VIDEO, Player, Keyboard, executebuiltin, getCondVisibility, getInfoLabel, log, LOGDEBUG
from xbmcgui import ListItem, Dialog, DialogProgress
from xbmcaddon import Addon
from xbmcplugin import addDirectoryItem, endOfDirectory, setContent, setResolvedUrl, addSortMethod, SORT_METHOD_VIDEO_TITLE, SORT_METHOD_DATE
import xbmcvfs
import inputstreamhelper

from directory import Directory


class Kodi:
    version_regex = r"plugin:\/\/([^\/]+)"
    addon_id = re.search(version_regex, sys.argv[0]).groups()[0]
    addon = Addon()
    data_folder = xbmcvfs.translatePath("special://profile/addon_data/%s" % addon_id)
    kodi_major_version = int(getInfoLabel('System.BuildVersion').split('.')[0])

    input_stream_protocol = 'mpd'
    input_stream_drm_version = 'com.widevine.alpha'
    input_stream_mime = 'application/dash+xml'
    input_stream_license_contenttype = 'application/octet-stream'
    widevine_system_id = 'edef8ba979d64acea3c827dcd51d21ed'
    timeshift_resolution_limit = '1024x576'

    geo_lock = False
    max_cache_age = 60 * 60 * 24

    def __init__(self, plugin):
        self.plugin = plugin
        self.init_storage()
        self.base_path = self.addon.getAddonInfo('path')
        self.resource_path = os.path.join(self.base_path, "resources")
        self.use_subtitles = self.addon.getSetting('useSubtitles') == 'true'
        self.use_segments = self.addon.getSetting('useSegments') == 'true'
        self.show_segments = self.addon.getSetting('showSegments') == 'true'
        self.use_timeshift = self.addon.getSetting('useTimeshift') == 'true'
        self.hide_audio_description_content = self.addon.getSetting('hideAD') == 'true'
        self.hide_sign_language_content = self.addon.getSetting('hideOEGS') == 'true'
        self.useragent = self.addon.getSetting('userAgent')
        self.pager_limit = int(self.addon.getSetting('pagerLimit'))
        self.max_cache_age = int(self.addon.getSetting('maxCacheAge')) * 60 * 60 * 24

    def init_storage(self):
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)

    def translate(self, translation_id):
        translation = self.addon.getLocalizedString
        return translation(translation_id)

    def get_translation(self, translation_id, fallback, replace=None):
        translation = self.translate(translation_id)
        if translation:
            if replace is not None:
                return replace % translation

            return translation
        return fallback

    def is_geo_locked(self) -> bool:
        return self.geo_lock

    def hide_audio_description(self) -> bool:
        return self.hide_audio_description_content

    def hide_sign_language(self) -> bool:
        return self.hide_sign_language_content

    def hide_accessibility_menu(self) -> bool:
        return self.hide_sign_language_content and self.hide_audio_description_content and not self.use_subtitles

    def set_geo_lock(self, lock):
        self.geo_lock = lock

    def hide_content(self, item) -> bool:
        if self.hide_audio_description_content and item.has_audio_description():
            self.log("Hiding %s because AD content hide is enabled in settings" % item.label())
            return True
        if self.hide_sign_language_content and item.has_sign_language():
            self.log("Hiding %s because OEGS content hide is enabled in settings" % item.label())
            return True
        if self.geo_lock and item.is_geo_locked():
            self.log("Hiding %s because GEO Lock is active for your ISP" % item.label())
            return True
        return False

    def render(self, item):
        if not self.hide_content(item):
            if item.is_playable():
                list_item = self.render_video(item)
                link = item.url()
                route = self.plugin.url_for_path(link)
                folder = self.use_segments and self.show_segments and item.has_segments()
                addDirectoryItem(self.plugin.handle, url=route, listitem=list_item, isFolder=folder)
            else:
                list_item = self.render_directory(item)
                link = item.url()
                route = self.plugin.url_for_path(link)
                addDirectoryItem(self.plugin.handle, url=route, listitem=list_item, isFolder=True)

    def restart(self, video):
        self.log("Running Restart Play Action")
        play_item = self.render_video(video, playback=True)
        play_item.setProperty('inputstream.adaptive.play_timeshift_buffer', 'true')
        streaming_url = video.get_stream().get('url')
        Player().play(streaming_url, play_item)

    def build_stream_url(self, url):
        return "%s|User-Agent=%s" % (url, self.useragent)

    def play_url(self, url):
        url = self.build_stream_url(unquote(url))
        play_item = ListItem(path=url, offscreen=True)
        setResolvedUrl(self.plugin.handle, True, play_item)

    def play(self, videos):
        if len(videos) < 1:
            Dialog().notification('No Stream available', 'Unable to find a stream for this content', xbmcaddon.Addon().getAddonInfo('icon'))
        self.log("Running Play Action")
        playlist = PlayList(PLAYLIST_VIDEO)
        tracks = []
        for video in videos:
            tracks.append(video)

        if len(tracks) > 1:
            if self.show_segments:
                for track in tracks:
                    self.render(track)
            else:
                items = []
                for track in tracks:
                    play_item = self.render_video(track, playback=True)
                    play_stream = self.build_stream_url(unquote(track.get_stream().get('url')))
                    play_item.setPath(play_stream)
                    items.append((play_stream, play_item))
                plugin_url = sys.argv[0] + sys.argv[2]
                position = playlist.getposition()
                if 0 <= position < playlist.size() and playlist[position].getPath() == plugin_url:
                    self.log("Resolving Playlist item %d with %d segments" % (position, len(items)))
                    for index, (play_stream, play_item) in enumerate(items[1:], start=position + 1):
                        playlist.add(play_stream, play_item, index)
                    setResolvedUrl(self.plugin.handle, True, items[0][1])
                else:
                    self.log("Starting new Playlist with %d segments" % len(items))
                    playlist.clear()
                    for play_stream, play_item in items:
                        playlist.add(play_stream, play_item)
                    setResolvedUrl(self.plugin.handle, False, ListItem(offscreen=True))
                    Player().play(playlist)
        else:
            self.log("Playing Single Video")
            for track in tracks:
                play_item = self.render_video(track, playback=True)
                setResolvedUrl(self.plugin.handle, True, play_item)
                break

    def render_directory(self, directory) -> ListItem:
        title = directory.label()
        title2 = directory.label2()

        list_item = ListItem(offscreen=True)
        list_item.setContentLookup(False)
        list_item.setLabel(title)
        list_item.setLabel2(title2)
        item_info = self.build_info(directory)
        list_item.setInfo(type="Video", infoLabels=item_info)
        list_item.setIsFolder(not directory.is_playable())
        list_item.setProperty("IsPlayable", str(directory.is_playable()))
        item_art = self.build_art(directory)
        list_item.setArt(item_art)
        return list_item

    def render_video(self, teaser, playback=False) -> ListItem:
        title = teaser.label()
        title2 = teaser.label2()
        stream_url = self.build_stream_url(unquote(teaser.url()))

        headers = "User-Agent=%s" % quote(self.useragent)
        license_headers = "%s&Content-Type=%s" % (headers, quote(self.input_stream_license_contenttype))
        is_helper = inputstreamhelper.Helper(self.input_stream_protocol, drm=self.input_stream_drm_version)
        if is_helper.check_inputstream():
            list_item = ListItem(path=stream_url, offscreen=True)
            list_item.setContentLookup(False)

            if teaser.get_stream():
                self.log("Found Stream for Video %s" % teaser.label())
                self.log("Stream: (%s)" % teaser.url())
                stream_data = teaser.get_stream()
                list_item.setProperty('inputstream', is_helper.inputstream_addon)
                list_item.setProperty('inputstream.adaptive.manifest_headers', headers)
                list_item.setProperty('inputstream.adaptive.stream_headers', headers)
                if self.kodi_major_version < 21:
                    list_item.setProperty('inputstream.adaptive.manifest_type', self.input_stream_protocol)

                if self.use_subtitles and stream_data.get('subtitle') and stream_data.get('subtitle') is not None:
                    list_item.setSubtitles([stream_data.get('subtitle')])
                    list_item.addStreamInfo('subtitle', {'language': 'deu'})

                if stream_data['drm']:
                    self.log("Video %s is DRM protected. Adding DRM relevant parameters" % teaser.label())
                    list_item.setMimeType(self.input_stream_mime)
                    license_url = "%s?BrandGuid=%s&userToken=%s" % (stream_data.get('drm_widewine_url'), stream_data.get('drm_widewine_brand'), stream_data.get('drm_token'))
                    init_data = self.get_widevine_init_data(unquote(stream_data.get('url') or teaser.url())) if playback else None
                    if init_data and self.kodi_major_version >= 22:
                        drm_config = {self.input_stream_drm_version: {'init_data': init_data, 'license': {'server_url': license_url, 'req_headers': license_headers}}}
                        list_item.setProperty('inputstream.adaptive.drm', json.dumps(drm_config))
                    elif self.kodi_major_version >= 21 and not init_data:
                        list_item.setProperty('inputstream.adaptive.drm_legacy', '%s|%s|%s' % (self.input_stream_drm_version, license_url, license_headers))
                    else:
                        list_item.setProperty('inputstream.adaptive.license_type', self.input_stream_drm_version)
                        list_item.setProperty('inputstream.adaptive.license_key', license_url + '|' + license_headers + '|R{SSM}|')
                        if init_data and self.kodi_major_version == 21:
                            list_item.setProperty('inputstream.adaptive.license_data', init_data)
                    if init_data and not getCondVisibility('System.Platform.Android'):
                        if self.kodi_major_version >= 22:
                            list_item.setProperty('inputstream.adaptive.config', json.dumps({'resolution_limit': self.timeshift_resolution_limit}))
                        else:
                            list_item.setProperty('inputstream.adaptive.chooser_resolution_max', '640p')
            else:
                self.log("No Stream for Video %s (%s)" % (teaser.label(), teaser.url()), 'error')

            list_item.setLabel(title)
            list_item.setLabel2(title2)
            item_info = self.build_info(teaser)

            list_item.setInfo(type="Video", infoLabels=item_info)
            list_item.setIsFolder(not teaser.is_playable())
            list_item.setProperty("IsPlayable", str(teaser.is_playable()))
            video_w, video_h = teaser.get_resolution()
            list_item.addStreamInfo('video', {'aspect': '1.78', 'codec': 'h264', 'width': video_w, 'height': video_h, 'duration': teaser.get_duration()})
            list_item.addStreamInfo('audio', {'codec': 'aac', 'language': 'deu', 'channels': 2})

            item_art = self.build_art(teaser)
            list_item.setArt(item_art)

            context_menu = []
            context_menu_items = teaser.get_context_menu()
            for context_menu_item in context_menu_items:
                context_menu.append(self.build_context_menu(context_menu_item))
            list_item.addContextMenuItems(context_menu, replaceItems=True)
            return list_item
        if not teaser.get_stream():
            Dialog().notification('No Stream available', 'Unable to find a stream for %s' % title, xbmcaddon.Addon().getAddonInfo('icon'))
        elif not is_helper.check_inputstream():
            Dialog().notification('Inputstream Adaptive not available', 'Install Inputstream Adaptive and Inputstream Helper', xbmcaddon.Addon().getAddonInfo('icon'))

    def get_widevine_init_data(self, manifest_url):
        pssh_boxes = []
        try:
            mpd = ElementTree.fromstring(self.http_get(manifest_url))
            for period in self.xml_children(mpd, 'Period'):
                for adaptation_set in self.xml_children(period, 'AdaptationSet'):
                    protections = [cp for cp in self.xml_children(adaptation_set, 'ContentProtection')
                                   if self.widevine_system_id in cp.get('schemeIdUri', '').replace('-', '').lower()]
                    if not protections:
                        continue
                    if any(self.xml_children(cp, 'pssh') for cp in protections):
                        return None
                    for representation in self.xml_children(adaptation_set, 'Representation'):
                        init_url = self.get_init_url(manifest_url, (mpd, period, adaptation_set, representation))
                        pssh = self.find_widevine_pssh(self.http_get(init_url)) if init_url else None
                        if pssh:
                            pssh_boxes.append(pssh)
        except (URLError, ElementTree.ParseError, ValueError) as error:
            self.log("Unable to read Widevine PSSH: %s" % error, 'error')
            return None
        return self.merge_widevine_pssh(pssh_boxes)

    def merge_widevine_pssh(self, pssh_boxes):
        payloads = [box[32:] for box in pssh_boxes if box[8] == 0]
        key_ids = []
        for payload in payloads:
            for key_id in re.findall(rb'\x12\x10(.{16})', payload, re.DOTALL):
                if key_id not in key_ids:
                    key_ids.append(key_id)
        if not key_ids:
            return None
        payload = payloads[0].replace(b'\x12\x10' + key_ids[0], b''.join(b'\x12\x10' + key_id for key_id in key_ids), 1)
        box = b'pssh' + bytes(4) + bytes.fromhex(self.widevine_system_id) + struct.pack('>I', len(payload)) + payload
        self.log("Using Widevine PSSH with %d key ids from init segments" % len(key_ids))
        return base64.b64encode(struct.pack('>I', len(box) + 4) + box).decode('ascii')

    def get_init_url(self, manifest_url, elements):
        representation = elements[-1]
        templates = self.xml_children(representation, 'SegmentTemplate') or self.xml_children(elements[-2], 'SegmentTemplate')
        if not templates or not templates[0].get('initialization'):
            return None
        init_path = templates[0].get('initialization').replace('$RepresentationID$', representation.get('id', ''))
        init_path = init_path.replace('$Bandwidth$', representation.get('bandwidth', ''))
        base_url = manifest_url
        for element in elements:
            base_urls = self.xml_children(element, 'BaseURL')
            if base_urls and base_urls[0].text:
                base_url = urljoin(base_url, base_urls[0].text.strip())
        return urljoin(base_url, init_path)

    def http_get(self, url):
        with urlopen(Request(url, headers={'User-Agent': self.useragent}), timeout=10) as response:
            return response.read()

    @staticmethod
    def xml_children(element, name):
        return [child for child in element if child.tag.split('}')[-1] == name]

    def find_widevine_pssh(self, data):
        system_id = bytes.fromhex(self.widevine_system_id)
        index = data.find(b'pssh')
        while index >= 4:
            size = struct.unpack('>I', data[index - 4:index])[0]
            box = data[index - 4:index - 4 + size]
            if box[12:28] == system_id:
                return box
            index = data.find(b'pssh', index + 4)
        return None

    def build_info(self, item) -> dict:
        desc_prefix = self.build_meta_description(item)
        if desc_prefix is not None and item.get_description():
            generated_description = desc_prefix + item.get_description()
            generated_outline = desc_prefix + self.truncate_string(item.get_description())
        else:
            generated_description = item.get_description()
            generated_outline = self.truncate_string(item.get_description())
        return {
            'title': item.label(),
            'originaltitle': item.label(),
            'sorttitle': item.label(),
            'tvshowtitle': item.label(),
            'plot': generated_description,
            'plotoutline': generated_outline,
            'genre': item.genre(),
            'tag': item.genre(),
            'aired': item.date(),
            'country': item.country(),
            'year': item.year(),
            'mediatype': item.media_type(),
            'cast': item.get_cast()
        }

    def build_art(self, item) -> dict:
        return {
            'thumb': item.thumbnail or self.get_media('icon.jpg'),
            'poster': item.poster or self.get_media('poster.jpg'),
            'fanart': item.backdrop or self.get_media('fanart.jpg'),
        }

    def build_context_menu(self, item):
        route = self.plugin.url_for_path(item.get('url'))
        if item.get('type') == 'run':
            return item.get('title'), 'RunPlugin(%s)' % route

        return item.get('title'), 'Container.Update(%s)' % route

    def list_callback(self, content_type="movies", sort=False) -> None:
        if content_type:
            setContent(self.plugin.handle, content_type)
        if sort:
            addSortMethod(int(sys.argv[1]), SORT_METHOD_DATE)
            addSortMethod(int(sys.argv[1]), SORT_METHOD_VIDEO_TITLE)
        endOfDirectory(self.plugin.handle, True)

    def get_media(self, filename):
        return os.path.join(self.resource_path, filename)

    def clear_stored_directories(self, storage_key):
        target_file = '%s.json' % storage_key
        self.remove_file(target_file)

    def get_stored_directories(self, storage_key):
        target_file = '%s.json' % storage_key
        self.init_storage()
        json_data = self.load_json(target_file)
        directories = []
        for json_item in json_data:
            directory = Directory(json_item.get('title'), json_item.get('description'), json_item.get('link'), translator=self)
            directories.append(directory)
        return directories

    def store_directory(self, directory, storage_key):
        target_file = '%s.json' % storage_key
        self.init_storage()

        json_data = self.load_json(target_file)
        directory_json = {
            'title': directory.title,
            'description': directory.description,
            'link': directory.url()
        }

        if json_data:
            json_data.append(directory_json)
        else:
            json_data = [directory_json]
        self.save_json(json_data, target_file)

    def remove_file(self, file) -> bool:
        file = "%s/%s" % (self.data_folder, file)
        try:
            os.remove(file)
            return True
        except FileNotFoundError:
            self.log("File %s could not be found. Skipping remove action." % file, 'warning')
            return False

    def get_cached_file(self, file) -> tuple:
        channel_map_age = self.get_file_age(file)

        if self.max_cache_age > channel_map_age >= 0:
            self.log("Channel Cache is valid. File age lower than %s seconds (%d seconds)" % (self.max_cache_age, channel_map_age))
            data = self.load_json(file)
            if not len(data):
                cached = False
            else:
                cached = True
        else:
            self.log("Channel Cache is invalid. Reloading because file age larger than %s seconds (%d seconds)" % (self.max_cache_age, channel_map_age))
            cached = False
            self.remove_file(file)
            data = {}
        return data, cached

    def get_file_age(self, file) -> int:
        file = "%s/%s" % (self.data_folder, file)
        try:
            st = os.stat(file)
            age_seconds = int(time.time() - st.st_mtime)
            self.log("Cache Age %d seconds" % age_seconds)
            return age_seconds
        except FileNotFoundError:
            self.log("File %s could not be found" % file, 'warning')
            return -1

    def save_json(self, json_data, file) -> bool:
        file = "%s/%s" % (self.data_folder, file)
        try:
            with open(file, 'w') as data_file:
                data_file.write(json.dumps(json_data))
            data_file.close()
            return True
        except TypeError:
            self.log("Json file format for %s was invalid. Removing file ..." % file, 'warning')
            os.remove(file)
            return False
        except PermissionError:
            self.log("Permission to File %s was denied" % file, 'warning')
            return False

    def load_json(self, file) -> list:
        file = "%s/%s" % (self.data_folder, file)
        self.log("Loading JSON from %s" % file)
        try:
            with open(file, 'r') as data_file:
                data = json.load(data_file)
            return data
        except FileNotFoundError:
            self.log("File %s could not be found" % file, 'warning')
            return []

    @staticmethod
    def log(msg, msg_type='info'):
        log("[%s][ORFON][KODI] %s" % (msg_type.upper(), msg), LOGDEBUG)

    @staticmethod
    def execute(command):
        executebuiltin(command)

    @staticmethod
    def select_dialog(title, items):
        select_dialog = Dialog()
        selected = select_dialog.select(title, items)
        if selected != -1:
            return selected
        return False

    @staticmethod
    def get_progress_dialog(title, description=""):
        progress = DialogProgress()
        progress.create(title, description)
        return progress

    @staticmethod
    def build_meta_description(item):
        desc = ""
        meta_desc = item.get_meta_description()
        for label in meta_desc:
            desc += "\n[COLOR blue][LIGHT]%s[/LIGHT][/COLOR] %s" % (label, meta_desc[label])
        if desc != "":
            desc += "\n\n"
        return desc

    @staticmethod
    def truncate_string(str_value, max_len=400) -> str:
        if str_value:
            return str_value[:max_len] + (str_value[max_len:] and ' ...')

    @staticmethod
    def build_url(url, args) -> str:
        arg_str = ""
        for arg in args:
            if not arg_str:
                arg_str = "?%s=%s" % (arg, args.get(arg)[0])
            else:
                arg_str += "&%s=%s" % (arg, args.get(arg)[0])
        return "%s%s" % (url, arg_str)

    @staticmethod
    def get_keyboard_input() -> str:
        keyboard = Keyboard()
        keyboard.doModal()
        if keyboard.isConfirmed():
            return keyboard.getText()
        return ""
