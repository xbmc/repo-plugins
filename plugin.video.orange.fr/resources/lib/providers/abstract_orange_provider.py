# ruff: noqa: D102
"""Orange provider template."""

import json
import re
from abc import ABC
from datetime import date, datetime, timedelta
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import xbmc

from lib.providers.abstract_provider import AbstractProvider
from lib.utils.kodi import build_addon_url, get_drm, get_global_setting, log
from lib.utils.request import build_request, get_random_ua, open_request

_PROGRAMS_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/live/v3/applications/STB4PC/programs?period={period}&epgIds=all&mco={mco}"
_CATCHUP_CHANNELS_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/catchup/v4/applications/PC/channels"
_CATCHUP_ARTICLES_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/catchup/v4/applications/PC/channels/{catchup_channel_id}/categories/{category_id}"
_CATCHUP_VIDEOS_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/catchup/v4/applications/PC/groups/{group_id}"
_CHANNELS_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/pds/v1/live/ew?everywherePopulation=OTT_Metro"
_STREAM_ENDPOINT = "https://mediation-tv.orange.fr/all/api-gw/{stream_type}/{version}/auth/accountToken/applications/PC/{item_type}/{stream_id}/stream?terminalModel=WEB_PC"

_STREAM_LOGO_URL = "https://proxymedia.woopic.com/api/v1/images/2090{path}"
_LIVE_HOMEPAGE_URL = "https://chaines-tv.orange.fr/"
_CATCHUP_VIDEO_URL = "https://replay.orange.fr/videos/{stream_id}"


