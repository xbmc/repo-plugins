# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import xbmc

from resources.lib.logger import Logger
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.regexer import Regexer
from resources.lib.urihandler import UriHandler
from resources.lib.proxyinfo import ProxyInfo


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
    def get_streams_from_you_tube(url, proxy=None, use_add_on=True):
        """ Parsers standard YouTube videos and returns a list of tuples with streams and
        bitrates that can be used by other methods.

        :param ProxyInfo proxy:     The proxy to use for opening
        :param str url:             The url to download
        :param bool use_add_on:     Should we use the Youtube add-on if available

        Can be used like this:

            part = item.create_new_empty_media_part()
            for s, b in YouTube.get_streams_from_you_tube(url, self.proxy):
                item.complete = True
                # s = self.get_verifiable_video_url(s)
                part.append_media_stream(s, b)

        :return: a list of streams with their bitrate and optionally the audio streams.
        :rtype: list[tuple[str,str]]

        """

        you_tube_streams = []
        you_tube_add_on_available = xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")') == 1

        if you_tube_add_on_available and use_add_on:
            Logger.info("Found Youtube add-on. Using it")
            you_tube_streams.append((YouTube.__play_you_tube_url(url), 0))
            Logger.trace(you_tube_streams)
            return you_tube_streams

        Logger.info("No Kodi Youtube Video add-on was found. Falling back.")

        if "watch?v=" in url:
            video_id = url.split("?v=")[-1]
            Logger.debug("Using Youtube ID '%s' retrieved from '%s'", video_id, url)
            # get the meta data url
            url = "https://www.youtube.com/get_video_info?hl=en_GB&asv=3&video_id=%s" % (video_id, )

        elif "get_video_info" not in url:
            Logger.error("Invalid Youtube URL specified: '%s'", url)
            return []

        data = UriHandler.open(url, proxy=proxy)
        if isinstance(data, bytes):
            data = data.decode()
        # get the stream data from the page

        # Up to 720p with audio and video combined.
        url_encoded_fmt_stream_map = Regexer.do_regex("url_encoded_fmt_stream_map=([^&]+)", data)
        # Up to 4K with audio and video split.
        # url_encoded_fmt_stream_map = Regexer.do_regex("adaptive_fmts=([^&]+)", data)
        url_encoded_fmt_stream_map_data = HtmlEntityHelper.url_decode(url_encoded_fmt_stream_map[0])
        # split per stream
        streams = url_encoded_fmt_stream_map_data.split(',')

        for stream in streams:
            # let's create a new part
            # noinspection PyTypeChecker
            qs_data = dict([x.split("=") for x in stream.split("&")])
            Logger.trace(qs_data)

            if "itag" in qs_data and "bitrate" not in qs_data:
                i_tag = int(qs_data.get('itag', -1))
                stream_encoding = YouTube.__YouTubeEncodings.get(i_tag, None)
                if stream_encoding is None:
                    # if the i_tag was not in the list, skip it.
                    Logger.debug(
                        "Not using i_tag %s as it is not in the list of supported encodings.", i_tag)
                    continue
                bitrate = stream_encoding[0]
            else:
                bitrate = int(qs_data['bitrate'])/1000

            signature = qs_data.get('s', None)
            quality = qs_data.get('quality_label', qs_data.get('quality'))
            if not quality:
                Logger.debug("Missing 'quality_label', skipping: %s", qs_data)
                continue

            video_url = HtmlEntityHelper.url_decode(qs_data['url'])
            if signature is None:
                url = video_url
            else:
                url = "%s&signature=%s" % (video_url, signature)

            you_tube_streams.append((url, bitrate))

        return you_tube_streams

    @staticmethod
    def __play_you_tube_url(url):
        """ Plays a YouTube URL with the YouTube addon from XBMC.

        url = YouTube.PlayYouTubeUrl(url[0])
        part.append_media_stream(url, bitrate=0)

        @param url: The URL to playback in the format: http://www.youtube.com/watch?v=878-LYQEcPs
        @return: The plugin:// url for the YouTube addon
        """

        if "youtube" in url:
            Logger.debug("Determining Add-on URL for YouTube: %s", url)
            url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=%s" % (url.split("v=")[1], )
        return url
