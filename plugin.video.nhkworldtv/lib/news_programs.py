from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from kodi_six import xbmc
import xml.etree.ElementTree as ET
from requests.models import HTTPError
from . import kodiutils, nhk_api, url, utils
from .episode import Episode


def get_programs():
    """ Get the list of news programs


    Returns:
        [list]: List of news programs
    """
    xbmc.log('Getting news programs from NHK')
    api_result_json = url.get_json(nhk_api.rest_url['news_program_config'],
                                   False)
    news_programs = api_result_json['config']['programs']
    row_count = 0
    episodes = []

    root = None

    for news_program in news_programs:
        row_count = row_count + 1
        news_program_xml = None
        news_program_id = news_program['id']
        api_url = nhk_api.rest_url['news_program_xml'].format(news_program_id)

        # Get the News Program URL from NHK - sometimes it doesn't exist
        # Errors will be ignored and the offending program will not be added
        # https://github.com/sbroenne/plugin.video.nhkworldtv/issues/9
        try:
            news_program_xml = url.get_url(api_url, False).text
        except HTTPError:
            xbmc.log('Could not load Program XML {0} from NHK Website'.format(
                news_program_id))
        else:
            # Sometimes the XML is invalid, add error handling
            try:
                root = ET.fromstring(news_program_xml)
            except ET.ParseError:
                xbmc.log(
                    'Could not parse Program XML {0}'.format(news_program_id))
            else:
                # Add program
                play_path = nhk_api.rest_url['news_programs_video_url'].format(
                    utils.get_news_program_play_path(
                        root.find('file.high').text))
                episode = Episode()
                vod_id = 'news_program_{0}'.format(news_program_id)
                episode.vod_id = vod_id

                # Extract the Title
                break_string = '<br />'
                description = root.find('description').text
                if (break_string in description):
                    lines = description.split(break_string, 1)
                    episode.title = lines[0]
                    # Extract the broadcast time and convert it to local time
                    date_string = lines[1].strip()
                    episode.broadcast_start_date = utils.get_timestamp_from_datestring(
                        (date_string))
                    episode.plot_include_time_difference = True
                else:
                    episode.title = description

                episode.plot = ''
                episode.fanart = news_program['image']
                episode.thumb = news_program['image']
                episode.duration = root.find('media.time').text
                episode.video_info = kodiutils.get_sd_video_info()
                episode.is_playable = True
                episodes.append((play_path, episode.kodi_list_item, False))

    return (episodes)
