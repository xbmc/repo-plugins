import requests
import uuid
import os, sys
from xbmcplugin import SORT_METHOD_LABEL_IGNORE_THE
from resources.lib.helpers.dynamic_headers import *
from resources.lib.helpers.helpermethods import *
from resources.lib.statics.static import *
from resources.lib.helpers import helperclasses

if sys.version_info[0] == 3:
    from urllib.parse import quote_plus, unquote_plus
else:
    from urllib import quote_plus, unquote_plus
    from builtins import xrange as range

class Tokens:
    def __init__(self, testing, kodiwrapper):
        self.testing = not testing
        self.kodi_wrapper = kodiwrapper
        self.get_l_string = kodiwrapper.get_localized_string
        self.session = requests.Session()

    def _prepare_request(self):
        r = self.make_request("POST",
                              "https://api.yeloplay.be/api/v1/oauth/prepare",
                              json_header, None, json_prepare_message, False, None, self.testing)

        j = r.json()["OAuthPrepareParams"]

        self.save_json_to_file("OAuthPrepareParams.json", {
            "authorizeUrl": j["authorizeUrl"],
            "clientId": j["clientId"],
            "nonce": j["nonce"],
            "redirectUri": j["redirectUri"],
        })

    def _authorize(self):
        OAuthPrepareParams = self.fetch_OAuthPrepareParams()

        authorize_Url = OAuthPrepareParams["authorizeUrl"]
        client_Id = OAuthPrepareParams["clientId"]
        nonce = OAuthPrepareParams["nonce"]
        state = self.create_State(20)
        redirect_Uri = quote_plus(OAuthPrepareParams["redirectUri"])

        r = self.make_request("GET", "{}?client_id={}&state={}&nonce={}&redirect_uri={}"
                              .format(authorize_Url, client_Id, nonce, state, redirect_Uri)
                              + "&response_type=code&prompt=login", default_headers, None, None, False, None,
                              self.testing)

        return r.headers["Location"]

    def _register_device(self):
        r = self.make_request("POST", "https://api.yeloplay.be/api/v1/device/register", json_header, None,
                              json_request_device, False, None, self.testing)
        j = r.json()

        if j["deviceRegistration"]["resultCode"] == "CREATED":
            self.save_json_to_file("IdTokens.json", {
                'deviceId': j["deviceRegistration"]["id"],
                'webId': j["deviceRegistration"]["deviceProperties"]["dict"][8]["value"]
            })

    def make_request(self, method, url, headers=None, data=None, json=None, allow_redirects=False, cookies=None,
                     verify=True):
        if method.upper() == "POST":
            r = self.session.post(url=url,
                                  data=data,
                                  headers=headers,
                                  json=json,
                                  allow_redirects=allow_redirects,
                                  cookies=cookies,
                                  verify=verify)
        elif method.upper() == "GET":
            r = self.session.get(url=url,
                                 data=data,
                                 headers=headers,
                                 json=json,
                                 allow_redirects=allow_redirects,
                                 cookies=cookies,
                                 verify=verify)
        else:
            r = None

        return r

    def login(self):
        self._prepare_request()
        self._register_device()
        self._authorize()

        self._login_do()

        callback_url = self._authorize()

        if self._callback(callback_url):
            self._verify_token()
            self._request_OAuthTokens()
            self._request_entitlement_and_postal()

            return True
        else:
            self.kodi_wrapper.dialog_ok(self.get_l_string(32006),
                                        self.get_l_string(32007))
            return False

    def _login_do(self):
        creds = helperclasses.Credentials(self.kodi_wrapper)
        if not creds.are_filled_in():
            self.kodi_wrapper.dialog_ok(self.get_l_string(32014),
                                        self.get_l_string(32015))
            self.kodi_wrapper.open_settings()
            creds.reload()

        self.make_request("POST", "https://login.prd.telenet.be/openid/login.do",
                          form_headers, create_login_payload(creds.username, creds.password),
                          None, False, None, self.testing)

    def _callback(self, url):
        callbackKey = regex(r"(?<=code=)\w{0,32}", url)

        if not callbackKey:
            return False

        self.save_json_to_file("callbackKey.json", {"callbackKey": callbackKey})

        self.make_request("GET", url, default_headers, None, None, False, None, self.testing)

        return True

    def _verify_token(self):
        Ids = self.fetch_Ids()
        callbackKey = self.fetch_CallbackKey()
        self.make_request("POST", "https://api.yeloplay.be/api/v1/device/verify",
                          verify_header(Ids["deviceId"], callbackKey), None,
                          json_verify_header(Ids["deviceId"], Ids["webId"]),
                          False, None, self.testing)

    def open_json_from_file(self, file_name):
        path = self.kodi_wrapper.get_addon_data_path()

        if not os.path.exists(path):
            os.mkdir(path, 0o775)

        os.chdir(path)

        for i in range(0, 2):
            try:
                with open(file_name, 'r') as file:
                    return json.load(file)
            except IOError:
                """ Did we login? """
                self.login()

    def save_json_to_file(self, file_name, data):
        path = self.kodi_wrapper.get_addon_data_path()

        if not os.path.exists(path):
            os.mkdir(path, 0o775)

        os.chdir(path)

        with open(file_name, 'w') as file:
            json.dump(data, file)

    def fetch_OAuthTokens(self):
        OAuthTokens = self.open_json_from_file("OAuthTokens.json")

        if OAuthTokens:
            return OAuthTokens

    def fetch_Ids(self):
        IdTokens = self.open_json_from_file("IdTokens.json")

        if IdTokens:
            return IdTokens

    def fetch_OAuthPrepareParams(self):
        OAuthPrepareParams = self.open_json_from_file("OAuthPrepareParams.json")

        if OAuthPrepareParams:
            return OAuthPrepareParams

    def fetch_CallbackKey(self):
        CallbackKey = self.open_json_from_file("callbackKey.json")

        if CallbackKey:
            return CallbackKey["callbackKey"]

    def fetch_Entitlement(self):
        Entitlement = self.open_json_from_file("entitlement.json")

        if Entitlement:
            return Entitlement["entitlementId"]

    def fetch_Postal(self):
        PostalCode = self.open_json_from_file("postal_code.json")

        if PostalCode:
            return PostalCode["postal_code"]

    def fetch_channel_list(self):
        postal = helperclasses.PostalCode(self.kodi_wrapper)

        # if postal is not filled in, in settings try to retrieve it from customerFeatures
        if not postal.are_filled_in():
            postal.postal_code = self.fetch_Postal()


            # if that does not seem to work..
            if postal.postal_code is None:
                self.kodi_wrapper.dialog_ok(self.get_l_string(32008),
                                            self.get_l_string(32009))
                self.kodi_wrapper.open_settings()
                postal.reload()

        r = self.make_request("GET", "https://api.yeloplay.be/api/v1/epg/channel/list?platform=Web"
                                     "&postalCode={}&postalCode={}".format(postal.postal_code, postal.postal_code),
                              default_headers,
                              None, None, False, None, self.testing)
        return r.json()["serviceCatalog"]["tvChannels"]

    def _request_OAuthTokens(self):
        Ids = self.fetch_Ids()
        OAuthPrepareParams = self.fetch_OAuthPrepareParams()
        callbackKey = self.fetch_CallbackKey()

        r = self.make_request("POST", "https://api.yeloplay.be/api/v1/oauth/token",
                              token_header(Ids["deviceId"], callbackKey), False,
                              json__token_header(callbackKey,
                                                 unquote_plus(OAuthPrepareParams["redirectUri"])),
                              False, None, self.testing)

        j = r.json()["OAuthTokens"]

        if j["status"] == "SUCCESS":
            self.save_json_to_file("OAuthTokens.json", j)

    def create_State(self, size):
        return str(uuid.uuid4()).replace("-", "")[0:size]

    def fetch_customer_id(self):
        Entitlement = self.open_json_from_file("entitlement.json")

        if Entitlement:
            return Entitlement["customer_id"]

    def _request_entitlement_and_postal(self):
        accessToken = self.fetch_OAuthTokens()["accessToken"]
        deviceId = self.fetch_Ids()["deviceId"]

        r = self.make_request("GET", "https://api.yeloplay.be/api/v1/session/lookup?include=customerFeatures",
                              authorization_header_json(deviceId, accessToken),
                              None, None, False, None, self.testing)
        j = r.json()

        entitlements = [int(item["id"]) for item in j["linked"]["customerFeatures"]["entitlements"]]
        customer_Id = j["loginSession"]["user"]["links"]["customerFeatures"]
        postal_code = j["linked"]["customerFeatures"]["idtvLines"][0]["region"]

        self.save_json_to_file("entitlement.json", {"entitlementId": entitlements,
                                                    "customer_id": customer_Id})
        self.save_json_to_file("postal_code.json", {"postal_code": postal_code})

