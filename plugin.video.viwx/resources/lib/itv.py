# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------

import os
import logging

from datetime import datetime, timedelta, timezone
import xbmc

from codequick import Script
from codequick.support import logger_id

from . import utils
from . import fetch
from . import kodi_utils


logger = logging.getLogger(logger_id + '.itv')


def get_live_schedule(hours=4, local_tz=None):
    """Get the schedule of the live channels from now up to the specified number of hours.

    """
    if local_tz is None:
        local_tz = utils.ZoneInfo('Europe/London')
    btz = utils.ZoneInfo('Europe/London')
    british_now = datetime.now(timezone.utc).astimezone(btz)

    # Request TV schedules for the specified number of hours from now, in british time
    from_date = british_now.strftime('%Y%m%d%H%M')
    to_date = (british_now + timedelta(hours=hours)).strftime('%Y%m%d%H%M')
    # Note: platformTag=ctv is exactly what a webbrowser sends
    url = 'https://scheduled.oasvc.itv.com/scheduled/itvonline/schedules?from={}&platformTag=ctv&to={}'.format(
        from_date, to_date)
    data = fetch.get_json(url)
    schedules_list = data.get('_embedded', {}).get('schedule', [])
    schedule = [element['_embedded'] for element in schedules_list]

    # Convert British start time to local time and format in the user's regional format
    # Use local time format without seconds. Fix weird kodi formatting for 12-hour clock.
    time_format = xbmc.getRegion('time').replace(':%S', '').replace('%I%I:', '%I:')
    strptime = utils.strptime
    for channel in schedule:
        for program in channel['slot']:
            time_str = program['startTime'][:16]
            brit_time = (strptime(time_str, '%Y-%m-%dT%H:%M')).replace(tzinfo=btz)
            program['startTime'] = brit_time.astimezone(local_tz).strftime(time_format)
            program['orig_start'] = program['onAirTimeUTC'][:19]

    return schedule


def get_live_urls(url=None, title=None, start_time=None, play_from_start=False, full_hd=False):
    """Return the urls to the dash stream, key service and subtitles for a particular live channel.

    .. note::
        Subtitles are usually embedded in live streams. Just return None in order to be compatible with
        data returned by get_catchup_urls(...).

    """
    # import web_pdb; web_pdb.set_trace()
    from . import itvx

    stream_data = itvx._request_stream_data(url, full_hd=full_hd)
    video_locations = stream_data['Playlist']['Video']['VideoLocations'][0]
    dash_url = video_locations['Url']
    start_again_url = video_locations.get('StartAgainUrl')

    if start_again_url:
        if start_time and (play_from_start or kodi_utils.ask_play_from_start(title)):
            dash_url = start_again_url.format(START_TIME=start_time)
            logger.debug('get_live_urls - selected play from start at %s', start_time)
        else:
            # Go 1 hour back to ensure we get the timeshift stream with adverts embedded
            # and can skip back a bit in the stream. Some FAST channels that do have a large
            # enough buffer automatically use the maximum available time shift for that channel.
            start_time = datetime.now(timezone.utc) - timedelta(seconds=3600)
            dash_url = start_again_url.format(START_TIME=start_time.strftime('%Y-%m-%dT%H:%M:%S'))
    dash_url = dash_url.replace('ctv-low', 'ctv', 1)
    key_service = video_locations['KeyServiceUrl']
    return dash_url, key_service, None


def get_catchup_urls(episode_url, full_hd=False):
    """Return the urls to the dash stream, key service and subtitles for a particular catchup
    episode and the type of video.

    """
    from resources.lib import itvx
    playlist = itvx._request_stream_data(episode_url, 'catchup', full_hd)['Playlist']
    stream_data = playlist['Video']

    # Select the media with the highest resolution
    highest_resolution = 0
    video_locations = None
    for media in stream_data['MediaFiles']:
        res = int(media.get('Resolution', 0))
        if res > highest_resolution:
            video_locations = media
            highest_resolution = res
    if video_locations is None:
        # Some items, in particular short news clip, may still have the old format of media files.
        video_locations = stream_data['MediaFiles'][0]

    dash_url = video_locations['Href']
    key_service = video_locations.get('KeyServiceUrl')
    try:
        # Usually stream_data['Subtitles'] is just None when subtitles are not available,
        # but on shortform items it's completely absent.
        subtitles = stream_data['Subtitles'][0]['Href']
    except (TypeError, KeyError, IndexError):
        subtitles = None
    return dash_url, key_service, subtitles, playlist['VideoType'], playlist['ProductionId']


def get_vtt_subtitles(subtitles_url):
    """Return a tuple with the file paths to rst subtitles files. The tuple usually
    has only a single element, but could contain more.

    Return None if subtitles_url does not point to a valid Web-vvt subtitle file or
    subtitles are not te be shown by user setting.

    """
    show_subtitles = Script.setting['subtitles_show'] == 'true'
    if show_subtitles is False:
        logger.info('Ignored subtitles by entry in settings')
        return None

    if not subtitles_url:
        logger.info('No subtitles available for this stream')
        return None

    # noinspection PyBroadException
    try:
        vtt_doc = fetch.get_document(subtitles_url)

        # vtt_file = os.path.join(utils.addon_info.profile, 'subtitles.vtt')
        # with open(vtt_file, 'w', encoding='utf8') as f:
        #     f.write(vtt_doc)

        srt_doc = utils.vtt_to_srt(vtt_doc, colourize=Script.setting['subtitles_color'] != 'false')
        srt_file = os.path.join(utils.addon_info.profile, 'hearing impaired.en.srt')
        with open(srt_file, 'w', encoding='utf8') as f:
            f.write(srt_doc)

        return (srt_file, )
    except:
        logger.error("Failed to get vtt subtitles from url %s", subtitles_url, exc_info=True)
        return None
