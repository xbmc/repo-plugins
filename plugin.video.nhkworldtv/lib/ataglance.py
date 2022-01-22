"""
At-a-glance episodes
"""
from . import kodiutils, nhk_api, url
from .episode import Episode

# At a glance menu item and list


def get_menu_item():
    """Returns the menu item for "At a glance"

   Returns:
        [Episode]: Menu item
    """

    menu_item = Episode()
    # Getting firststory
    featured_news = url.get_json(
        nhk_api.rest_url['get_news_ataglance'])['data'][0]
    thumbnails = featured_news['image']
    menu_item.thumb = thumbnails['list_sp']
    menu_item.fanart = thumbnails['main_pc']
    menu_item.title = kodiutils.get_string(30015)

    # Create the plot field
    menu_item.plot = kodiutils.get_string(30012).format(
        featured_news['title'], featured_news['description'])

    # Create the directory item

    menu_item.video_info = kodiutils.get_sd_video_info()
    return menu_item


def get_episodes(max_items):
    """ Get the list of "At a glance" episodes

    Args:
        max_items ([inr]): Maximum amount of episodes to display


    Returns:
        [list]: List of Episodes
    """

    api_result_json = url.get_json(nhk_api.rest_url['get_news_ataglance'])
    max_row_count = max_items
    result_row_count = len(api_result_json['data'])
    row_count = 0
    episodes = []

    # Only display MAX ROWS
    if result_row_count < max_row_count:
        max_row_count = result_row_count

    for row_count in range(0, max_row_count):
        row = api_result_json['data'][row_count]

        episode = Episode()
        title = row['title']
        thumbnails = row['image']
        if thumbnails['list_sp'] is not None:
            episode.thumb = thumbnails['list_sp']
        else:
            episode.thumb = thumbnails['list_pc']
        episode.fanart = thumbnails['main_pc']

        episode.broadcast_start_date = row['posted_at']
        episode.title = title
        vod_id = row['id']
        episode.vod_id = vod_id
        episode.duration = row['video']['duration']
        episode.plot_include_time_difference = True
        episode.plot = row['description']

        episode.video_info = kodiutils.get_sd_video_info()
        episode.is_playable = True
        episode.url = url.get_nhk_website_url(row['video']['config'])
        episodes.append(episode)
    return episodes
