# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
import threading
import time
import logging
import requests

from data import USER_AGENT
from helpers.helperclasses import Credentials, EPG, PluginCache
from helpers.helpermethods import (authorization_payload, create_token, device_authorize, device_payload, login_payload,
                                   oauth_payload, oauth_refresh_token_payload, regex, stream_payload, timestamp_to_datetime)
from kodiwrapper import KodiWrapper
from yelo_exceptions import NotAuthorizedException, YeloException, ForbiddenException

try:  # Python 3
    from urllib.parse import quote
except ImportError:  # Python 2
    from urllib2 import quote

BASE_URL = "https://api.yeloplay.be/api/v1"
CALLBACK_URL = "https://www.yeloplay.be/openid/callback"

EPG_DAYS = 2

MAXTHREADS = 5
SEMAPHORE = threading.Semaphore(value=MAXTHREADS)
VERIFY = True

_LOGGER = logging.getLogger('plugin')


class YeloErrors:  # pylint: disable=no-init
    # noinspection PyTypeChecker
    @classmethod
    def get_error_message(cls, errid):
        resp = requests.get("https://api.yeloplay.be/api/v1/masterdata?platform=Web&fields=errors", verify=VERIFY)

        errors = resp.json().get('masterData').get('errors')

        res = next((error for error in errors if error.get('id') == errid), "")

        if not res:
            return None

        return res["title"]["locales"]["en"], res["subtitle"]["locales"]["en"]


