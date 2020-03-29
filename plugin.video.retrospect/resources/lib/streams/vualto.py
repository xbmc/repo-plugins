# SPDX-License-Identifier: CC-BY-NC-SA-4.0
from resources.lib.addonsettings import AddonSettings
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.subtitlehelper import SubtitleHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem
from resources.lib.streams.m3u8 import M3u8
from resources.lib.streams.mpd import Mpd
from resources.lib.urihandler import UriHandler
from resources.lib.chn_class import Channel


class Vualto(object):
    def __init__(self, channel, client_id):
        """

        :param Channel channel:
        :param str client_id:   The client ID to use

        """

        self.client_id = client_id
        self.channel = channel

    def get_stream_info(self, item, mzid, live=False, hls_over_dash=False):  # NOSONAR
        """ Updates an item with Vualto stream data.

        :param MediaItem item:      The Mediaitem to update
        :param str mzid:            The MZ ID of the stream
        :param bool live:           Indicator if the stream is live or not
        :param bool hls_over_dash:  Should we prefer HLS over Dash?

        :return: An updated MediaItem
        :rtype: MediaItem

        """

        # We need a player token
        token_data = UriHandler.open("https://media-services-public.vrt.be/"
                                     "vualto-video-aggregator-web/rest/external/v1/tokens", data="",
                                     additional_headers={"Content-Type": "application/json"})

        token = JsonHelper(token_data).get_value("vrtPlayerToken")

        asset_url = "https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/" \
                    "external/v1/videos/{0}?vrtPlayerToken={1}&client={2}" \
            .format(HtmlEntityHelper.url_encode(mzid), HtmlEntityHelper.url_encode(token),
                    HtmlEntityHelper.url_encode(self.client_id))
        asset_data = UriHandler.open(asset_url, no_cache=True)
        asset_data = JsonHelper(asset_data)

        drm_key = asset_data.get_value("drm")
        drm_protected = drm_key is not None
        adaptive_available = AddonSettings.use_adaptive_stream_add_on(
            with_encryption=drm_protected, channel=self.channel)
        part = item.create_new_empty_media_part()
        srt = None

        # see if we prefer hls over dash
        hls_prio = 2 if hls_over_dash else 0

        for target_url in asset_data.get_value("targetUrls"):
            video_type = target_url["type"]
            video_url = target_url["url"]

            if video_type == "hls_aes" and drm_protected and adaptive_available:
                # no difference in encrypted or not.
                Logger.debug("Found HLS AES encrypted stream and a DRM key")
                stream = part.append_media_stream(video_url, hls_prio)
                M3u8.set_input_stream_addon_input(stream)

            elif video_type == "hls" and not drm_protected:
                # no difference in encrypted or not.
                if adaptive_available:
                    Logger.debug("Found standard HLS stream and without DRM protection")
                    stream = part.append_media_stream(video_url, hls_prio)
                    M3u8.set_input_stream_addon_input(stream)
                else:
                    m3u8_data = UriHandler.open(video_url)
                    for s, b, a in M3u8.get_streams_from_m3u8(video_url,
                                                              play_list_data=m3u8_data,
                                                              map_audio=True):
                        item.complete = True
                        if a:
                            audio_part = a.rsplit("-", 1)[-1]
                            audio_part = "-%s" % (audio_part,)
                            s = s.replace(".m3u8", audio_part)
                        part.append_media_stream(s, b)

                    srt = M3u8.get_subtitle(video_url, play_list_data=m3u8_data)
                    if not srt or live:
                        # If there is not SRT don't download it. If it a live stream with subs,
                        # don't use it as it is not supported by Kodi
                        continue

                    srt = srt.replace(".m3u8", ".vtt")
                    part.Subtitle = SubtitleHelper.download_subtitle(srt, format="webvtt")

            elif video_type == "mpeg_dash" and adaptive_available:
                if not drm_protected:
                    Logger.debug("Found standard MPD stream and without DRM protection")
                    stream = part.append_media_stream(video_url, 1)
                    Mpd.set_input_stream_addon_input(stream)
                else:
                    stream = part.append_media_stream(video_url, 1)
                    encryption_json = '{{"token":"{0}","drm_info":[D{{SSM}}],"kid":"{{KID}}"}}' \
                        .format(drm_key)
                    encryption_key = Mpd.get_license_key(
                        key_url="https://widevine-proxy.drm.technology/proxy",
                        key_type="D",
                        key_value=encryption_json,
                        key_headers={"Content-Type": "text/plain;charset=UTF-8"}
                    )
                    Mpd.set_input_stream_addon_input(stream, license_key=encryption_key)

            if video_type.startswith("hls") and srt is None:
                srt = M3u8.get_subtitle(video_url)
                if not srt or live:
                    # If there is not SRT don't download it. If it a live stream with subs,
                    # don't use it as it is not supported by Kodi
                    continue

                srt = srt.replace(".m3u8", ".vtt")
                part.Subtitle = SubtitleHelper.download_subtitle(srt, format="webvtt")

            item.complete = True
        return item
