# ruff: noqa: D102
"""Orange provider template."""

import json
import re
from abc import ABC
from datetime import date, datetime, timedelta
from time import strptime
from typing import List
from urllib.parse import urlencode

import xbmc
from requests import Session
from requests.exceptions import JSONDecodeError, RequestException

from lib.exceptions import AuthenticationRequired, StreamDataDecodeError, StreamNotIncluded
from lib.providers.abstract_provider import AbstractProvider
from lib.utils.kodi import build_addon_url, get_addon_setting, get_drm, get_global_setting, log, set_addon_setting
from lib.utils.request import request, request_json

_PROGRAMS_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/live/v3/applications/STB4PC/programs?period={period}&epgIds=all&mco={mco}"
_CATCHUP_CHANNELS_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/catchup/v4/applications/PC/channels"
_CATCHUP_ARTICLES_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/catchup/v4/applications/PC/channels/{channel_id}/categories/{category_id}"
_CATCHUP_VIDEOS_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/catchup/v4/applications/PC/groups/{group_id}"
_CHANNELS_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/pds/v1/live/ew?everywherePopulation=OTT_Metro"

_LIVE_STREAM_ENDPOINT = "https://mediation-tv.orange.fr/all/api-gw/stream/v2/auth/accountToken/live/{stream_id}?deviceModel=WEB_PC&customerOrangePopulation=OTT_Metro"
_CATCHUP_STREAM_ENDPOINT = "https://mediation-tv.orange.fr/all/api-gw/catchup/v4/auth/accountToken/applications/PC/videos/{stream_id}/stream?terminalModel=WEB_PC&terminalId="

_STREAM_LOGO_URL = "https://proxymedia.woopic.com/api/v1/images/2090{path}"
_LIVE_HOMEPAGE_URL = "https://tv.orange.fr/"
_LOGIN_URL = "https://login.orange.fr"

_LICENSE_ENDPOINT = "https://mediation-tv.orange.fr/all/api-gw/license/v1/auth/accountToken"