class YeloApi:  # pylint: disable=useless-object-inheritance
    session = requests.Session()
    session.verify = VERIFY
    session.headers['User-Agent'] = USER_AGENT

    def __init__(self):
        self.auth_tries = 0
        if not self.oauth_in_cache:
            self._execute_required_steps()

    @staticmethod
    def _display_error_message(response_data):
        title, message = YeloErrors.get_error_message(response_data["errors"][0]["code"])
        KodiWrapper.dialog_ok(title, message)

    @property
    def oauth_in_cache(self):
        return PluginCache.key_exists("OAuthTokens")

    @staticmethod
    def extract_auth_token(url):
        callback_key = regex(r"(?<=code=)\w{0,32}", url)
        return callback_key

    def _execute_required_steps(self):
        self._authorize()
        if self._login():
            self._register_device()
            self._request_oauth_tokens()
            self._get_entitlements()

    def _customer_features(self):
        device_id = PluginCache.get_by_key("device_id")
        oauth_tokens = PluginCache.get_by_key("OAuthTokens")

        if not oauth_tokens:
            return {}

        resp = self.session.get(BASE_URL + "/session/lookup?include=customerFeatures",
                                headers={
                                    "Content-Type": "application/json;charset=utf-8",
                                    "X-Yelo-DeviceId": device_id,
                                    "Authorization": authorization_payload(oauth_tokens.get('accessToken'))
                                })
        return resp.json()

    def _authorize(self):
        state = create_token(20)
        nonce = create_token(32)

        self.session.get("https://login.prd.telenet.be/openid/oauth/authorize"
                         "?client_id={}&state={}&nonce={}&redirect_uri={}"
                         "&response_type=code&prompt=login".
                         format("yelo", state, nonce, quote(CALLBACK_URL)),
                         allow_redirects=False)

    def _login(self):
        creds = Credentials()

        if not creds.are_filled_in():
            KodiWrapper.dialog_ok(KodiWrapper.get_localized_string(32014),
                                  KodiWrapper.get_localized_string(32015))
            KodiWrapper.open_settings()
            creds.reload()

        resp = self.session.post("https://login.prd.telenet.be/openid/login.do",
                                 data=login_payload(creds.username, creds.password))

        last_response = resp.history[-1]

        try:
            self.auth_tries += 1

            if "Location" in last_response.headers:
                token = self.extract_auth_token(last_response.headers.get('Location'))
                if not token:
                    raise NotAuthorizedException()
                PluginCache.set_data({"auth_token": token})
                return True
        except NotAuthorizedException:
            KodiWrapper.dialog_ok(KodiWrapper.get_localized_string(32006),
                                  KodiWrapper.get_localized_string(32007))

            if self.auth_tries < 2:
                KodiWrapper.open_settings()
                self._execute_required_steps()

        return False

    def _device_authorize(self, device_id):
        oauth_tokens = PluginCache.get_by_key("OAuthTokens")

        resp = self.session.post(BASE_URL + "/device/authorize",
                                 headers={
                                     "Content-Type": "application/json;charset=utf-8",
                                     "X-Yelo-DeviceId": device_id,
                                     "Authorization": authorization_payload(oauth_tokens["accessToken"])
                                 },
                                 data=device_authorize(device_id, "YeloPlay"))

        return resp

    def _register_device(self):
        resp = self.session.post(BASE_URL + "/device/register",
                                 headers={
                                     "Content-Type": "application/json;charset=utf-8"
                                 },
                                 data=device_payload(),
                                 allow_redirects=False)
        try:
            json_data = resp.json()
            device_id = json_data.get('deviceRegistration').get('id')
            PluginCache.set_data({"device_id": device_id})
        except (ValueError, KeyError) as exc:
            _LOGGER.error(exc)
        return resp

    def _request_oauth_tokens(self):
        auth_token = PluginCache.get_by_key("auth_token")
        device_id = PluginCache.get_by_key("device_id")

        resp = self.session.post(BASE_URL + "/oauth/token",
                                 headers={
                                     "Content-Type": "application/json;charset=utf-8",
                                     "X-Yelo-DeviceId": device_id
                                 },
                                 data=oauth_payload(auth_token, CALLBACK_URL),
                                 allow_redirects=False)

        try:
            json_data = resp.json()
            oauth_data = json_data.get('OAuthTokens')

            if oauth_data and oauth_data.get('status').upper() == 'SUCCESS':
                PluginCache.set_data({"OAuthTokens": oauth_data})
        except (ValueError, KeyError) as exc:
            _LOGGER.error(exc)

    def _refresh_oauth_token(self):
        device_id = PluginCache.get_by_key("device_id")
        refresh_token = PluginCache.get_by_key("OAuthTokens").get('refreshToken')

        resp = self.session.post(BASE_URL + "/oauth/token",
                                 headers={
                                     "Content-Type": "application/json;charset=utf-8",
                                     "X-Yelo-DeviceId": device_id,
                                 },
                                 data=oauth_refresh_token_payload(refresh_token, CALLBACK_URL),
                                 allow_redirects=False)

        try:
            json_data = resp.json()
            oauth_data = json_data.get('OAuthTokens')

            if oauth_data and oauth_data.get('status') == "SUCCESS":
                PluginCache.set_data({"OAuthTokens": oauth_data})
        except (ValueError, KeyError) as exc:
            _LOGGER.error(exc)

    def _start_stream(self, channel):
        response_data = None
        max_iterations = 2
        current_iteration = 0

        device_id = PluginCache.get_by_key("device_id")

        while current_iteration < max_iterations:
            oauth_tokens = PluginCache.get_by_key("OAuthTokens")

            try:
                response = self.session.post(BASE_URL + "/stream/start",
                                             headers={
                                                 "Content-Type": "application/json;charset=utf-8",
                                                 "X-Yelo-DeviceId": device_id,
                                                 "Authorization": authorization_payload(
                                                     oauth_tokens["accessToken"])
                                             },
                                             data=stream_payload(device_id, channel))

                try:
                    response_data = response.json()
                except ValueError as exc:
                    _LOGGER.error(exc)

                current_iteration += 1

                if response.status_code == 401:
                    raise NotAuthorizedException("Unauthorized")
                if response.status_code == 403:
                    raise ForbiddenException("Forbidden")
                break
            except NotAuthorizedException:
                self._refresh_oauth_token()
            except ForbiddenException:
                stream = response_data.get('stream')
                if stream is None:
                    self._display_error_message(response_data)
                    return None
                if stream.get('authorizationResult') is None or stream.get('authorizationResult').get('resultCode').upper() != "DEVICE_AUTHORIZATION_REQUIRED":
                    self._display_error_message(response_data)
                    return None
                self._check_registered_devices(response_data)
        return response_data

    def _check_registered_devices(self, response_data):
        devices_registered = response_data["stream"]["authorizationResult"]["authorizedDevices"]
        devices_maximum = response_data["stream"]["authorizationResult"]["allowedDevices"]

        if devices_maximum - devices_registered == 0:
            self._display_error_message(response_data)
            return self._register_device()

        device_id = PluginCache.get_by_key("device_id")
        return self._device_authorize(device_id)

    def get_manifest(self, channel):
        start_stream_response = self._start_stream(channel)

        if not start_stream_response:
            raise YeloException("Start stream returned an empty response.")

        stream = start_stream_response.get('stream')
        stream_desc = stream.get('streamDescriptor')
        manifest = stream_desc.get('manifest')
        return manifest

    def _get_entitlements(self):
        if not PluginCache.get_by_key("entitlements"):
            try:
                customer_features = self._customer_features()

                entitlements = [int(item["id"])
                                for item in customer_features["linked"]["customerFeatures"]["entitlements"]]
                customer_id = customer_features["loginSession"]["user"]["links"]["customerFeatures"]

                PluginCache.set_data({"entitlements": {
                    "entitlementId": entitlements,
                    "customer_id": customer_id}})
            except (ValueError, KeyError) as exc:
                _LOGGER.error(exc)

        return PluginCache.get_by_key("entitlements")

    @staticmethod
    def _get_entitled_channels(tv_channels):
        allowed_channels = []
        entitlements = PluginCache.get_by_key('entitlements')
        if not entitlements:
            return []

        entitlement_ids = entitlements.get('entitlementId')
        if not entitlement_ids:
            return []

        for tv_channel in tv_channels:
            if (
                    bool(tv_channel["channelProperties"]["live"])
                    and any(tv_channel["channelPolicies"]["linearEndpoints"])
                    and any(x in entitlement_ids for x in tv_channel["channelAvailability"]["oasisId"])
            ):
                allowed_channels.append(tv_channel)

        return allowed_channels

    @classmethod
    def get_channels(cls):
        resp = requests.get(BASE_URL + "/epg/channel/list?platform=Web", verify=VERIFY)

        try:
            json_data = resp.json()
            tv_channels = json_data["serviceCatalog"]["tvChannels"]
            allowed_tv_channels = cls._get_entitled_channels(tv_channels)
            return allowed_tv_channels
        except (ValueError, KeyError) as exc:
            _LOGGER.error(exc)

        return []

    def get_channels_iptv(self):
        allowed_tv_channels = self.get_channels()

        channels = []
        for channel in allowed_tv_channels:
            name = channel.get('channelIdentification', {}).get('name')
            epg_id = channel.get('channelIdentification', {}).get('name')
            channel_id = channel.get('channelIdentification', {}).get('stbUniqueName')
            logo = channel.get('channelProperties', {}).get('squareLogo')
            channels.append(dict(
                name=name,
                id=epg_id,
                logo=logo,
                stream=KodiWrapper.url_for('play_id', channel_id=channel_id),
            ))
        return channels

    @classmethod
    def _get_schedule(cls, channel_id):
        from datetime import datetime, timedelta

        today = datetime.today()

        name = ""
        broadcasts = []
        for i in range(EPG_DAYS):
            date_str = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            resp = requests.get("https://pubba.yelo.prd.telenet-ops.be/v1/"
                                "events/schedule-day/outformat/json/lng/nl/channel/"
                                "{}/day/{}/".format(channel_id, date_str), verify=VERIFY)

            schedule = resp.json()["schedule"]
            broadcast = schedule[0]["broadcast"]
            name = schedule[0]["name"]
            broadcasts.extend(broadcast)

        return dict(name=name, broadcasts=broadcasts)

    @classmethod
    def __epg(cls, channel_id, channels_ref):
        SEMAPHORE.acquire()

        try:
            schedule = cls._get_schedule(channel_id)
            channel_name = schedule.get("name")
            broadcasts = schedule.get("broadcasts")

            channels = []
            for broadcast in broadcasts:
                channels.append(dict(
                    id=channel_id,
                    start=timestamp_to_datetime(broadcast.get('starttime')),
                    stop=timestamp_to_datetime(broadcast.get('endtime')),
                    title=broadcast.get('title', ''),
                    description=broadcast.get('shortdescription'),
                    subtitle=broadcast.get('contentlabel'),
                    image=broadcast.get('image'),
                ))

            channels_ref.update({channel_name: channels})

            time.sleep(0.01)
            SEMAPHORE.release()
        except (ValueError, KeyError) as exc:
            _LOGGER.error(exc)

    @classmethod
    def _epg(cls, tv_channels):
        threads = []
        channels_ref = {}

        channel_ids = [item["id"] for item in tv_channels]
        for channel_id in channel_ids:
            thread = threading.Thread(target=cls.__epg, args=(channel_id, channels_ref))
            thread.start()
            threads.append(thread)

        # wait for all threads to terminate
        for thread in threads:
            thread.join()

        return channels_ref

    @classmethod
    def get_epg(cls, tv_channels):
        return cls._epg(tv_channels)

    @staticmethod
    def get_cached_epg():
        return EPG.get_from_cache()

    @staticmethod
    def _create_guide_from_channel_info(previous, current, upcoming):
        guide = ""
        if previous:
            guide += "[B]Previously: [/B]\n%s\n" % previous
        if current:
            guide += "[B]Currently playing: [/B]\n%s\n" % current
        if upcoming:
            guide += "[B]Coming up next: [/B]\n%s\n" % upcoming

        return guide
