"""."""

import codecs
import json
import re
from datetime import date, datetime, timedelta
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import xbmc

from lib.utils.request import get_random_ua, install_proxy
from lib.utils.xbmctools import get_drm, get_global_setting, log

_EPG_ENDPOINT = "https://rp-ott-mediation-tv.woopic.com/api-gw/live/v3/applications/STB4PC/programs?period={period}&epgIds=all&mco={mco}"
_STREAM_INFO_ENDPOINT = "https://mediation-tv.orange.fr/all/api-gw/live/v3/auth/accountToken/applications/PC/channels/{channel_id}/stream?terminalModel=WEB_PC"
_STREAM_LOGO_ENDPOINT = "https://proxymedia.woopic.com/api/v1/images/2090%2Flogos%2Fv2%2Flogos%2F{external_id}%2F{hash}%2F{type}%2Flogo_{width}x{height}.png"

_HOMEPAGE_ENDPOINTS = [
    "https://chaines-tv.orange.fr/",
    "https://chaines-tv.orange.fr/ce-soir?filtres=all",
    "https://chaines-tv.orange.fr/programme-tv?filtres=all",
]

_EXTERNAL_ID_MAP = {
    "canalplus": "canal_plus",
    "lcp": "lcp_ps",
    "france4": "france_4",
    "itelevision": "cnews",
    "directstar": "cstar",
    "lcimobile": "lci",
    "tcm": "tcmcinema",
    # livetv_canal_sport
    "gameone": "game_one",
    "chasseetpeche": "chasse_peche",
    "toute_l_histoire": "toute_histoire",
    "ushuaia": "ushuaia_tv",
    "natgeo": "national_geographic",
    "planeteplus": "planete_plus",
    "m6_music": "m6music",
    "equidia": "equidia_live",
    "luxe": "luxe_tv",
    "deutschewelle": "deutsche_welle_english",
    "france3corsevs": "f3_corse_via_stella",
    "rai_tre": "raitre",
}

_NO_PRESET_START = 1000


def get_stream_info(channel_id: str, mco: str = "OFR") -> dict:
    """Load stream info from Orange."""
    tv_token = _extract_tv_token()
    log(tv_token, xbmc.LOGINFO)

    url = _STREAM_INFO_ENDPOINT.format(channel_id=channel_id)
    req = _build_request(url, {"tv_token": f"Bearer {tv_token}"})

    try:
        with urlopen(req) as res:
            stream_info = json.loads(res.read())
    except HTTPError as error:
        if error.code == 403:
            return False

    drm = get_drm()
    license_server_url = None
    for system in stream_info.get("protectionData"):
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
        "drm": drm.name.lower(),
        "license_type": drm.value,
        "license_key": f"{license_server_url}|{headers}|{post_data}|{response}",
    }

    log(stream_info, xbmc.LOGDEBUG)
    return stream_info


def get_streams(groups: dict, external_id_map: dict, mco: str = "OFR") -> list:
    """Load stream data from Orange and convert it to JSON-STREAMS format."""
    channels = _discover_channels()
    channels = _load_channel_logos(channels)
    channels = _load_channel_presets(channels, mco)
    log(f"{len(channels)} channels found", xbmc.LOGINFO)

    channels_without_id = {
        external_id: channel for external_id, channel in list(channels.items()) if channel["id"] == ""
    }
    log(f"{len(channels_without_id)} channels without id", xbmc.LOGINFO)

    for external_id in channels_without_id:
        log(f" => {external_id}", xbmc.LOGDEBUG)

    return [
        {
            "id": channel["id"],
            "name": channel["name"],
            "preset": channel["preset"],
            "logo": channel.get("logo", None),
            "stream": "plugin://plugin.video.orange.fr/channels/{channel_id}".format(channel_id=channel["id"]),
            "group": [group_name for group_name in groups if int(channel["id"]) in groups[group_name]],
        }
        for channel in list(channels.values())
        if channel["id"] != "" and "preset" in channel
    ]


def get_epg(chunks_per_day: int = 2, mco: str = "OFR") -> dict:
    """Load EPG data from Orange and convert it to JSON-EPG format."""
    start_day = datetime.timestamp(
        datetime.combine(
            date.today() - timedelta(days=int(get_global_setting("epg.pastdaystodisplay"))), datetime.min.time()
        )
    )

    days_to_display = int(get_global_setting("epg.futuredaystodisplay")) + int(
        get_global_setting("epg.pastdaystodisplay")
    )

    programs = _get_programs(start_day, days_to_display, chunks_per_day, mco)
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


