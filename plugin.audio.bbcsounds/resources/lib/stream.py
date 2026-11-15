# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

from __future__ import annotations
import re
import json

import xbmc
import xbmcgui
from typing import TYPE_CHECKING

from resources.lib import fetch
from resources.lib import route
from resources.lib.exceptions import AccountError
from resources.lib.log import log

if TYPE_CHECKING:
    from resources.lib.plugin import Plugin
    from resources.lib import prog_mon


MEDIA_SELECTOR_URL = ('https://open.live.bbc.co.uk/mediaselector/6/select/version/3.0/'
                      'mediaset/pc/cvid/urn:bbc:pips:pid:{}/format/json/cors/1')


@route.resolve
def play_od(plugin: Plugin, service_id: str, pid: str) -> xbmcgui.ListItem | None:
    """Play an on-demand stream"""
    log('play on demand: service_id = "%s".', service_id)
    strm_url = select_stream_url(service_id)
    if not strm_url:
        return None
    li = create_listitem(strm_url)

    resume_info = xbmc.getInfoLabel('ListItem.Property(resume_point)')
    if resume_info and not plugin.is_resuming:
        # Create a resume dialog similar to the one displayed when playing a video.
        resume_time, total_time = resume_info.split(';')
        hours, seconds = divmod(int(resume_time), 3600)
        minutes, seconds = divmod(int(seconds), 60)
        ctx_items = [
            xbmc.getLocalizedString(12022).format(f'{hours:02d}:{minutes:02d}:{seconds:02d}'),
            xbmc.getLocalizedString(12021)
        ]
        result = xbmcgui.Dialog().contextmenu(ctx_items)
        if result == -1:
            return None
        if result == 0:
            li.getVideoInfoTag().setResumePoint(int(resume_time), int(total_time))
    if plugin.settings.getBool('is-signed-in'):
        from resources.lib import prog_mon

        plugin.register_delayed(prog_mon.start_progress_monitor,
                                report_progress,
                                callb_kwargs={'version_pid': service_id, 'pid': pid},
                                video_url=strm_url,
                                heartbeat_interval=30)
    return li


@route.resolve
def play_live(plugin: Plugin, service_id: str, start_t: str = '') -> xbmcgui.ListItem | None:
    """Play a live stream

    Play from the start time if `start_t` is provided.

    """
    log('play_live: service_id = "%s".', service_id)
    jwt = get_jwt('https://www.bbc.co.uk/sounds/play/live/' + service_id)
    strm_type = 'hls' if plugin.kodi_version > (21, 90) else 'dash'
    strm_url = select_stream_url(service_id, jwt, strm_type)
    if not strm_url:
        return None
    li = create_listitem(strm_url, strm_type)
    if start_t:
        resume_time = resume_point(start_t)
        log("Resuming live at %s seconds from the start of the timeshift buffer", resume_time)
        li.getVideoInfoTag().setResumePoint(resume_time, 14400)
        li.setProperty('inputstream.adaptive.play_timeshift_buffer', 'true')
    xbmc.PlayList(xbmc.PLAYLIST_MUSIC).clear()
    return li


def get_jwt(url: str) -> str | None:
    """Get the JWT required for live streams."""
    resp = fetch.get(url)
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', resp.text, re.DOTALL)
    if not match:
        return None
    json_data = json.loads(match[1])
    tkn = json_data['props']['pageProps'].get('jwtToken')
    return tkn


def select_stream_url(media_id: str,
                      jwt: str | None = None,
                      strm_type: str = 'dash') -> str | None:
    url = MEDIA_SELECTOR_URL.format(media_id)
    if jwt:
        headers = {'authorization': 'Bearer ' + jwt}
    else:
        headers = None
    resp = fetch.get(url, headers=headers)
    streams_data = json.loads(resp.content)
    selected_media_set = {}
    highest_bitrate = 0
    # captions_url = None

    for media_set in streams_data['media']:
        # Note: some streams include non-audio streams like captions.
        kind = media_set.get('kind')
        if kind == 'audio':
            if media_set.get('bitrate', 0) > highest_bitrate:
                selected_media_set = media_set
                highest_bitrate = media_set['bitrate']
        # Currently, Kodi doesn't seem able to do anything with captions on audio streams
        # elif kind == 'captions' and media_set.get('presentation_type') == 'static':
        #     for connection in media_set['connection']:
        #         if connection['protocol'] == 'https' and connection['transferFormat'] == 'plain':
        #             captions_url = connection['href']
        #             break

    for connection in selected_media_set['connection']:
        if connection['protocol'] == 'https' and connection['transferFormat'] == strm_type:
            return connection['href']
    return None


def create_listitem(url: str, strm_type: str = 'dash') -> xbmcgui.ListItem:
    li = xbmcgui.ListItem(path=url, offscreen=True)
    li.setProperty("IsPlayable", "true")
    li.setProperty('inputstream', 'inputstream.adaptive')
    if strm_type == 'hls':
        li.setMimeType('application/vnd.apple.mpegurl')
    else:
        li.setMimeType('application/dash+xml')
    li.setContentLookup(False)
    return li


def resume_point(start_time: str) -> int:
    """Calculate the stream resume point from the programme's start time.

    :param start_time: The UTC start time of the programme in iso format.

    """
    from datetime import datetime, timezone

    start_utc = datetime.fromisoformat(start_time)
    utc_now = datetime.now(timezone.utc)
    skip_time = int((utc_now - start_utc).total_seconds())
    # Live radio has a timeshift buffer of 4 hours.
    return max(0, 14400 - skip_time)


def report_progress(evt: prog_mon.ProgressEvent, version_pid: str, pid: str) -> bool:
    """Report the current play position of a playing stream to the BBC."""
    action = {'initialize': 'started',
              'heartbeat': 'heartbeat',
              'stopped': 'paused'}.get(evt.evt_type)

    post_data = {
        'action': action,
        'play_mode': 'ondemand',
        'pid': pid,
        'version_pid': version_pid,
        'elapsed_time': max(0, int(evt.play_time)),
        'resource_type': 'episode'
    }

    try:
        resp = fetch.post('https://rms.api.bbc.co.uk/v2/my/programmes/plays', json=post_data)
    except AccountError:
        log("Abort progress monitoring; user is not signed in.")
        return False

    status = resp.status_code
    if status != 202:
        log('stream.report_progress: Unexpeced status code: "%s"', status)
    return 200 <= resp.status_code < 300