class AbstractOrangeProvider(AbstractProvider, ABC):
    """Abstract Orange Provider."""

    chunks_per_day = 2
    mco = "OFR"
    groups = {}

    def get_live_stream_info(self, stream_id: str) -> dict:
        """Get live stream info."""
        return self._get_stream_info(_LIVE_STREAM_ENDPOINT, stream_id)

    def get_catchup_stream_info(self, stream_id: str) -> dict:
        """Get catchup stream info."""
        return self._get_stream_info(_CATCHUP_STREAM_ENDPOINT, stream_id)

    def get_streams(self) -> list:
        """Load stream data from Orange and convert it to JSON-STREAMS format."""
        # @todo: use new API to check if channel is part of subscription
        channels = request_json(_CHANNELS_ENDPOINT, default={"channels": {}})["channels"]
        channels.sort(key=lambda channel: channel["displayOrder"])

        log(f"{len(channels)} channels found", xbmc.LOGINFO)

        return [
            {
                "id": str(channel["idEPG"]),
                "name": channel["name"],
                "preset": str(channel["displayOrder"]),
                "logo": self._extract_logo(channel["logos"]),
                "stream": build_addon_url(f"/stream/live/{self._get_channel_live_id(channel)}"),
                "group": [group_name for group_name in self.groups if int(channel["idEPG"]) in self.groups[group_name]],
            }
            for channel in channels
        ]

    def _get_channel_live_id(self, channel: dict) -> str:
        """Get live id for given channel."""
        return channel["technicalChannels"]["live"][0]["liveTargetURLRelativePath"]

    def get_epg(self) -> dict:
        """Load EPG data from Orange and convert it to JSON-EPG format."""
        past_days_to_display = get_global_setting("epg.pastdaystodisplay", int)
        future_days_to_display = get_global_setting("epg.futuredaystodisplay", int)

        start_day = datetime.combine(date.today() - timedelta(days=past_days_to_display), datetime.min.time())
        days_to_display = past_days_to_display + future_days_to_display

        programs = self._get_programs(start_day, days_to_display, self.chunks_per_day, self.mco)
        log(f"{len(programs)} EPG entries found", xbmc.LOGINFO)

        epg = {}

        for program in programs:
            if program["channelId"] not in epg:
                epg[program["channelId"]] = []

            if program["programType"] != "EPISODE":
                title = program["title"]
                subtitle = None
                episode = None
            else:
                title = program["season"]["serie"]["title"]
                subtitle = program["title"]
                season_number = program["season"]["number"]
                episode_number = program.get("episodeNumber", None)
                episode = f"S{season_number}E{episode_number}"

            image = None
            if isinstance(program["covers"], list):
                for cover in program["covers"]:
                    if cover["format"] == "RATIO_16_9":
                        image = program["covers"][0]["url"]

            start = datetime.fromtimestamp(program["diffusionDate"]).astimezone().replace(microsecond=0).isoformat()
            stop = datetime.fromtimestamp(program["diffusionDate"] + program["duration"]).astimezone().isoformat()

            epg[program["channelId"]].append(
                {
                    "start": start,
                    "stop": stop,
                    "title": title,
                    "subtitle": subtitle,
                    "episode": episode,
                    "description": program["synopsis"],
                    "genre": program["genre"] if program["genreDetailed"] is None else program["genreDetailed"],
                    "image": image,
                }
            )

        return epg

    def get_catchup_items(self, levels: List[str]) -> list:
        """Return a list of directory items for the specified levels."""
        depth = len(levels)
        item_getters = [
            self._get_catchup_channels,
            self._get_catchup_categories,
            self._get_catchup_articles,
            self._get_catchup_videos,
        ]

        return item_getters[depth](*levels)

    def _get_catchup_channels(self) -> list:
        """Load available catchup channels."""
        channels = request_json(_CATCHUP_CHANNELS_ENDPOINT, default=[])

        return [
            {
                "is_folder": True,
                "label": str(channel["name"]).upper(),
                "path": build_addon_url(f"/catchup/{channel['id']}"),
                "art": {"thumb": channel["logos"]["ref_millenials_partner_white_logo"]},
            }
            for channel in channels
        ]

    def _get_catchup_categories(self, channel_id: str) -> list:
        """Return a list of catchup categories for the specified channel id."""
        url = f"{_CATCHUP_CHANNELS_ENDPOINT}/{channel_id}"
        categories = request_json(url, default={"categories": {}})["categories"]

        return [
            {
                "is_folder": True,
                "label": category["name"][0].upper() + category["name"][1:],
                "path": build_addon_url(f"/catchup/{channel_id}/{category['id']}"),
            }
            for category in categories
        ]

    def _get_catchup_articles(self, channel_id: str, category_id: str) -> list:
        """Return a list of catchup groups for the specified channel id and category id."""
        url = _CATCHUP_ARTICLES_ENDPOINT.format(channel_id=channel_id, category_id=category_id)
        articles = request_json(url, default={"articles": {}})["articles"]

        return [
            {
                "is_folder": True,
                "label": article["title"],
                "path": build_addon_url(f"/catchup/{channel_id}/{category_id}/{article['id']}"),
                "art": {"poster": article["covers"]["ref_16_9"]},
            }
            for article in articles
        ]

    def _get_catchup_videos(self, channel_id: str, category_id: str, article_id: str) -> list:
        """Return a list of catchup videos for the specified channel id and article id."""
        url = _CATCHUP_VIDEOS_ENDPOINT.format(group_id=article_id)
        videos = request_json(url, default={"videos": {}})["videos"]

        return [
            {
                "is_folder": False,
                "label": video["title"],
                "path": build_addon_url(f"/stream/catchup/{video['id']}"),
                "art": {"poster": video["covers"]["ref_16_9"]},
                "info": {
                    "duration": int(video["duration"]) * 60,
                    "genres": video["genres"],
                    "plot": video["longSummary"],
                    "premiered": datetime.fromtimestamp(int(video["broadcastDate"]) / 1000).strftime("%Y-%m-%d"),
                    "year": int(video["productionDate"]),
                },
            }
            for video in videos
        ]

    def _get_stream_info(self, stream_endpoint: str, stream_id: str) -> dict:
        """Load stream info from Orange."""
        tv_token, tv_token_expires, wassup = self._retrieve_auth_data()

        try:
            stream_endpoint_url = stream_endpoint.format(stream_id=stream_id)
            headers = {"tv_token": f"Bearer {tv_token}", "Cookie": f"wassup={wassup}"}
            res = request("GET", stream_endpoint_url, headers=headers)
            stream = res.json()
            log("Initiate new session", xbmc.LOGINFO)
        except RequestException as e:
            if e.response.status_code == 403:
                raise StreamNotIncluded() from e
            else:
                raise AuthenticationRequired("Cannot initiate new session") from e
        except JSONDecodeError as e:
            raise StreamDataDecodeError() from e

        return self._compute_stream_info(stream, tv_token, wassup)

    def _compute_stream_info(self, stream: dict, tv_token: str, wassup: str) -> dict:
        """Compute stream info."""
        protectionData = stream.get("protectionData") or stream.get("protectionDatas")
        path = stream.get("streamURL") or stream.get("url")

        license_server_url = _LICENSE_ENDPOINT if stream.get("url") is None else ""

        for system in protectionData:
            if system.get("keySystem") == get_drm():
                license_server_url += system.get("laUrl")

        stream_info = {
            "path": path,
            "protocol": "mpd",
            "mime_type": "application/xml+dash",
            "drm_config": {
                "license_type": get_drm(),
                "license_key": "|".join(
                    {
                        "licence_server_url": license_server_url,
                        "headers": urlencode(
                            {
                                "tv_token": f"Bearer {tv_token}",
                                "Content-Type": "",
                                "Cookie": f"wassup={wassup}",
                            }
                        ),
                        "post_data": "R{SSM}",
                        "response_data": "",
                    }.values()
                ),
            },
        }

        log(stream_info, xbmc.LOGDEBUG)
        return stream_info

    def _retrieve_auth_data(self, login: str = None, password: str = None) -> (str, str, str):
        """Retreive auth data from Orange (tv token and wassup cookie)."""
        provider_session_data = get_addon_setting("provider.session_data", dict)
        tv_token, tv_token_expires, wassup = (
            provider_session_data.get(k) for k in ("tv_token", "tv_token_expires", "wassup")
        )

        if not tv_token_expires or datetime.utcnow().timestamp() > tv_token_expires:
            session = Session()

            if not self._is_wassup_expired(wassup):
                log("Cookie reuse", xbmc.LOGINFO)
                session.headers["Cookie"] = f"wassup={wassup}"

            try:
                response = request("GET", _LIVE_HOMEPAGE_URL, session=session)
                tv_token = json.loads(re.search('"token":(".*?")', response.text).group(1))
            except AttributeError:
                log("Login required", xbmc.LOGINFO)
                self._login(session)
                response = request("GET", _LIVE_HOMEPAGE_URL, session=session)
                tv_token = json.loads(re.search('"token":(".*?")', response.text).group(1))

            tv_token_expires = datetime.utcnow().timestamp() + 30 * 60

            if "wassup" in session.cookies:
                wassup = session.cookies.get("wassup")

            provider_session_data = {
                "tv_token": tv_token,
                "tv_token_expires": tv_token_expires,
                "wassup": wassup,
            }
            set_addon_setting("provider.session_data", provider_session_data)

        log(f"tv_token: {tv_token}, tv_token_expires: {tv_token_expires}, wassup: {wassup}", xbmc.LOGDEBUG)
        return tv_token, tv_token_expires, wassup

    def _is_wassup_expired(self, wassup: str) -> bool:
        try:
            wassup = bytes.fromhex(wassup).decode()
            xwvd = re.search("\|X_WASSUP_VALID_DATE=(.*?)\|", wassup).group(1)
            wassup_expires = datetime(*(strptime(xwvd, "%Y%m%d%H%M%S")[0:6])).timestamp()
            return datetime.utcnow().timestamp() > wassup_expires
        except (TypeError, AttributeError):
            return True

    def _login(self, session):
        """Login to Orange."""
        login, password = get_addon_setting("provider.username"), get_addon_setting("provider.password")
        session.headers = {
            "Accept": "application/xhtml+xml,application/xml",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
        }

        try:
            request("GET", _LOGIN_URL, headers=session.headers, session=session)
        except RequestException:
            log("Error while authenticating (init)", xbmc.LOGWARNING)
            return

        try:
            request(
                "POST",
                f"{_LOGIN_URL}/api/login",
                data=json.dumps({"login": login, "params": {}}),
                session=session,
            )
        except RequestException:
            log("Error while authenticating (login)", xbmc.LOGWARNING)
            return

        try:
            request(
                "POST",
                f"{_LOGIN_URL}/api/password",
                data=json.dumps({"password": password, "remember": True}),
                s=session,
            )
        except RequestException:
            log("Error while authenticating (password)", xbmc.LOGWARNING)

    def _extract_logo(self, logos: list, definition_type: str = "mobileAppliDark") -> str:
        for logo in logos:
            if logo["definitionType"] == definition_type:
                return _STREAM_LOGO_URL.format(path=logo["listLogos"][0]["path"])

        return None

    def _get_programs(self, start_day: datetime, days_to_display: int, chunks_per_day: int, mco: str = "OFR") -> list:
        """Return the programs for today (default) or the specified period."""
        programs = []
        start_day_timestamp = start_day.timestamp()
        chunk_duration = 24 * 60 * 60 / chunks_per_day

        for chunk in range(0, days_to_display * chunks_per_day):
            period_start = (start_day_timestamp + chunk_duration * chunk) * 1000
            period_end = (start_day_timestamp + chunk_duration * (chunk + 1)) * 1000

            try:
                period = f"{int(period_start)},{int(period_end)}"
            except ValueError:
                period = "today"

            url = _PROGRAMS_ENDPOINT.format(period=period, mco=mco)
            programs.extend(request_json(url, default=[]))

        return programs