def _get_programs(start_day: int, days_to_display: int, chunks_per_day: int = 2, mco: str = "OFR") -> list:
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

        url = _EPG_ENDPOINT.format(period=period, mco=mco)
        req = _build_request(url)
        log(f"Fetching: {url}", xbmc.LOGINFO)

        with urlopen(req) as res:
            programs.extend(json.loads(res.read()))

    return programs


def _build_request(url: str, additional_headers: dict = None) -> Request:
    """Build request."""
    if additional_headers is None:
        additional_headers = {}

    install_proxy()

    return Request(url, headers={"User-Agent": get_random_ua(), "Host": urlparse(url).netloc, **additional_headers})


def _extract_tv_token() -> str:
    """Extract TV token."""
    req = _build_request(_HOMEPAGE_ENDPOINTS[0])

    with urlopen(req) as res:
        html = res.read().decode("utf-8")

    return re.search('instanceInfo:{token:"([a-zA-Z0-9-_.]+)"', html).group(1)


def _discover_channels() -> list:
    """Load available channels from homepages."""
    channels = {}

    pattern = '"([A-Z0-9+/\': ]*[A-Z][A-Z0-9+/\': ]*)","(livetv_[a-zA-Z0-9_]+)",([0-9]*)'

    for url in _HOMEPAGE_ENDPOINTS:
        req = _build_request(url)

        with urlopen(req) as res:
            html = codecs.decode(res.read().decode("utf-8"), "unicode-escape")

        matches = re.findall(pattern, html)

        for match in matches:
            channels[match[1]] = {"name": match[0], "id": match[2]}

    return channels


def _load_channel_logos(channels: dict, mco: str = "OFR") -> dict:
    """Load channel logos from homepage."""
    req = _build_request(_HOMEPAGE_ENDPOINTS[0])

    with urlopen(req) as res:
        html = codecs.decode(res.read().decode("utf-8"), "unicode-escape")

    matches = re.findall(
        'path:"%2Flogos%2Fv2%2Flogos%2F(livetv_[a-zA-Z0-9_]+)%2F([0-9]+_[0-9]+)%2FmobileAppliDark%2Flogo_([0-9]+)x([0-9]+)\.png"',
        html,
    )

    for match in matches:
        if match[0] not in channels:
            continue

        channels[match[0]]["logo"] = _STREAM_LOGO_ENDPOINT.format(
            external_id=match[0],
            hash=match[1],
            type="mobileAppliDark",
            width=match[2],
            height=match[3],
        )

    # Fill missing channel ids from EPG when possible
    req = _build_request(_EPG_ENDPOINT.format(period="today", mco=mco) + "&groupBy=channel")

    with urlopen(req) as res:
        programs_by_channel = json.loads(res.read())

    channel_ids = {
        programs[0]["externalId"]: programs[0]["channelId"] for programs in list(programs_by_channel.values())
    }

    for external_id in channels:
        epg_external_id = _get_external_id(external_id)

        if epg_external_id in channel_ids and channels[external_id]["id"] == "":
            log(f" => Fill missing channel id for {external_id}", xbmc.LOGDEBUG)
            channels[external_id]["id"] = channel_ids[epg_external_id]

    return channels


def _load_channel_presets(channels: dict, mco: str = "OFR") -> dict:
    """Load presets from EPG."""
    req = _build_request(_EPG_ENDPOINT.format(period="today", mco=mco) + "&groupBy=channel")

    with urlopen(req) as res:
        programs_by_channel = json.loads(res.read())

    preset = _NO_PRESET_START

    for external_id in channels:
        if channels[external_id]["id"] in programs_by_channel:
            program = programs_by_channel[channels[external_id]["id"]][0]
            channels[external_id]["preset"] = program["channelZappingNumber"]
        else:
            result = re.findall("90([0-9]+)", channels[external_id]["id"])

            if len(result) > 0:
                channels[external_id]["preset"] = result[0]
            else:
                channels[external_id]["preset"] = preset
                preset = preset + 1
                log(
                    "=> Force preset {preset} for {channel_name} ({channel_id})".format(
                        preset=preset,
                        channel_name=channels[external_id]["name"],
                        channel_id=channels[external_id]["id"],
                    ),
                    xbmc.LOGDEBUG,
                )

    return channels


def _get_external_id(stream_external_id: str) -> str:
    """Format original external id to EPG external id."""
    epg_external_id = stream_external_id.lower().replace("_umts", "").replace("livetv_", "")
    epg_external_id = "livetv_" + _EXTERNAL_ID_MAP.get(epg_external_id, epg_external_id) + "_ctv"
    log(f"{stream_external_id} => {epg_external_id}".format(stream_external_id, epg_external_id), xbmc.LOGDEBUG)
    return epg_external_id
