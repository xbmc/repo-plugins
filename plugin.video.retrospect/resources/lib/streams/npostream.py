# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.regexer import Regexer
from resources.lib.streams.m3u8 import M3u8
from resources.lib.streams.mpd import Mpd
from resources.lib.helpers.subtitlehelper import SubtitleHelper
from resources.lib.urihandler import UriHandler
from resources.lib.logger import Logger
from resources.lib.proxyinfo import ProxyInfo


class NpoStream(object):
    def __init__(self):
        pass

    @staticmethod
    def get_subtitle(stream_id, proxy=None):
        """ Downloads a subtitle for a POMS id.

        :param str stream_id:   The POMS id.
        :param ProxyInfo proxy: The proxy to use

        :return: The full patch of the cached SRT file.
        :rtype: str

        """

        sub_title_url = "http://tt888.omroep.nl/tt888/%s" % (stream_id,)
        return SubtitleHelper.download_subtitle(sub_title_url, stream_id + ".srt", format='srt', proxy=proxy)

    @staticmethod
    def add_mpd_stream_from_npo(url, episode_id, part, proxy=None, headers=None, live=False):
        """ Extracts the Dash streams for the given url or episode id

        :param str|None url:        The url to download
        :param str episode_id:      The NPO episode ID
        :param dict headers:        Possible HTTP Headers
        :param ProxyInfo proxy:     The proxy to use for opening
        :param bool live:           Is this a live stream?

        :rtype: str|None
        :return: An error message if an error occurred.

        for s, b, p in NpoStream.GetMpdStreamFromNpo(None, episodeId, proxy=self.proxy):
            item.complete = True
            stream = part.append_media_stream(s, b)
            for k, v in p.iteritems():
                stream.add_property(k, v)

        """

        if url:
            Logger.info("Determining MPD streams for url: %s", url)
            episode_id = url.split("/")[-1]
        elif episode_id:
            Logger.info("Determining MPD streams for VideoId: %s", episode_id)
        else:
            Logger.error("No url or streamId specified!")
            return None

        token_headers = {"x-requested-with": "XMLHttpRequest"}
        token_headers.update(headers or {})
        data = UriHandler.open("https://www.npostart.nl/api/token", proxy=proxy,
                               additional_headers=token_headers)
        token = JsonHelper(data).get_value("token")

        post_data = {"_token": token}
        data = UriHandler.open("https://www.npostart.nl/player/{0}".format(episode_id),
                               proxy=proxy,
                               additional_headers=headers,
                               data=post_data)
        Logger.trace("Episode Data: %s", data)

        token = JsonHelper(data).get_value("token")
        Logger.debug("Found token %s", token)

        stream_data_url = "https://start-player.npo.nl/video/{0}/streams?" \
                          "profile=dash-widevine" \
                          "&quality=npo" \
                          "&tokenId={1}" \
                          "&streamType=broadcast" \
                          "&mobile=0" \
                          "&isChromecast=0".format(episode_id, token)

        data = UriHandler.open(stream_data_url, proxy=proxy, additional_headers=headers)
        Logger.trace("Stream Data: %s", data)
        stream_data = JsonHelper(data)
        error = stream_data.get_value("html")
        if error:
            error = Regexer.do_regex(r'message">\s*<p>([^<]+)', error)
            if bool(error):
                return error[0]
            return "Unspecified error retrieving streams"

        stream_url = stream_data.get_value("stream", "src")
        if stream_url is None:
            return None

        # Encryption?
        license_url = stream_data.get_value("stream", "keySystemOptions", 0, "options", "licenseUrl")
        if license_url:
            Logger.info("Using encrypted Dash for NPO")
            license_headers = stream_data.get_value("stream", "keySystemOptions", 0, "options", "httpRequestHeaders")
            if license_headers:
                license_headers = '&'.join(["{}={}".format(k, v) for k, v in license_headers.items()])
            license_type = stream_data.get_value("stream", "keySystemOptions", 0, "name")
            license_key = "{0}|{1}|R{{SSM}}|".format(license_url, license_headers or "")
        else:
            Logger.info("Using non-encrypted Dash for NPO")
            license_type = None
            license_key = None

        # Actually set the stream
        stream = part.append_media_stream(stream_url, 0)
        # M3u8.set_input_stream_addon_input(stream, proxy, headers)
        Mpd.set_input_stream_addon_input(stream, proxy, headers,
                                         license_key=license_key,
                                         license_type=license_type,
                                         manifest_update=None if not live else "full")

        return None

    @staticmethod
    def get_streams_from_npo(url, episode_id, proxy=None, headers=None):
        """ Retrieve NPO Player Live streams from a different number of stream urls.

        @param url:               (String) The url to download
        @param episode_id:         (String) The NPO episode ID
        @param headers:           (dict) Possible HTTP Headers
        @param proxy:             (Proxy) The proxy to use for opening

        Can be used like this:

            part = item.create_new_empty_media_part()
            for s, b in NpoStream.get_streams_from_npo(m3u8Url, self.proxy):
                item.complete = True
                # s = self.get_verifiable_video_url(s)
                part.append_media_stream(s, b)

        """

        if url:
            Logger.info("Determining streams for url: %s", url)
            episode_id = url.split("/")[-1]
        elif episode_id:
            Logger.info("Determining streams for VideoId: %s", episode_id)
        else:
            Logger.error("No url or streamId specified!")
            return []

        # we need an hash code
        token_json_data = UriHandler.open("http://ida.omroep.nl/app.php/auth",
                                          no_cache=True, proxy=proxy, additional_headers=headers)
        token_json = JsonHelper(token_json_data)
        token = token_json.get_value("token")

        url = "http://ida.omroep.nl/app.php/%s?adaptive=yes&token=%s" % (episode_id, token)
        stream_data = UriHandler.open(url, proxy=proxy, additional_headers=headers)
        if not stream_data:
            return []

        stream_json = JsonHelper(stream_data, logger=Logger.instance())
        stream_infos = stream_json.get_value("items")[0]
        Logger.trace(stream_infos)
        streams = []
        for stream_info in stream_infos:
            Logger.debug("Found stream info: %s", stream_info)
            if stream_info["format"] == "mp3":
                streams.append((stream_info["url"], 0))
                continue

            elif stream_info["contentType"] == "live":
                Logger.debug("Found live stream")
                url = stream_info["url"]
                url = url.replace("jsonp", "json")
                live_url_data = UriHandler.open(url, proxy=proxy, additional_headers=headers)
                live_url = live_url_data.strip("\"").replace("\\", "")
                Logger.trace(live_url)
                streams += M3u8.get_streams_from_m3u8(live_url, proxy, headers=headers)

            elif stream_info["format"] == "hls":
                m3u8_info_url = stream_info["url"]
                m3u8_info_data = UriHandler.open(m3u8_info_url, proxy=proxy, additional_headers=headers)
                m3u8_info_json = JsonHelper(m3u8_info_data, logger=Logger.instance())
                m3u8_url = m3u8_info_json.get_value("url")
                streams += M3u8.get_streams_from_m3u8(m3u8_url, proxy, headers=headers)

            elif stream_info["format"] == "mp4":
                bitrates = {"hoog": 1000, "normaal": 500}
                url = stream_info["url"]
                if "contentType" in stream_info and stream_info["contentType"] == "url":
                    mp4_url = url
                else:
                    url = url.replace("jsonp", "json")
                    mp4_url_data = UriHandler.open(url, proxy=proxy, additional_headers=headers)
                    mp4_info_json = JsonHelper(mp4_url_data, logger=Logger.instance())
                    mp4_url = mp4_info_json.get_value("url")
                bitrate = bitrates.get(stream_info["label"].lower(), 0)
                if bitrate == 0 and "/ipod/" in mp4_url:
                    bitrate = 200
                elif bitrate == 0 and "/mp4/" in mp4_url:
                    bitrate = 500
                streams.append((mp4_url, bitrate))

        return streams
