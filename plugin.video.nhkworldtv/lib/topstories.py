from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from . import kodiutils, nhk_api, url
from .episode import Episode

# Top stories menu item and list


def get_menu_item():
    """Returns the menu item for "Top stories"

    Returns:
        [Episode]: Menu item
    """

    # Getting top story
    featured_news = url.get_json(nhk_api.rest_url['homepage_news'],
                                 False)['data'][0]
    thumbnails = featured_news['thumbnails']

    menu_item = Episode()

    menu_item.thumb = thumbnails['small']
    menu_item.fanart = thumbnails['middle']

    menu_item.title = kodiutils.get_string(30010)

    # Create the plot field
    menu_item.plot = kodiutils.get_string(30012).format(
        featured_news['title'], featured_news['description'])

    # Create the directory item
    menu_item.video_info = kodiutils.get_SD_video_info()

    return menu_item


def get_episodes(max_items, icon, fanart):
    """ Get the list of "Top stories" episodes

    Args:
        max_items ([inr]): Maximum amount of episodes to display

    Returns:
        [list]: List of Episodes
    """

    api_result_json = url.get_json(nhk_api.rest_url['homepage_news'], False)
    max_row_count = max_items
    result_row_count = len(api_result_json['data'])
    row_count = 0
    episodes = []
    # Only display MAX ROWS
    if (result_row_count < max_row_count):
        max_row_count = result_row_count

    for row_count in range(0, max_row_count):
        row = api_result_json['data'][row_count]

        episode = Episode()
        title = row['title']
        news_id = row['id']

        thumbnails = row['thumbnails']
        if (thumbnails is None):
            # Featured news does not have a thumbnail
            episode.thumb = icon
            episode.fanart = fanart
        else:
            episode.thumb = thumbnails['small']
            episode.fanart = thumbnails['middle']
        episode.broadcast_start_date = row['updated_at']

        if row['videos'] is not None:
            video = row['videos']
            # Top stories that have a video attached to them
            episode.title = kodiutils.get_string(30063).format(title)
            episode.vod_id = news_id
            episode.duration = video['duration']
            episode.plot_include_time_difference = True
            episode.plot = row['description']
            episode.video_info = kodiutils.get_SD_video_info()
            episode.IsPlayable = True
            episode.url = url.get_NHK_website_url(video['config'])
            episodes.append(episode)
        else:
            # No video attached to it
            episode.title = title
            # Get detailed news information
            api_url = nhk_api.rest_url['news_detail'].format(news_id)
            news_detail_json = url.get_json(api_url)['data']
            detail = news_detail_json['detail']
            detail = detail.replace('<br />', '\n')
            detail = detail.replace('\n\n', '\n')
            episode.plot_include_time_difference = True
            episode.plot = detail
            thumbnails = news_detail_json['thumbnails']
            if (thumbnails is not None):
                episode.thumb = thumbnails['small']
                episode.fanart = thumbnails['middle']
            episode.IsPlayable = False
            episodes.append((episode))
    return (episodes)
