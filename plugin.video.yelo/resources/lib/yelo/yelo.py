import requests
import uuid
from datetime import datetime
import os, sys
from xbmcplugin import SORT_METHOD_LABEL_IGNORE_THE
from resources.lib.helpers.dynamic_headers import *
from resources.lib.helpers.helpermethods import *
from resources.lib.statics.static import *
from resources.lib.helpers import helperclasses

# region Python_check

if sys.version_info[0] == 3:
    from urllib.parse import quote_plus, unquote_plus
else:
    from urllib import quote_plus, unquote_plus
    from builtins import xrange as range

# endregion

FILE_NAME = "data.json"

session = requests.Session()


class Errors():
    def __init__(self, testing, kodiwrapper):
        self.testing = not testing
        self.kodi_wrapper = kodiwrapper

    def get_error_message(self, id):
        r = make_request(session, "GET", "https://api.yeloplay.be/api/v1/masterdata?"
                                         "platform=Web&fields=errors",
                         default_headers, None, None, False, None, self.testing)

        errors = r.json()["masterData"]["errors"]

        res = next((error for error in errors if error["id"] == id), "")

        if res:
            return res["title"]["locales"]["en"], res["subtitle"]["locales"]["en"]


class Prepare:
    def __init__(self, testing, kodiwrapper):
        self.testing = not testing
        self.kodi_wrapper = kodiwrapper
        self.get_l_string = kodiwrapper.get_localized_string

    def _prepare_request(self):
        r = make_request(session, "POST",
                         "https://api.yeloplay.be/api/v1/oauth/prepare",
                         json_header, None, json_prepare_message, False, None, self.testing)

        j = r.json()["OAuthPrepareParams"]

        self.append_json_to_file(FILE_NAME,
                                 {"OAuthPrepareParams": {
                                     'authorizeUrl': j["authorizeUrl"],
                                     'clientId': j["clientId"],
                                     'nonce': j["nonce"],
                                     'redirectUri': j["redirectUri"]
                                 }})

    def _authorize(self):
        OAuthPrepareParams = self.fetch_from_data("OAuthPrepareParams")

        authorize_Url = OAuthPrepareParams["authorizeUrl"]
        client_Id = OAuthPrepareParams["clientId"]
        nonce = OAuthPrepareParams["nonce"]
        state = self.create_State(20)
        redirect_Uri = quote_plus(OAuthPrepareParams["redirectUri"])

        r = make_request(session, "GET", "{}?client_id={}&state={}&nonce={}&redirect_uri={}"
                         .format(authorize_Url, client_Id, nonce, state, redirect_Uri)
                         + "&response_type=code&prompt=login", default_headers, None, None, False, None,
                         self.testing)

        return r.headers["Location"]

    def _register_device(self):
        r = make_request(session, "POST", "https://api.yeloplay.be/api/v1/device/register", json_header, None,
                         json_request_device, False, None, self.testing)
        j = r.json()

        if j["deviceRegistration"]["resultCode"] == "CREATED":
            self.append_json_to_file(FILE_NAME,
                                     {"IdTokens": {
                                         'deviceId': j["deviceRegistration"]["id"],
                                         'webId': j["deviceRegistration"]["deviceProperties"]["dict"][8]["value"]
                                     }})

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

        make_request(session, "POST", "https://login.prd.telenet.be/openid/login.do",
                     form_headers, create_login_payload(creds.username, creds.password),
                     None, False, None, self.testing)

    def _callback(self, url):
        callbackKey = regex(r"(?<=code=)\w{0,32}", url)

        if not callbackKey:
            return False

        self.append_json_to_file(FILE_NAME, {"callbackKey": {"callbackKey": callbackKey}})

        make_request(session, "GET", url, default_headers, None, None, False, None, self.testing)

        return True

    def _verify_token(self):
        Ids = self.fetch_from_data("IdTokens")
        callbackKey = self.fetch_from_data("callbackKey")["callbackKey"]
        make_request(session, "POST", "https://api.yeloplay.be/api/v1/device/verify",
                     verify_device_header(Ids["deviceId"], callbackKey), None,
                     json_verify_data(Ids["deviceId"], Ids["webId"]),
                     False, None, self.testing)

    def append_json_to_file(self, file_name, json_data):
        path = self.kodi_wrapper.get_addon_data_path()

        if not os.path.exists(path):
            os.mkdir(path, 0o775)

        os.chdir(path)

        data = {}
        if os.path.isfile(file_name):
            with open(file_name, "r") as jsonFile:
                data = json.load(jsonFile)

        data.update(json_data)

        with open(file_name, "w") as jsonFile:
            json.dump(data, jsonFile)

    def fetch_from_data(self, key):
        with open(FILE_NAME, "r") as jsonFile:
            data = json.load(jsonFile)

        return data[key]

    def fetch_channel_list(self):
        postal = helperclasses.PostalCode(self.kodi_wrapper)

        # if postal is not filled in, in settings try to retrieve it from customerFeatures
        if not postal.are_filled_in():
            postal.postal_code = self.fetch_from_data("postal")["postal_code"]

            # if that does not seem to work..
            if postal.postal_code is None:
                self.kodi_wrapper.dialog_ok(self.get_l_string(32008),
                                            self.get_l_string(32009))
                self.kodi_wrapper.open_settings()
                postal.reload()

        r = make_request(session, "GET", "https://api.yeloplay.be/api/v1/epg/channel/list?platform=Web"
                                         "&postalCode={}&postalCode={}".format(postal.postal_code, postal.postal_code),
                         default_headers,
                         None, None, False, None, self.testing)
        return r.json()["serviceCatalog"]["tvChannels"]

    def _request_OAuthTokens(self):
        Ids = self.fetch_from_data("IdTokens")
        OAuthPrepareParams = self.fetch_from_data("OAuthPrepareParams")
        callbackKey = self.fetch_from_data("callbackKey")["callbackKey"]

        r = make_request(session, "POST", "https://api.yeloplay.be/api/v1/oauth/token",
                         token_header(Ids["deviceId"], callbackKey), False,
                         json_oauth_token_data(callbackKey,
                                               unquote_plus(OAuthPrepareParams["redirectUri"])),
                         False, None, self.testing)

        j = r.json()["OAuthTokens"]

        if j["status"] == "SUCCESS":
            self.append_json_to_file(FILE_NAME, {"OAuthTokens": j})

    def create_State(self, size):
        return str(uuid.uuid4()).replace("-", "")[0:size]

    def _request_entitlement_and_postal(self):
        accessToken = self.fetch_from_data("OAuthTokens")["accessToken"]
        deviceId = self.fetch_from_data("IdTokens")["deviceId"]

        r = make_request(session, "GET", "https://api.yeloplay.be/api/v1/session/lookup?include=customerFeatures",
                         authorization_header(deviceId, accessToken),
                         None, None, False, None, self.testing)
        j = r.json()

        entitlements = [int(item["id"]) for item in j["linked"]["customerFeatures"]["entitlements"]]
        customer_Id = j["loginSession"]["user"]["links"]["customerFeatures"]
        postal_code = j["linked"]["customerFeatures"]["idtvLines"][0]["region"]

        self.append_json_to_file(FILE_NAME, {"entitlement": {"entitlementId": entitlements,
                                                             "customer_id": customer_Id}})
        self.append_json_to_file(FILE_NAME, {"postal": {"postal_code": postal_code}})


