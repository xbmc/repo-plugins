# ruff: noqa: D102
"""Orange provider template."""

import json
import re
from abc import ABC
from datetime import date, datetime, timedelta
from typing import List
from urllib.parse import urlencode

import xbmc
from requests import Session
from requests.exceptions import JSONDecodeError, RequestException

from lib.exceptions import AuthenticationRequired, StreamDataDecodeError, StreamNotIncluded
from lib.providers.abstract_provider import AbstractProvider
from lib.utils.kodi import build_addon_url, get_addon_setting, get_drm, get_global_setting, log, set_addon_setting
from lib.utils.request import request, request_json, to_cookie_string

_PROGRAMS_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/live/v3/applications/STB4PC/programs?period={period}&epgIds=all&mco={mco}"
_CATCHUP_CHANNELS_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/catchup/v4/applications/PC/channels"
_CATCHUP_ARTICLES_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/catchup/v4/applications/PC/channels/{channel_id}/categories/{category_id}"
_CATCHUP_VIDEOS_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/catchup/v4/applications/PC/groups/{group_id}"
_CHANNELS_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/pds/v1/live/ew?everywherePopulation=OTT_Metro"

_LIVE_STREAM_ENDPOINT = "https://mediation-tv.orange.fr/all/api-gw/live/v3/auth/accountToken/applications/PC/channels/{stream_id}/stream?terminalModel=WEB_PC&terminalId={terminal_id}"
_CATCHUP_STREAM_ENDPOINT = "https://mediation-tv.orange.fr/all/api-gw/catchup/v4/auth/accountToken/applications/PC/videos/{stream_id}/stream?terminalModel=WEB_PC&terminalId={terminal_id}"

_STREAM_LOGO_URL = "https://proxymedia.woopic.com/api/v1/images/2090{path}"
_LIVE_HOMEPAGE_URL = "https://chaines-tv.orange.fr/"
_CATCHUP_VIDEO_URL = "https://replay.orange.fr/videos/{stream_id}"