class AbstractOrangeProvider(AbstractProvider, ABC):
    """Abstract Orange Provider."""

    chunks_per_day = 2
    mco = "OFR"
    groups = {}

    def get_live_stream_info(self, stream_id: str) -> dict:
        return self._get_stream_info("live", "v3", "channels", stream_id)

    def get_catchup_stream_info(self, stream_id: str) -> dict:
        return self._get_stream_info("catchup", "v4", "videos", stream_id)

    def get_streams(self) -> list:
        """Load stream data from Orange and convert it to JSON-STREAMS format."""
        req = build_request(_CHANNELS_ENDPOINT)
        channels = dict(open_request(req, {"channels": {}}))["channels"]

        log(f"{len(channels)} channels found", xbmc.LOGINFO)
        channels.sort(key=lambda channel: channel["displayOrder"])

        return [
            {
                "id": str(channel["idEPG"]),
                "name": channel["name"],
                "preset": str(channel["displayOrder"]),
                "logo": self._extract_logo(channel["logos"]),
                "stream": build_addon_url(f"/live-streams/{channel['idEPG']}"),
                "group": [group_name for group_name in self.groups if int(channel["idEPG"]) in self.groups[group_name]],
            }
            for channel in channels
        ]

    def get_epg(self) -> dict:
        """Load EPG data from Orange and convert it to JSON-EPG format."""
        start_day = datetime.timestamp(
            datetime.combine(
                date.today() - timedelta(days=int(get_global_setting("epg.pastdaystodisplay"))), datetime.min.time()
            )
        )

        days_to_display = int(get_global_setting("epg.futuredaystodisplay")) + int(
            get_global_setting("epg.pastdaystodisplay")
        )

        programs = self._get_programs(start_day, days_to_display, self.chunks_per_day, self.mco)
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

    def get_catchup_channels(self) -> list:
        """Load available catchup channels."""
        req = build_request(_CATCHUP_CHANNELS_ENDPOINT)
        channels = open_request(req, [])

        log(f"{len(channels)} catchup channels found", xbmc.LOGINFO)

        return [
            {
                "label": str(channel["name"]).upper(),
                "path": build_addon_url(f"/channels/{channel['id']}/categories"),
                "art": {"thumb": channel["logos"]["ref_millenials_partner_white_logo"]},
            }
            for channel in channels
        ]

    def get_catchup_categories(self, catchup_channel_id: str) -> list:
        """Return a list of catchup categories for the specified channel id."""
        req = build_request(_CATCHUP_CHANNELS_ENDPOINT + "/" + catchup_channel_id)
        categories = dict(open_request(req, {"categories": {}}))["categories"]

        return [
            {
                "label": category["name"][0].upper() + category["name"][1:],
                "path": build_addon_url(f"/channels/{catchup_channel_id}/categories/{category['id']}/articles"),
            }
            for category in categories
        ]

    def get_catchup_articles(self, catchup_channel_id: str, category_id: str) -> list:
        """Return a list of catchup groups for the specified channel id and category id."""
        url = _CATCHUP_ARTICLES_ENDPOINT.format(catchup_channel_id=catchup_channel_id, category_id=category_id)
        req = build_request(url)

        articles = dict(open_request(req, {"articles": {}}))["articles"]

        return [
            {
                "label": article["title"],
                "path": build_addon_url(f"/channels/{catchup_channel_id}/articles/{article['id']}/videos"),
                "art": {"poster": article["covers"]["ref_16_9"]},
            }
            for article in articles
        ]

    def get_catchup_videos(self, catchup_channel_id: str, article_id: str) -> list:
        """Return a list of catchup videos for the specified channel id and article id."""
        req = build_request(_CATCHUP_VIDEOS_ENDPOINT.format(group_id=article_id))
        videos = dict(open_request(req, {"videos": {}}))["videos"]

        return [
            {
                "label": video["title"],
                "path": build_addon_url(f"/catchup-streams/{video['id']}"),
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

    def _get_stream_info(self, stream_type: str, version: str, item_type: str, stream_id: str) -> dict:
        """Load stream info from Orange."""
        auth_url = _LIVE_HOMEPAGE_URL if stream_type == "live" else _CATCHUP_VIDEO_URL.format(stream_id=stream_id)
        url = _STREAM_ENDPOINT.format(
            stream_type=stream_type,
            version=version,
            item_type=item_type,
            stream_id=stream_id,
        )
        req, tv_token = self._build_auth_request(url, auth_url=auth_url)

        try:
            with urlopen(req) as res:
                stream_info = json.loads(res.read())
        except HTTPError as error:
            log(error, xbmc.LOGERROR)
            if error.code == 403 or error.code == 401:
                return False

        drm = get_drm()
        protectionData = (
            stream_info.get("protectionData", None)
            if stream_info.get("protectionData", None) is not None
            else stream_info.get("protectionDatas")
        )
        license_server_url = None

        for system in protectionData:
            if system.get("keySystem") == drm.value:
                license_server_url = system.get("laUrl")

        headers = (
            f"User-Agent={get_random_ua()}"
            + f"&Host={urlparse(url).netloc}"
            + f"&tv_token=Bearer {tv_token}"
            + "&Content-Type="
        )
        post_data = "R{SSM}"
        response = ""

        stream_info = {
            "path": stream_info["url"],
            "mime_type": "application/xml+dash",
            "manifest_type": "mpd",
            "license_type": drm.value,
            "license_key": f"{license_server_url}|{headers}|{post_data}|{response}",
        }

        log(stream_info, xbmc.LOGDEBUG)
        return stream_info

    def _build_auth_request(self, url: str, additional_headers: dict = None, auth_url: str = None) -> (Request, str):
        """Build HTTP request."""
        tv_token = None

        if additional_headers is None:
            additional_headers = {}

        if auth_url is not None:
            req = build_request(auth_url, {"User-Agent": get_random_ua()})

            with urlopen(req) as res:
                html = res.read().decode("utf-8")

            tv_token = re.search('instanceInfo:{token:"([a-zA-Z0-9-_.]+)"', html).group(1)
            household_id = re.search('householdId:"([A-Z0-9]+)"', html).group(1)

            additional_headers["tv_token"] = f"Bearer {tv_token}"
            additional_headers["User-Agent"] = get_random_ua()

            url += f"&terminalId=Windows10-x64-Firefox-{household_id}"

        return build_request(url, additional_headers), tv_token

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
            req = build_request(url)
            log(f"Fetching: {url}", xbmc.LOGINFO)

            with urlopen(req) as res:
                programs.extend(json.loads(res.read()))

        return programs
