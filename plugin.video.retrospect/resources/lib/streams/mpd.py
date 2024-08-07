# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Optional, Dict

from resources.lib.streams.adaptive import Adaptive
from resources.lib.mediaitem import MediaStream


class Mpd(object):
    def __init__(self):
        pass

    # def set_input_stream_addon_input(strm, headers=None,
    #                                  license_key=None, license_type="com.widevine.alpha",
    #                                  max_bit_rate=None,
    #                                  persist_storage=False,
    #                                  service_certificate=None,
    #                                  manifest_update=None):

    @staticmethod
    def set_input_stream_addon_input(strm: MediaStream,
                                     stream_headers: Optional[Dict[str, str]] = None,
                                     stream_parameters: Optional[Dict[str, str]] = None,

                                     license_key: Optional[str] = None,
                                     license_type: Optional[str] = "com.widevine.alpha",
                                     max_bit_rate: Optional[int] = 0,
                                     persist_storage: bool = False,
                                     service_certificate: Optional[str] = None,

                                     manifest_params: Optional[Dict[str, str]] = None,
                                     manifest_headers: Optional[Dict[str, str]] = None,
                                     manifest_update_params: Optional[str] = None,
                                     manifest_upd_params: Optional[Dict[str, str]] = None) -> MediaStream:

        """ Updates an existing stream with parameters for the inputstream adaptive add-on.

        :param strm:                    The MediaStream to update
        :param stream_headers:          Possible HTTP Headers for the stream.
        :param stream_parameters:       The stream parameters.
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
            Mpd.set_input_stream_addon_input(stream, self.headers)
            item.complete = True

        if maxBitRate is not set, the bitrate will be configured via the normal generic Retrospect
        or channel settings.

        https://github.com/xbmc/inputstream.adaptive/wiki/Integration

        """

        if license_key is not None:
            # Local import to make sure the overhead is low
            import inputstreamhelper
            from resources.lib.logger import Logger

            is_helper = inputstreamhelper.Helper("mpd", drm=license_type)
            if is_helper.check_inputstream():
                Logger.info("Widevine library was already installed or installed successfully.")
            else:
                Logger.error("Widevine was not installed or failed to install.")

        return Adaptive.set_input_stream_addon_input(strm,
                                                     stream_headers=stream_headers,
                                                     stream_parameters=stream_parameters,
                                                     manifest_type="mpd",
                                                     license_key=license_key,
                                                     license_type=license_type,
                                                     max_bit_rate=max_bit_rate,
                                                     persist_storage=persist_storage,
                                                     service_certificate=service_certificate,
                                                     manifest_params=manifest_params,
                                                     manifest_headers=manifest_headers,
                                                     manifest_update_params=manifest_update_params,
                                                     manifest_upd_params=manifest_upd_params)

    @staticmethod
    def get_license_key(key_url, key_type="R", key_headers=None, key_value=None, json_filter=""):
        """ Generates a propery license key value

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

        return Adaptive.get_license_key(key_url,
                                        key_type=key_type,
                                        key_headers=key_headers,
                                        key_value=key_value,
                                        json_filter=json_filter)