class AbstractOrangeProvider(AbstractProvider, ABC):
    """Abstract Orange Provider."""

    chunks_per_day = 2
    mco = "OFR"
    groups = {}

    def get_live_stream_info(self, stream_id: str) -> dict:
        """Get live stream info."""
        auth_url = _LIVE_HOMEPAGE_URL
        return self._get_stream_info(auth_url, _LIVE_STREAM_ENDPOINT, stream_id)

    def get_catchup_stream_info(self, stream_id: str) -> dict:
        """Get catchup stream info."""
        auth_url = _CATCHUP_VIDEO_URL.format(stream_id=stream_id)
        return self._get_stream_info(auth_url, _CATCHUP_STREAM_ENDPOINT, stream_id)

    def get_streams(self) -> list:
        """Load stream data from Orange and convert it to JSON-STREAMS format."""
        channels = request_json(_CHANNELS_ENDPOINT, default={"channels": {}})["channels"]
        channels.sort(key=lambda channel: channel["displayOrder"])

        log(f"{len(channels)} channels found", xbmc.LOGINFO)

        return [
            {
                "id": str(channel["idEPG"]),
                "name": channel["name"],
                "preset": str(channel["displayOrder"]),
                "logo": self._extract_logo(channel["logos"]),
                "stream": build_addon_url(f"/stream/live/{channel['idEPG']}"),
                "group": [group_name for group_name in self.groups if int(channel["idEPG"]) in self.groups[group_name]],
            }
            for channel in channels
        ]

    def get_epg(self) -> dict:
        """Load EPG data from Orange and convert it to JSON-EPG format."""
        start_day = datetime.timestamp(
            datetime.combine(
                date.today() - timedelta(days=get_global_setting("epg.pastdaystodisplay", int)), datetime.min.time()
            )
        )

        days_to_display = get_global_setting("epg.futuredaystodisplay", int) + get_global_setting(
            "epg.pastdaystodisplay", int
        )

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

            epg[program["channelId"]].append(
                {
                    "start": datetime.fromtimestamp(program["diffusionDate"])
                    .astimezone()
                    .replace(microsecond=0)
                    .isoformat(),
                    "stop": (
                        datetime.fromtimestamp(program["diffusionDate"] + program["duration"]).astimezone()
                    ).isoformat(),
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

        if depth == 0:
            return self._get_catchup_channels()
        elif depth == 1:
            return self._get_catchup_categories(levels[0])
        elif depth == 2:
            return self._get_catchup_articles(levels[0], levels[1])
        elif depth == 3:
            return self._get_catchup_videos(levels[0], levels[1], levels[2])

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
        url = _CATCHUP_CHANNELS_ENDPOINT + "/" + channel_id
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

    def _get_stream_info(self, auth_url: str, stream_endpoint: str, stream_id: str) -> dict:
        """Load stream info from Orange."""
        provider_session_data = get_addon_setting("provider.session_data", dict)
        tv_token, terminal_id, wassup = (provider_session_data.get(k) for k in ("tv_token", "terminal_id", "wassup"))
        res = None

        if tv_token and terminal_id:
            try:
                stream_endpoint_url = stream_endpoint.format(stream_id=stream_id, terminal_id=terminal_id)
                headers = {"tv_token": f"Bearer {tv_token}", "Cookie": f"wassup={wassup}"}
                res = request("GET", stream_endpoint_url, headers=headers)
                log("Use stored session data", xbmc.LOGINFO)
            except RequestException as e:
                if e.response.status_code == 403:
                    raise StreamNotIncluded() from e
                else:
                    log("Stored session data expired", xbmc.LOGWARNING)

        if res is None:
            set_addon_setting("provider.session_data", {})

            try:
                if get_addon_setting("provider.use_credentials", bool):
                    username, password = get_addon_setting("provider.username"), get_addon_setting("provider.password")
                    tv_token, terminal_id, wassup = self._retrieve_auth_data(auth_url, username, password)
                else:
                    tv_token, terminal_id, wassup = self._retrieve_auth_data(auth_url)
            except RequestException as e:
                raise AuthenticationRequired("Authentication page load failed") from e
            except AttributeError as e:
                raise AuthenticationRequired("Cannot extract tv token or household id") from e

            try:
                stream_endpoint_url = stream_endpoint.format(stream_id=stream_id, terminal_id=terminal_id)
                headers = {"tv_token": f"Bearer {tv_token}", "Cookie": f"wassup={wassup}"}
                res = request("GET", stream_endpoint_url, headers=headers)
                log("Initiate new session", xbmc.LOGINFO)
            except RequestException as e:
                if e.response.status_code == 403:
                    raise StreamNotIncluded() from e
                else:
                    raise AuthenticationRequired("Cannot initiate new session") from e

        try:
            stream = res.json()
        except JSONDecodeError as e:
            raise StreamDataDecodeError() from e

        provider_session_data = {
            "tv_token": tv_token,
            "terminal_id": terminal_id,
            "wassup": wassup,
        }

        set_addon_setting("provider.session_data", provider_session_data)
        return self._compute_stream_info(stream, tv_token, wassup)

    def _compute_stream_info(self, stream: dict, tv_token: str, wassup: str) -> dict:
        """Compute stream info."""
        protectionData = (
            stream.get("protectionData") if stream.get("protectionData") is not None else stream.get("protectionDatas")
        )

        license_server_url = None

        for system in protectionData:
            if system.get("keySystem") == get_drm():
                license_server_url = system.get("laUrl")

        stream_info = {
            "path": stream.get("url"),
            "protocol": "mpd",
            "mime_type": "application/xml+dash",
            "drm_config": {  # Keeping items in order
                "drm": get_drm(),
                "license_server_url": license_server_url,
                "headers": urlencode(
                    {
                        "tv_token": f"Bearer {tv_token}",
                        "Content-Type": "",
                        "Cookie": f"wassup={wassup}",
                    }
                ),
            },
        }

        log(stream_info, xbmc.LOGDEBUG)
        return stream_info

    def _retrieve_auth_data(self, auth_url: str, login: str = None, password: str = None) -> (str, str, str):
        """Retreive auth data from Orange (tv token and terminal id, plus wassup cookie when using credentials)."""
        cookies = {}

        if login or password:
            cookies = self._login(login, password)

        res = request("GET", auth_url, headers={"Cookie": to_cookie_string(cookies, ["trust", "wassup"])})

        tv_token = re.search('instanceInfo:{token:"([a-zA-Z0-9-_.]+)"', res.text).group(1)
        household_id = re.search('householdId:"([A-Z0-9]+)"', res.text).group(1)

        log(f"tv_token: {tv_token}, household_id: {household_id}, wassup: {cookies.get('wassup')}", xbmc.LOGDEBUG)
        return tv_token, household_id, cookies.get("wassup")

    def _login(self, login: str, password: str) -> dict:
        """Login to Orange and return session cookie."""
        cookies = {}
        s = Session()

        try:
            res = request("GET", "https://login.orange.fr", s=s)
            cookies = res.cookies.get_dict()
        except RequestException:
            log("Error while authenticating (init)", xbmc.LOGWARNING)
            return {}

        try:
            res = request(
                "POST",
                "https://login.orange.fr/api/login",
                headers={
                    "Content-Type": "application/json",
                    "Cookie": to_cookie_string(cookies, ["xauth"]),
                },
                data=json.dumps({"login": login, "params": {}, "isSosh": False}),
                s=s,
            )
            cookies = res.cookies.get_dict()
        except RequestException:
            log("Error while authenticating (login)", xbmc.LOGWARNING)
            return {}

        try:
            res = request(
                "POST",
                "https://login.orange.fr/api/password",
                headers={
                    "Content-Type": "application/json",
                    "Cookie": to_cookie_string(cookies, ["xauth"]),
                },
                data=json.dumps({"password": password, "params": {}}),
                s=s,
            )
            cookies = res.cookies.get_dict()
        except RequestException:
            log("Error while authenticating (password)", xbmc.LOGWARNING)
            return {}

        return cookies

    def _extract_logo(self, logos: list, definition_type: str = "mobileAppliDark") -> str:
        for logo in logos:
            if logo["definitionType"] == definition_type:
                return _STREAM_LOGO_URL.format(path=logo["listLogos"][0]["path"])

        return None

    def _get_programs(self, start_day: int, days_to_display: int, chunks_per_day: int = 2, mco: str = "OFR") -> list:
        """Return the programs for today (default) or the specified period."""
        programs = []
        chunk_duration = 24 * 60 * 60 / chunks_per_day

        for chunk in range(0, days_to_display * chunks_per_day):
            period_start = (start_day + chunk_duration * chunk) * 1000
            period_end = (start_day + chunk_duration * (chunk + 1)) * 1000

            try:
                period = f"{int(period_start)},{int(period_end)}"
            except ValueError:
                period = "today"

            url = _PROGRAMS_ENDPOINT.format(period=period, mco=mco)
            programs.extend(request_json(url, default=[]))

        return programs
