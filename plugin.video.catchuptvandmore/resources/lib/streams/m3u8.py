# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re

import xbmcgui
# noinspection PyUnresolvedReferences
from codequick import Script
import urlquick

from resources.lib.addon_utils import Quality
from resources.lib.streams.mediastream import MediaStream

TYPE_INDEX = 0
BITRATE_INDEX = 1
ID_INDEX = 2
RESOLUTION_INDEX = 2
URL_INDEX = 3

# add an offset to include the selected bitrate, we should have more than the bitrate found
BITRATE_OFFSET = 100


class M3u8(object):
    # EXT-X-STREAM-INF:BANDWIDTH=1888000,CODECS="avc1.4d481f,mp4a.40.2",RESOLUTION=1024x576
    # PATTERN_RESOLUTIONS = re.compile(r'#EXT-X-STREAM-INF:.*RESOLUTION=([^\n]*)\n(.*\.m3u8)')
    PATTERN_STREAMS = re.compile(
        r"(#\w[^:]+)[^\n]+BANDWIDTH=(\d+)\d{3}[^\n]*RESOLUTION=(\d+x\d+)[^\n]*\W+([^\n]+.m3u8[^\n\r]*)")
    PATTERN_AUDIO1 = re.compile(r'(#\w[^:]+):TYPE=AUDIO()[^\r\n]+ID="([^"]+)"[^\n\r]+URI="([^"]+.m3u8[^"]*)"')
    PATTERN_AUDIO2 = re.compile(
        r'(#\w[^:]+)[^\n]+BANDWIDTH=(\d+)\d{3}(?:[^\r\n]*AUDIO="([^"]+)")?[^\n]*\W+([^\n]+.m3u8[^\n\r]*)')

    def __init__(self, url, headers=None, append_query_string=False, map_audio=False, verify=True):

        self.verify = verify
        self.map_audio = map_audio
        self.append_query_string = append_query_string
        self.headers = headers
        self.url = url

        self.media_streams = []  # type: list[MediaStream]
        self.media_streams_checked = False

    @staticmethod
    def get_streams(url, headers=None, append_query_string=False, map_audio=False, verify=True):
        """ Parsers standard M3U8 lists and returns a list of tuples with streams and bitrates and resolutions that
        can be used by other methods.

        :param dict[str,str] headers:       Possible HTTP Headers
        :param str url:                     The url to download
        :param bool append_query_string:    Should the existing query string be appended?
        :param bool map_audio:              Map audio streams
        :param bool verify:                 verify ssl

        :return: a list of streams with their bitrate and their resolution and optionally the audio streams.
        :rtype: list[tuple[str,str,str]|tuple[str,str,str,str]]

        """

        streams = []
        resp = urlquick.get(url, headers=headers, max_age=-1, verify=verify)
        data = resp.text

        qs = None
        if append_query_string and "?" in url:
            base, qs = url.split("?", 1)
            Script.log("Going to append QS: %s" % qs, lvl=Script.INFO)
        elif "?" in url:
            base, qs = url.split("?", 1)
            Script.log("Ignoring QS: %s" % qs, lvl=Script.INFO)
            qs = None
        else:
            base = url

        Script.log("Processing M3U8 Streams: %s" % url, lvl=Script.DEBUG)

        # If we need audio
        if map_audio:
            found_streams = M3u8.PATTERN_AUDIO1.findall(data)
            found_streams += M3u8.PATTERN_AUDIO2.findall(data)
        else:
            found_streams = M3u8.PATTERN_STREAMS.findall(data)

        audio_streams = {}
        base_url = base[:base.rindex("/")]
        for found_stream in found_streams:
            if "#EXT-X-I-FRAME" in found_stream[TYPE_INDEX]:
                continue

            if "://" not in found_stream[URL_INDEX]:
                stream = "%s/%s" % (base_url, found_stream[URL_INDEX])
            else:
                stream = found_stream[URL_INDEX]
            bitrate = found_stream[BITRATE_INDEX]
            if map_audio:
                resolution = "0x0"
            else:
                resolution = found_stream[RESOLUTION_INDEX]

            if qs is not None and stream.endswith("?null="):
                stream = stream.replace("?null=", "?%s" % (qs,))
            elif qs is not None and "?" in stream:
                stream = "%s&%s" % (stream, qs)
            elif qs is not None:
                stream = "%s?%s" % (stream, qs)

            if map_audio and "#EXT-X-MEDIA" in found_stream[TYPE_INDEX]:
                Script.log("Found audio stream: %s -> %s" % (found_stream[ID_INDEX], stream), lvl=Script.DEBUG)
                audio_streams[found_stream[ID_INDEX]] = stream
                continue

            if map_audio:
                streams.append((stream, bitrate, resolution, audio_streams.get(found_stream[ID_INDEX]) or None))
            else:
                streams.append((stream, bitrate, resolution))

        Script.log("Found %s substreams in M3U8" % len(streams), lvl=Script.DEBUG)
        return streams

    @staticmethod
    def get_media_streams(url, headers=None, append_query_string=False, map_audio=False, verify=True):
        media_streams = []
        if map_audio:
            for s, b, r, a in M3u8.get_streams(url, headers=headers, append_query_string=append_query_string,
                                               map_audio=True, verify=verify):
                if a:
                    audio_part = a.rsplit("-", 1)[-1]
                    audio_part = "-%s" % (audio_part,)
                    s = s.replace(".m3u8", audio_part)
                media_streams.append(MediaStream(s, b, r))

        for s, b, r in M3u8.get_streams(url, headers=headers, append_query_string=append_query_string, map_audio=False,
                                        verify=verify):
            media_streams.append(MediaStream(s, b, r))

        return media_streams

    def get_matching_stream(self, bitrate):
        """ Returns the MediaStream for the requested bitrate.

        Arguments:
        bitrate : integer - The bitrate of the stream in kbps

        Returns:
        The url of the stream with the requested bitrate.

        If bitrate is not specified the highest bitrate stream will be used.

        """

        if not self.media_streams_checked:
            self.media_streams = M3u8.get_media_streams(self.url, self.headers, self.append_query_string,
                                                        self.map_audio, self.verify)
            self.media_streams_checked = True

        # order the items by bitrate
        self.media_streams.sort(key=lambda s: s.bitrate)
        best_stream = None
        best_distance = None

        if bitrate == 0:
            # return the highest one
            return self.media_streams[-1]

        for stream in self.media_streams:
            if stream.bitrate is None:
                # no bitrate set, see if others are available
                continue

            # this is the bitrate-as-max-limit-method
            if stream.bitrate > bitrate:
                # if the bitrate is higher, continue for more
                continue
            # if commented ^^ , we get the closest-match-method

            # determine the distance till the bitrate
            distance = abs(bitrate - stream.bitrate)

            if best_distance is None or best_distance > distance:
                # this stream is better, so store it.
                best_distance = distance
                best_stream = stream

        if best_stream is None:
            # no match, take the lowest bitrate
            return self.media_streams[0]

        return best_stream

    def get_url_and_bitrate_for_quality(self):
        """ Returns the url and the bitrate for the requested quality.

         Returns:
         The url of the stream and the requested bitrate.

         """

        final_video_url = self.url
        desired_quality = Script.setting.get_string('quality')
        if desired_quality == "DEFAULT":
            return final_video_url, 0

        if not self.media_streams_checked:
            self.media_streams = M3u8.get_media_streams(self.url, self.headers, self.append_query_string,
                                                        self.map_audio, self.verify)
            self.media_streams_checked = True

        if len(self.media_streams) == 0:
            return final_video_url, 0

        all_video_resolutions = list(map(lambda x: x.resolution, self.media_streams))
        all_video_bitrates = list(map(lambda x: x.bitrate, self.media_streams))
        all_video_qualities = list(map(lambda x: 'resolution: %s, bitrate: %s'
                                                 % (x.resolution, x.bitrate), self.media_streams))
        all_videos_urls = list(map(lambda x: x.url, self.media_streams))

        if desired_quality == Quality['DIALOG']:
            selected_item = xbmcgui.Dialog().select(
                Script.localize(30709),
                all_video_qualities)
            if selected_item == -1:
                return None, None

            return all_videos_urls[selected_item], (all_video_bitrates[selected_item] + BITRATE_OFFSET)

        elif desired_quality == Quality['BEST']:
            max_resolution = 0
            url_best = self.url
            i = 0
            for data_video in all_video_resolutions:
                current_resolution = int(re.sub(r'x\d*', '', data_video))
                if current_resolution > max_resolution:
                    max_resolution = current_resolution
                    url_best = all_videos_urls[i]
                i = i + 1
            return url_best, 0  # you can return bitrate unlimited (0)

        elif desired_quality == Quality['WORST']:
            min_resolution = 99999999999999999999999
            url_worst = self.url
            bitrate_worst = 0
            i = 0
            for data_video in all_video_resolutions:
                current_resolution = int(re.sub(r'x\d*', '', data_video))
                if current_resolution < min_resolution:
                    min_resolution = current_resolution
                    url_worst = all_videos_urls[i]
                    bitrate_worst = all_video_bitrates[i]
                i = i + 1
            return url_worst, (bitrate_worst + BITRATE_OFFSET)

        return final_video_url, 0
