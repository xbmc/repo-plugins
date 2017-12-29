import json
import xml.etree.ElementTree as ET
from kodihelper import KodiHelper

helper = KodiHelper()


class Widevine(object):
    license_url = helper.c.config['settings']['drmProxy']

    def get_kid(self, mpd_url):
        """Parse the KID from the MPD manifest."""
        mpd_data = helper.c.make_request(mpd_url, 'get')
        mpd_root = ET.fromstring(mpd_data)

        for i in mpd_root.iter('{urn:mpeg:dash:schema:mpd:2011}ContentProtection'):
            if '{urn:mpeg:cenc:2013}default_KID' in i.attrib:
                return i.attrib['{urn:mpeg:cenc:2013}default_KID']

    def get_license(self, mpd_url, wv_challenge, token):
        """Acquire the Widevine license from the license server and return it."""
        post_data = {
            'drm_info': [x for x in bytearray(wv_challenge)],  # convert challenge to a list of bytes
            'kid': self.get_kid(mpd_url),
            'token': token
        }

        wv_license = helper.c.make_request(self.license_url, 'post', payload=json.dumps(post_data))
        return wv_license
