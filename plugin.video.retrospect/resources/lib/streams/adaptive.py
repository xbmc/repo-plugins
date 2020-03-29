# SPDX-License-Identifier: CC-BY-NC-SA-4.0

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

    # noinspection PyUnusedLocal
    @staticmethod
    def set_input_stream_addon_input(strm, proxy=None, headers=None, addon="inputstream.adaptive",
                                     manifest_type=None,
                                     license_key=None,
                                     license_type=None,
                                     max_bit_rate=None,
                                     persist_storage=False,
                                     service_certificate=None,
                                     manifest_update=None):
        """ Parsers standard M3U8 lists and returns a list of tuples with streams and bitrates that
        can be used by other methods.

        :param strm:                    (MediaStream) the MediaStream to update
        :param proxy:                   (Proxy) The proxy to use for opening
        :param dict headers:            Possible HTTP Headers
        :param str addon:               Adaptive add-on to use
        :param str manifest_type:       Type of manifest (hls/mpd)
        :param str license_key:         The value of the license key request
        :param str license_type:        The type of license key request used (see below)
        :param int max_bit_rate:        The maximum bitrate to use (optional)
        :param bool persist_storage:    Should we store certificates? And request server certificates?
        :param str service_certificate: Use the specified server certificate
        :param str manifest_update:     How should the manifest be updated

        Can be used like this:

            part = item.create_new_empty_media_part()
            stream = part.append_media_stream(stream_url, 0)
            M3u8.set_input_stream_addon_input(stream, self.proxy, self.headers)
            item.complete = True

        if maxBitRate is not set, the bitrate will be configured via the normal generic Retrospect
        or channel settings.

        """

        if manifest_type is None:
            raise ValueError("No manifest type set")

        strm.Adaptive = True    # NOSONAR

        # See https://github.com/peak3d/inputstream.adaptive/blob/master/inputstream.adaptive/addon.xml.in
        strm.add_property("inputstreamaddon", addon)
        strm.add_property("inputstream.adaptive.manifest_type", manifest_type)
        if license_key:
            strm.add_property("inputstream.adaptive.license_key", license_key)
        if license_type:
            strm.add_property("inputstream.adaptive.license_type", license_type)
        if max_bit_rate:
            strm.add_property("inputstream.adaptive.max_bandwidth", max_bit_rate * 1000)
        if persist_storage:
            strm.add_property("inputstream.adaptive.license_flags", "persistent_storage")
        if service_certificate is not None:
            strm.add_property("inputstream.adaptive.server_certificate", service_certificate)
        if manifest_update:
            strm.add_property("inputstream.adaptive.manifest_update_parameter", manifest_update)

        if headers:
            header = ""
            for k, v in headers.items():
                header = "{0}&{1}={2}".format(header, k, HtmlEntityHelper.url_encode(v))
            strm.add_property("inputstream.adaptive.stream_headers", header.strip("&"))

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
