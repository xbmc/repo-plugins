# SPDX-License-Identifier: GPL-3.0-or-later

import xbmc
from resources.lib.addonsettings import AddonSettings

from resources.lib.logger import Logger
from resources.lib.xbmcwrapper import XbmcWrapper
from resources.lib.helpers.languagehelper import LanguageHelper


class YouTube(object):
    def __init__(self):
        """ Creates a Youtube Parsing class """
        pass

    # http://en.wikipedia.org/wiki/YouTube#Quality_and_codecs
    __YouTubeEncodings = {
        # Flash Video
        5: [314, "flv", "240p", "Sorenson H.263", "N/A", "0.25", "MP3", "64"],
        6: [864, "flv", "270p", "Sorenson H.263", "N/A", "0.8", "MP3", "64"],
        34: [628, "flv", "360p", "H.264", "Main", "0.5", "AAC", "128"],
        35: [1028, "flv", "480p", "H.264", "Main", "0.8-1", "AAC", "128"],

        # 3GP
        36: [208, "3gp", "240p", "MPEG-4 Visual", "Simple", "0.17", "AAC", "38"],
        13: [500, "3gp", "N/A", "MPEG-4 Visual", "N/A", "0.5", "AAC", "N/A"],
        17: [74, "3gp", "144p", "MPEG-4 Visual", "Simple", "0.05", "AAC", "24"],

        # MPEG-4
        18: [596, "mp4", "360p", "H.264", "Baseline", "0.5", "AAC", "96"],
        22: [2792, "mp4", "720p", "H.264", "High", "2-2.9", "AAC", "192"],
        37: [3800, "mp4", "1080p", "H.264", "High", "3-4.3", "AAC", "192"],
        38: [4500, "mp4", "3072p", "H.264", "High", "3.5-5", "AAC", "192"],
        82: [596, "mp4", "360p", "H.264", "3D", "0.5", "AAC", "96"],
        83: [596, "mp4", "240p", "H.264", "3D", "0.5", "AAC", "96"],
        84: [2752, "mp4", "720p", "H.264", "3D", "2-2.9", "AAC", "152"],
        85: [2752, "mp4", "520p", "H.264", "3D", "2-2.9", "AAC", "152"],

        # WebM
        43: [628, "webm", "360p", "VP8", "N/A", "0.5", "Vorbis", "128"],
        44: [1128, "webm", "480p", "VP8", "N/A", "1", "Vorbis", "128"],
        45: [2192, "webm", "720p", "VP8", "N/A", "2", "Vorbis", "192"],
        # 46: ["webm", "1080p", "VP8", "N/A", "N/A", "Vorbis", "192"],
        # 100: ["webm", "360p", "VP8", "3D", "N/A", "Vorbis", "128"],
        # 101: ["webm", "360p", "VP8", "3D", "N/A", "Vorbis", "192"],
        # 102: ["webm", "720p", "VP8", "3D", "N/A", "Vorbis", "192"]
    }

    @staticmethod
    def get_streams_from_you_tube(url, ignore_add_on_status=True):
        """ Parsers standard YouTube videos and returns a list of tuples with streams and
        bitrates that can be used by other methods.

        :param str url:                     The url to download.
        :param bool ignore_add_on_status:   Should we ignore the add-on check.

        Can be used like this:

            for s, b in YouTube.get_streams_from_you_tube(url):
                item.complete = True
                # s = self.get_verifiable_video_url(s)
                item.add_stream(s, b)

        :return: a list of streams with their bitrate and optionally the audio streams.
        :rtype: list[tuple[str,str]]

        """

        you_tube_streams = []

        if AddonSettings.is_min_version(AddonSettings.KodiMatrix):
            you_tube_add_on_available = xbmc.getCondVisibility('System.HasAddon(plugin.video.youtube) + System.AddonIsEnabled(plugin.video.youtube)') == 1
        else:
            you_tube_add_on_available = xbmc.getCondVisibility('System.HasAddon(plugin.video.youtube)') == 1

        if you_tube_add_on_available or ignore_add_on_status:
            Logger.info("Found Youtube add-on. Using it")
            you_tube_streams.append((YouTube.__play_you_tube_url(url), 0))
            Logger.trace(you_tube_streams)
            return you_tube_streams

        Logger.info("No Kodi Youtube Video add-on was found. Falling back.")
        XbmcWrapper.show_dialog(LanguageHelper.ErrorId, LanguageHelper.YouTubeMissing)
        return you_tube_streams

    @staticmethod
    def __play_you_tube_url(url):
        """ Plays a YouTube URL with the YouTube addon from XBMC.

        url = YouTube.PlayYouTubeUrl(url[0])
        part.append_media_stream(url, bitrate=0)

        :param str url: The URL to playback in the format: http://www.youtube.com/watch?v=878-LYQEcPs

        :return: The plugin:// url for the YouTube addon
        :rtype: str

        """

        if "youtube" in url:
            Logger.debug("Determining Add-on URL for YouTube: %s", url)
            url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=%s" % (url.split("v=")[1], )
        return url