class YeloPlay(Tokens):
    def __init__(self, kodiwrapper, streaming_protocol, testing=False):
        Tokens.__init__(self, testing, kodiwrapper)
        self.streaming_protocol = streaming_protocol

    def display_main_menu(self, is_folder=True):
        listing = []
        item = {
            "name": "Livestreams",
            "thumb": r"http://pluspng.com/img-png/search-button-png-button-buttons-"
                     r"multimedia-play-square-web-icon-512.png"
        }

        list_item = self.kodi_wrapper.create_list_item(item["name"], item["thumb"], None, "false")
        url = self.kodi_wrapper.construct_url("{0}?action=listing&category={1}", item["name"].lower())
        listing.append((url, list_item, is_folder))

        self.kodi_wrapper.add_dir_item(listing)
        self.kodi_wrapper.sort_method(SORT_METHOD_LABEL_IGNORE_THE)
        self.kodi_wrapper.end_directory()

    def list_channels(self, tv_channels, is_folder=False):
        listing = []
        entitlementId = self.fetch_Entitlement()

        for i in range(len(tv_channels)):
            if (
                    not bool(tv_channels[i]["channelProperties"]["radio"])
                    and bool(tv_channels[i]["channelProperties"]["live"])
                    and any(tv_channels[i]["channelPolicies"]["linearEndpoints"])
                    and any(x in entitlementId for x in tv_channels[i]["channelAvailability"]["oasisId"])
            ):
                list_item = self.kodi_wrapper.create_list_item(tv_channels[i]["channelIdentification"]["name"],
                                                               tv_channels[i]["channelProperties"]["squareLogo"],
                                                               tv_channels[i]["channelProperties"]["liveThumbnailURL"],
                                                               "true")

                url = self.kodi_wrapper.construct_url("{0}?action=play&livestream={1}",
                                                      tv_channels[i]["channelIdentification"]["stbUniqueName"])

                listing.append((url, list_item, is_folder))

        self.kodi_wrapper.add_dir_item(listing)
        self.kodi_wrapper.sort_method(SORT_METHOD_LABEL_IGNORE_THE)
        self.kodi_wrapper.end_directory()

    def play_live_stream(self, stream_url):
        bit_rate = helperclasses.BitRate(self.kodi_wrapper)
        deviceId = self.fetch_Ids()["deviceId"]
        customerId = self.fetch_customer_id()

        self.kodi_wrapper.play_live_stream(deviceId, customerId, stream_url, bit_rate.bitrate)

    def select_manifest_url(self, channel):
        for i in range(0, 2):
            try:
                accessToken = self.fetch_OAuthTokens()["accessToken"]
                deviceId = self.fetch_Ids()["deviceId"]

                r = self.make_request("POST", "https://api.yeloplay.be/api/v1/stream/start",
                                      authorization_header_json(deviceId, accessToken), None,
                                      json_request_header(deviceId, channel, self.streaming_protocol),
                                      False, None, self.testing)

                j = r.json()

                if not j.get("errors"):
                    return j["stream"]["streamDescriptor"]["manifest"]
                else:
                    if j["errors"][0]["code"] == "EPG_RESTRICTED_EUROPE":
                        self.kodi_wrapper.dialog_ok(self.get_l_string(32011),
                                                    self.get_l_string(32012))
                    elif j["errors"][0]["code"] == "EPG_RESTRICTED_NOWHERE":
                        self.kodi_wrapper.dialog_ok(self.get_l_string(32011),
                                                    self.get_l_string(32013))
                    return False
            except ValueError:
                """ Session might be expired """
                self.login()
