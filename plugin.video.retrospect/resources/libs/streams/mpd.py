# ===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
# ===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
# ===============================================================================

from streams.adaptive import Adaptive


class Mpd(object):
    def __init__(self):
        pass

    @staticmethod
    def set_input_stream_addon_input(strm, proxy=None, headers=None,
                                     license_key=None, license_type="com.widevine.alpha",
                                     max_bit_rate=None,
                                     persist_storage=False,
                                     service_certificate=None,
                                     manifest_update=None):
        """ Parsers standard M3U8 lists and returns a list of tuples with streams and bitrates that
        can be used by other methods.

        :param strm:                    (MediaStream) the MediaStream to update
        :param proxy:                   (Proxy) The proxy to use for opening
        :param dict headers:            Possible HTTP Headers
        :param str license_key:         The value of the license key request
        :param str license_type:        The type of license key request used (see below)
        :param int max_bit_rate:        The maximum bitrate to use (optional)
        :param bool persist_storage:    Should we store certificates? And request server certificates?
        :param str service_certificate: Use the specified server certificate

        Can be used like this:

            part = item.create_new_empty_media_part()
            stream = part.append_media_stream(m3u8url, 0)
            M3u8.set_input_stream_addon_input(stream, self.proxy, self.headers)
            item.complete = True

        if maxBitRate is not set, the bitrate will be configured via the normal generic Retrospect
        or channel settings.

        """

        return Adaptive.set_input_stream_addon_input(strm, proxy, headers,
                                                     manifest_type="mpd",
                                                     license_key=license_key,
                                                     license_type=license_type,
                                                     max_bit_rate=max_bit_rate,
                                                     persist_storage=persist_storage,
                                                     service_certificate=service_certificate,
                                                     manifest_update=manifest_update)

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
        :param str key_value:               The value that is beging passed on as the key value.
        :param str json_filter:             If specified selects that json element to extract the
                                            key response.

        :return: A formated license string that can be passed to the adaptive input add-on.
        :rtype: str

        """

        return Adaptive.get_license_key(key_url,
                                        key_type=key_type,
                                        key_headers=key_headers,
                                        key_value=key_value,
                                        json_filter=json_filter)
