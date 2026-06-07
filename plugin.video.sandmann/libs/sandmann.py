# -*- coding: utf-8 -*-
# Copyright 2022 sorax
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import json
import sys

from bs4 import BeautifulSoup
from requests.exceptions import RequestException

from libs.network import fetchHtml
from libs.network import fetchJson


# -- Addon --
addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
addon_name = addon.getAddonInfo("name")
addon_icon = addon.getAddonInfo("icon")

base_path = sys.argv[0]


# -- Settings --
dgs = addon.getSettingInt("dgs2")
interval = addon.getSettingInt("interval2")
quality = addon.getSettingInt("quality2")
update = addon.getSettingInt("update2")
source = addon.getSettingInt("source2")


def sandmann():
    li_refresh = xbmcgui.ListItem(label=addon.getLocalizedString(30020))
    xbmcplugin.addDirectoryItem(addon_handle, base_path, li_refresh, True)

    try:
        html = fetchWebsite()
    except RequestException as e:
        xbmc.log(f"[{addon_name}] Failed to fetch website: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification(
            addon_name, addon.getLocalizedString(30200), xbmcgui.NOTIFICATION_ERROR
        )
        xbmcplugin.endOfDirectory(addon_handle)
        return

    if dgs == 0:
        episodes = getEpisodes(html, 1)
    elif dgs == 2:
        episodes = getEpisodes(html, 2)
    else:
        episodes = getEpisodes(html, 1) + getEpisodes(html, 2)

    item_list = []
    for episode, description in episodes:
        try:
            path = getEpisodePath(episode)
            details = fetchEpisodeDetails(path)
            item_list.append((details["stream"], getListItem(details, description), False))
        except (RequestException, KeyError, IndexError, TypeError, ValueError,
                json.JSONDecodeError) as e:
            xbmc.log(f"[{addon_name}] Skipping episode: {e}", xbmc.LOGWARNING)
            continue

    if not item_list:
        xbmcgui.Dialog().notification(
            addon_name, addon.getLocalizedString(30201), xbmcgui.NOTIFICATION_WARNING
        )

    xbmcplugin.addDirectoryItems(addon_handle, item_list, len(item_list))
    xbmcplugin.endOfDirectory(addon_handle)


def fetchWebsite():
    url = "https://www.sandmann.de/videos/"
    html = fetchHtml(url)

    return html


def getEpisodes(html, count):
    soup = BeautifulSoup(html, "html.parser")
    episodes = soup.select(f"#main > .count{count} .manualteaserpicture")
    html_descriptions = soup.select(f"#main > .count{count} .manualteasershorttext p")
    descriptions = [p.get_text() for p in html_descriptions]

    if not episodes:
        xbmc.log(f"[{addon_name}] No episodes found for count{count}", xbmc.LOGWARNING)
        return []

    if len(episodes) != len(descriptions):
        xbmc.log(
            f"[{addon_name}] Episode/description count mismatch: "
            f"{len(episodes)} episodes vs {len(descriptions)} descriptions",
            xbmc.LOGWARNING,
        )
        descriptions.extend([""] * (len(episodes) - len(descriptions)))

    return list(zip(episodes, descriptions))


def getEpisodePath(episode):
    jsb_string = episode.get("data-jsb")
    if not jsb_string:
        raise ValueError("Missing 'data-jsb' attribute on episode element")

    jsb_object = json.loads(jsb_string)

    if "media" not in jsb_object:
        raise KeyError("Missing 'media' key in episode JSON data")

    return jsb_object["media"]


def fetchEpisodeDetails(path):
    data = fetchJson(f"https://www.sandmann.de{path}")

    media_array = data.get("_mediaArray")
    if not media_array or not media_array[0].get("_mediaStreamArray"):
        raise KeyError("Missing media stream data in API response")

    streams = {}
    for stream in media_array[0]["_mediaStreamArray"]:
        quality = stream.get("_quality")
        url = stream.get("_stream")
        if quality is not None and url:
            streams[quality] = url

    if "auto" not in streams:
        raise KeyError("No 'auto' quality stream available")

    title_parts = data.get("rbbtitle", "").split(" | ")
    date = title_parts[2] if len(title_parts) > 2 else ""
    name = title_parts[0] if title_parts else ""
    title = f"{date} | {name}" if date and name else data.get("rbbtitle", "Unbekannt")

    preview_image = data.get("_previewImage", "")
    if preview_image:
        preview_image = "https://www.sandmann.de" + preview_image.rsplit("/", 1)[0]

    return {
        "date": date,
        "duration": data.get("_duration", 0),
        "fanart": f"{preview_image}/size=1920x1080.jpg" if preview_image else "",
        "stream": streams["auto"],
        "thumb": f"{preview_image}/size=640x360.jpg" if preview_image else "",
        "title": title,
    }


def getListItem(item, description):
    li = xbmcgui.ListItem()
    li.setLabel(item["title"])
    li.setArt({
        "fanart": item["fanart"],
        "thumb": item["thumb"]
    })
    li.setInfo(
        type="video",
        infoLabels={
            "aired": item["date"],
            "duration": item["duration"],
            "plot": description,
        }
    )
    li.setProperty("IsPlayable", "true")

    return li
