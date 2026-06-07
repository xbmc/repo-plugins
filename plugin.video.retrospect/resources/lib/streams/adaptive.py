# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Dict, Optional
from urllib.parse import urlencode, quote

from resources.lib.addonsettings import AddonSettings
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper


class Adaptive(object):

    def __init__(self):
        pass

    @staticmethod
    def get_license_key(key_url, key_type="R", key_headers=None, key_value=None, json_filter=""):
        """ Generates a property license key value

        # A{SSM} -> not implemented
        # R{SSM} -> raw format
        # B{SSM} -> base64 format URL encoded (b{ssmm} will not URL encode)
        # D{SSM} -> decimal format

        The generic format for a LicenseKey is:
        |<url>|<headers>|<key with placeholders>|<optional json filter>

        The Widevine Decryption Key Identifier (KID) can be inserted via the placeholder {KID}

        :param str key_url:                 The URL where the license key can be obtained.
        :param str|None key_type:           The key type (A, R, B or D).
        :param dict[str,str] key_headers:   A dictionary that contains the HTTP headers to pass.
        :param str key_value:               The value that is being passed on as the key value.
        :param str json_filter:             If specified selects that json element to extract the
                                            key response.

        :return: A formatted license string that can be passed to the adaptive input add-on.
        :rtype: str

        """

        header = ""
        if key_headers:
            for k, v in key_headers.items():
                header = "{0}&{1}={2}".format(header, k, HtmlEntityHelper.url_encode(v))

        if key_type in ("A", "R", "B"):
            key_value = "{0}{{SSM}}".format(key_type)
        elif key_type == "D":
            if "D{SSM}" not in key_value:
                raise ValueError("Missing D{SSM} placeholder")
            key_value = HtmlEntityHelper.url_encode(key_value)

        return "{0}|{1}|{2}|{3}".format(key_url, header.strip("&"), key_value, json_filter)

    # noinspection PyUnusedLocal,PyUnresolvedReferences
    @staticmethod
    def set_input_stream_addon_input(strm: "MediaStream",
                                     stream_headers: Optional[Dict[str, str]] = None,
                                     stream_parameters: Optional[Dict[str, str]] = None,
                                     addon: str = "inputstream.adaptive",
                                     manifest_type: Optional[str] = None,

                                     license_key: Optional[str] = None,
                                     license_type: Optional[str] = None,
                                     max_bit_rate: Optional[int] = 0,
                                     persist_storage: bool = False,
                                     service_certificate: Optional[str] = None,

                                     manifest_params: Optional[Dict[str, str]] = None,
                                     manifest_headers: Optional[Dict[str, str]] = None,
                                     manifest_update_params: Optional[str] = None,
                                     manifest_upd_params: Optional[Dict[str, str]] = None) -> "MediaStream":

        """ Updates an existing stream with parameters for the inputstream adaptive add-on.

        :param strm:                    The MediaStream to update
        :param stream_headers:          Possible HTTP Headers for the stream.
        :param stream_parameters:       The stream parameters.
        :param addon:                   Adaptive add-on to use
        :param manifest_type:           Type of manifest (hls/mpd)
        :param license_key:             The value of the license key request
        :param license_type:            The type of license key request used (see below)
        :param max_bit_rate:            The maximum bitrate to use (optional)
        :param persist_storage:         Should we store certificates? And request server certificates?
        :param service_certificate:     Use the specified server certificate
        :param manifest_headers:        The headers to add to the manifest request.
        :param manifest_params:         The parameters to asdd to the manifest request.
        :param manifest_update_params:  How should the manifest be updated ("full"). Deprecated in v21
        :param manifest_upd_params:     The request parameters for the manifest update requests.

        Can be used like this:

            stream = item.add_stream(stream_url, 0)
            M3u8.set_input_stream_addon_input(stream, self.headers)
            item.complete = True

        if maxBitRate is not set, the bitrate will be configured via the normal generic Retrospect
        or channel settings.

        https://github.com/xbmc/inputstream.adaptive/wiki/Integration

        """

        if manifest_type is None:
            raise ValueError("No manifest type set")

        strm.Adaptive = True    # NOSONAR

        # See https://forum.kodi.tv/showthread.php?tid=353560
        if AddonSettings.is_min_version(AddonSettings.KodiMatrix):
            strm.add_property("inputstream", addon)
        else:
            strm.add_property("inputstreamaddon", addon)

        # See https://github.com/peak3d/inputstream.adaptive/blob/master/inputstream.adaptive/addon.xml.in
        strm.add_property("inputstream.adaptive.manifest_type", manifest_type)

        if license_key:
            strm.add_property("inputstream.adaptive.license_key", license_key)
        if license_type:
            strm.add_property("inputstream.adaptive.license_type", license_type)

        if max_bit_rate:
            strm.add_property("inputstream.adaptive.max_bandwidth", str(max_bit_rate * 1000))
        if persist_storage:
            strm.add_property("inputstream.adaptive.license_flags", "persistent_storage")
        if service_certificate is not None:
            strm.add_property("inputstream.adaptive.server_certificate", service_certificate)

        # Stream stuff
        if stream_headers:
            # On Kodi v19 or below: Specifies the HTTP headers to be used to download manifests
            # and streams (audio/video/subtitles).
            #
            # On Kodi v20: Specifies the HTTP headers to be used to download manifests
            # and streams (audio/video/subtitles).
            # NOTE: Use this property to set headers to the manifests is a deprecated behaviour,
            # use inputstream.adaptive.manifest_headers instead.
            #
            # From Kodi v21 or above:
            # Specifies the HTTP headers to be used to download streams (audio/video/subtitles) only.
            params = urlencode(stream_headers, quote_via=quote)
            strm.add_property("inputstream.adaptive.stream_headers", params)

        if stream_parameters and AddonSettings.is_min_version(AddonSettings.KodiNexus):
            params = urlencode(stream_parameters, quote_via=quote)
            strm.add_property("inputstream.adaptive.stream_params", params)

        # Manifest stuff
        if AddonSettings.is_min_version(AddonSettings.KodiNexus):
            if manifest_params:
                params = urlencode(manifest_params, quote_via=quote)
                strm.add_property("inputstream.adaptive.manifest_params", params)

            if manifest_headers:
                params = urlencode(manifest_headers, quote_via=quote)
                strm.add_property("inputstream.adaptive.manifest_headers", params)
            elif stream_headers:
                params = urlencode(stream_headers, quote_via=quote)
                strm.add_property("inputstream.adaptive.manifest_headers", params)

        if manifest_update_params and not AddonSettings.is_min_version(AddonSettings.KodiOmega):
            # WARNING: PROPERTY DEPRECATED ON Kodi v21 AND REMOVED ON Kodi v22, please use manifest_upd_params instead.
            strm.add_property("inputstream.adaptive.manifest_update_parameter", manifest_update_params)

        if manifest_upd_params and AddonSettings.is_min_version(AddonSettings.KodiOmega):
            params = urlencode(manifest_upd_params, quote_via=quote)
            strm.add_property("inputstream.adaptive.manifest_upd_params", params)

        return strm

    @staticmethod
    def set_max_bitrate(stream, max_bit_rate):
        """ Sets the maximum bitrate for a stream.

        :param MediaStream stream:  The stream to limit.
        :param int max_bit_rate:    The maximum bitrate

        """

        if not stream.Adaptive or max_bit_rate == 0:
            return

        # Previously defined when creating the stream => We don't override that
        if "inputstream.adaptive.max_bandwidth" in stream.Properties:
            return

        stream.add_property("inputstream.adaptive.max_bandwidth", str(max_bit_rate * 1000))
        return
