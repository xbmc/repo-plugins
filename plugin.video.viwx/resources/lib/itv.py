# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------

import os
import logging

from datetime import datetime, timedelta
import pytz
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
        local_tz = pytz.timezone('Europe/London')
    btz = pytz.timezone('Europe/London')
    british_now = datetime.now(pytz.utc).astimezone(btz)

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
            brit_time = btz.localize(strptime(time_str, '%Y-%m-%dT%H:%M'))
            program['startTime'] = brit_time.astimezone(local_tz).strftime(time_format)
            program['orig_start'] = program['onAirTimeUTC'][:19]

    return schedule


stream_req_data = {
    'client': {
        'id': 'browser',
        'service': 'itv.x',
        'supportsAdPods': False,
        'version': '4.1'
    },
    'device': {
        'manufacturer': 'Firefox',
        'model': '110',
        'os': {
            'name': 'Linux',
            'type': 'desktop',
        }
    },
    'user': {
        'entitlements': [],
        'itvUserId': '',
        'token': ''
    },
    'variantAvailability': {
        'featureset': {
            'max': ['mpeg-dash', 'widevine', 'outband-webvtt', 'hd', 'single-track'],
            'min': ['mpeg-dash', 'widevine', 'outband-webvtt', 'hd', 'single-track']
        },
        'platformTag': 'dotcom',
        'player': 'dash'
    }
}


def _request_stream_data(url, stream_type='live'):
    from .itv_account import itv_session, fetch_authenticated
    session = itv_session()

    stream_req_data['user']['token'] = session.access_token
    stream_req_data['client']['supportsAdPods'] = stream_type != 'live'

    if stream_type == 'live':
        accept_type = 'application/vnd.itv.online.playlist.sim.v3+json'
        # Live MUST have a featureset containing an item without outband-webvtt, or a bad request is returned.
        min_features = ['mpeg-dash', 'widevine']
    else:
        accept_type = 'application/vnd.itv.vod.playlist.v2+json'
        # ITV appears now to use the min feature for catchup streams, causing subtitles
        # to go missing if not specified here. Min and max both specifying webvtt appears to
        # be no problem for catchup streams that don't have subtitles.
        min_features = ['mpeg-dash', 'widevine', 'outband-webvtt', 'hd', 'single-track']

    stream_req_data['variantAvailability']['featureset']['min'] = min_features

    stream_data = fetch_authenticated(
        fetch.post_json, url,
        data=stream_req_data,
        headers={'Accept': accept_type},
        cookies=session.cookie)

    return stream_data


def get_live_urls(url=None, title=None, start_time=None, play_from_start=False):
    """Return the urls to the dash stream, key service and subtitles for a particular live channel.

    .. note::
        Subtitles are usually embedded in live streams. Just return None in order to be compatible with
        data returned by get_catchup_urls(...).

    """
    channel = url.rsplit('/', 1)[1]

    stream_data = _request_stream_data(url)
    video_locations = stream_data['Playlist']['Video']['VideoLocations'][0]
    dash_url = video_locations['Url']
    start_again_url = video_locations.get('StartAgainUrl')

    if start_again_url:
        if start_time and (play_from_start or kodi_utils.ask_play_from_start(title)):
            dash_url = start_again_url.format(START_TIME=start_time)
            logger.debug('get_live_urls - selected play from start at %s', start_time)
        # Fast channels play only for about 5 minutes on the time shift stream
        elif not channel.startswith('FAST'):
            # Go 30 sec back to ensure we get the timeshift stream
            start_time = datetime.utcnow() - timedelta(seconds=30)
            dash_url = start_again_url.format(START_TIME=start_time.strftime('%Y-%m-%dT%H:%M:%S'))

    key_service = video_locations['KeyServiceUrl']
    return dash_url, key_service, None


def get_catchup_urls(episode_url):
    """Return the urls to the dash stream, key service and subtitles for a particular catchup
    episode and the type of video.

    """
    playlist = _request_stream_data(episode_url, 'catchup')['Playlist']
    stream_data = playlist['Video']
    url_base = stream_data['Base']
    video_locations = stream_data['MediaFiles'][0]
    dash_url = url_base + video_locations['Href']
    key_service = video_locations.get('KeyServiceUrl')
    try:
        # Usually stream_data['Subtitles'] is just None when subtitles are not available.
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
