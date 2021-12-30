from resources.lib.globals import *
import inputstreamhelper


class Stream:
    drm_asset_id = ''
    drm_token = ''
    drm_type = ''
    lic_url = 'https://widevine.license.istreamplanet.com/widevine/api/license/263b65d9-0c1f-4246-9b3f-0b500ed8c794'
    manifest_url = ''
    media_token = ''
    pid = ''
    requestor_id = 'nbcsports'
    resource_id = ''
    token_headers = {
        "Accept": "*/*",
        "Accept-Language": "en;q=1",
        "Content-Type": "application/json",
        "User-Agent": "okhttp/3.12.12"
    }
    token_url = 'https://tokens.playmakerservices.com'

    def __init__(self, stream_vars):
        self.drm_asset_id = stream_vars['drm_asset_id']
        self.drm_type = stream_vars['drm_type']
        self.manifest_url = stream_vars['manifest_url']
        self.pid = stream_vars['pid']
        self.resource_id = stream_vars['resource_id']
        self.media_token = stream_vars['media_token']

    def get_tokenized_url(self):
        payload = {
            "application": "NBCSports",
            "authInfo": {
                "authenticationType": "adobe-pass",
                "requestorId": self.requestor_id,
                "resourceId": base64.b64encode(codecs.encode(self.resource_id)).decode("ascii"),
                "token": self.media_token
            },
            "cdns": [
                {
                    "name": "akamai",
                    "url": self.manifest_url
                }
            ],
            "pid": self.pid,
            "platform": "android"
        }

        xbmc.log(str(payload))
        r = requests.post(self.token_url, headers=self.token_headers, cookies=load_cookies(), json=payload, verify=VERIFY)
        save_cookies(r.cookies)
        xbmc.log(r.text)

        self.manifest_url = r.json()['akamai'][0]['tokenizedUrl']

    def get_drm_token(self):
        payload = {
            "application": "NBCSports",
            "pid": self.pid,
            "platform": "android",
            "authInfo": {
                "authenticationType": "adobe-pass",
                "requestorId": self.requestor_id,
                "resourceId": base64.b64encode(codecs.encode(self.resource_id)).decode("ascii"),
                "token": self.media_token
            },
            "drmInfo":
                {
                    "assetId": self.drm_asset_id,
                    "deviceId": "android_c577f1f28b8d181d"
                }
        }

        r = requests.post(self.token_url, headers=self.token_headers, cookies=load_cookies(), json=payload, verify=VERIFY)
        save_cookies(r.cookies)
        xbmc.log(r.text)

        return r.json()['drmToken']

    def create_listitem(self):
        self.get_tokenized_url()

        is_helper = inputstreamhelper.Helper('hls', drm='widevine')
        listitem = xbmcgui.ListItem(path=('%s|User-Agent=%s') % (self.manifest_url, UA_NBCSN))
        if is_helper.check_inputstream():
            if KODI_VERSION >= 19:
                listitem.setProperty('inputstream', 'inputstream.adaptive')
            else:
                listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')

            if self.drm_type == 'widevine':
                lic_headers = 'User-Agent=Dalvik%2F2.1.0+(Linux%3B+U%3B+Android+6.0.1%3B+Hub+Build%2FMHC19J)'
                lic_headers += '&Content-Type=application/octet-stream'
                lic_headers += '&X-ISP-TOKEN=%s' % urllib.quote(self.get_drm_token())
                license_key = '%s|%s|R{SSM}|' % (self.lic_url, lic_headers)
                listitem.setProperty('inputstream.adaptive.license_key', license_key)
                listitem.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')

            listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
            listitem.setProperty('inputstream.adaptive.stream_headers', 'User-Agent=%s' % UA_NBCSN)
        else:
            listitem.setMimeType("application/x-mpegURL")

        return listitem