class YeloPlay(Prepare, Errors):
    def __init__(self, kodiwrapper, streaming_protocol, testing=False):
        Prepare.__init__(self, testing, kodiwrapper)
        Errors.__init__(self, testing, kodiwrapper)

        self.streaming_protocol = streaming_protocol
        self.addon_url = kodiwrapper.get_addon_url()

    def display_main_menu(self, is_folder=True):
        listing = []
        item = {
            "name": "Livestreams",
            "thumb": "DefaultAddonPVRClient.png"
        }

        list_item = self.kodi_wrapper.create_list_item(item["name"], item["thumb"], None, None, "false")

        url = self.kodi_wrapper.url_for("list_channels", category=item["name"].lower())
        listing.append((url, list_item, is_folder))

        self.kodi_wrapper.add_dir_items(listing)
        self.kodi_wrapper.sort_method(SORT_METHOD_LABEL_IGNORE_THE)
        self.kodi_wrapper.end_directory()

    def _request_broadcast_info(self, channelId, datetime):
        r = make_request(session, "GET", "https://pubba.yelo.prd.telenet-ops.be/v1/"
                                         "events/schedule-time/outformat/json/lng/nl/start/"
                                         "{}/range/{}/channel/{}/".
                         format(datetime, 2, channelId),
                         default_headers, None, None, False, None, self.testing)

        schedules = r.json()["schedule"]

        return [
            {"title": broadcast_elem["title"],
             "start": broadcast_elem["starttime"],
             "end": broadcast_elem["endtime"],
             "poster": broadcast_elem["poster"]
            }
            for schedule_elem in schedules for broadcast_elem in schedule_elem["broadcast"]]

    def _timestamp_to_time(self, timestamp):
        return datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")

    def _get_broadcast_now(self, channelId):
        today = datetime.today().strftime("%Y%m%d%H")
        return self._request_broadcast_info(channelId, today)

    def _extract_schedule(self, schedule):
        timestamp = get_timestamp()

        now = next((item for item in schedule if int(item["start"])
                    <= timestamp <= int(item["end"])), "")

        prev = next((item for item in schedule if int(item["end"]) == now.get("start")), "")

        nxt = next((item for item in schedule if int(item["start"]) == now.get("end")), "")

        if now:
            now["start"] = self._timestamp_to_time(now.get("start"))
            now["end"] = self._timestamp_to_time(now.get("end"))
        if prev:
            prev["start"] = self._timestamp_to_time(prev.get("start"))
            prev["end"] = self._timestamp_to_time(prev.get("end"))
        if nxt:
            nxt["start"] = self._timestamp_to_time(nxt.get("start"))
            nxt["end"] = self._timestamp_to_time(nxt.get("end"))

        return  prev, now, nxt

    def get_current_program_playing(self, channelId):
        schedule = self._get_broadcast_now(channelId)

        return self._extract_schedule(schedule)

    def list_channels(self, tv_channels, is_folder=True):
        listing = []
        entitlementId = self.fetch_from_data("entitlement")["entitlementId"]

        for i in range(len(tv_channels)):
            if (
                    not bool(tv_channels[i]["channelProperties"]["radio"])
                    and bool(tv_channels[i]["channelProperties"]["live"])
                    and any(tv_channels[i]["channelPolicies"]["linearEndpoints"])
                    and any(x in entitlementId for x in tv_channels[i]["channelAvailability"]["oasisId"])
            ):

                if sys.version_info[0] == 3:
                    name = tv_channels[i]["channelIdentification"]["name"]
                else:
                    name = (tv_channels[i]["channelIdentification"]["name"]). \
                        encode("utf-8")

                squareLogo = tv_channels[i]["channelProperties"]["squareLogo"]
                liveThumbnailURL = tv_channels[i]["channelProperties"]["liveThumbnailURL"]
                stbUniqueName = tv_channels[i]["channelIdentification"]["stbUniqueName"]
                channelId = tv_channels[i]["channelIdentification"]["channelId"]

                list_item = self.kodi_wrapper. \
                    create_list_item(name, squareLogo, liveThumbnailURL, {"plot": name})

                import base64
                url = self.kodi_wrapper.url_for(
                    "channel_info",
                    channel_name=base64.b64encode(name),
                    logo=base64.b64encode(squareLogo),
                    channel=stbUniqueName,
                    channelId=channelId
                )

                listing.append((url, list_item, is_folder))

        self.kodi_wrapper.add_dir_items(listing)
        self.kodi_wrapper.sort_method(SORT_METHOD_LABEL_IGNORE_THE)
        self.kodi_wrapper.end_directory()

    def show_info_stream(self, name, logo, channel, channel_id):
        prev, now, nxt = self.get_current_program_playing(channel_id)

        guide = ""
        if prev:
            guide += "[B]Previously: [/B]" + "\n" +  prev.get("title") + "\n" + "[COLOR green]" \
                     + prev.get("start") + "[/COLOR]" + " >> " + "[COLOR red]" \
                     + prev.get("end") + "[/COLOR] " + "\n\n"
        if now:
            guide += "[B]Currently Playing: [/B]" + "\n" + now.get("title") + "\n" + "[COLOR green]" \
                     + now.get("start") + "[/COLOR]" + " >> " + "[COLOR red]" \
                     + now.get("end") + "[/COLOR] " + "\n\n"
        if nxt:
            guide += "[B]Coming up next: [/B]" + "\n" + nxt.get("title") + "\n" + "[COLOR green]" \
                     + nxt.get("start") + "[/COLOR]" + " >> " + "[COLOR red]" \
                     + nxt.get("end") + "[/COLOR] " + "\n\n"

        list_item = self.kodi_wrapper. \
            create_list_item(name, logo, now.get("poster"),
                             {"plot": guide if now.get("title") else name}, "true")

        url = self.kodi_wrapper.url_for("play_livestream", channel=channel)

        self.kodi_wrapper.add_dir_item(url, list_item, 1)
        self.kodi_wrapper.sort_method(SORT_METHOD_LABEL_IGNORE_THE)
        self.kodi_wrapper.end_directory()

    def play_live_stream(self, stream_url):
        bit_rate = helperclasses.BitRate(self.kodi_wrapper)
        deviceId = self.fetch_from_data("IdTokens")["deviceId"]
        customerId = self.fetch_from_data("entitlement")["customer_id"]

        self.kodi_wrapper.play_live_stream(deviceId, customerId, stream_url, bit_rate.bitrate)

    def select_manifest_url(self, channel):
        for _ in range(2):
            try:
                accessToken = self.fetch_from_data("OAuthTokens")["accessToken"]
                deviceId = self.fetch_from_data("IdTokens")["deviceId"]

                r = make_request(session, "POST", "https://api.yeloplay.be/api/v1/stream/start",
                                 authorization_header(deviceId, accessToken), None,
                                 stream_start_data(deviceId, channel, self.streaming_protocol),
                                 False, None, self.testing)

                j = r.json()
                if not j.get("errors"):
                    return j["stream"]["streamDescriptor"]["manifest"]
                else:
                    title, message = self.get_error_message(j["errors"][0]["code"])
                    self.kodi_wrapper.dialog_ok(title, message)

                    return False
            except ValueError:
                """ Session might be expired """
                self.login()
