"""
At-a-glance episodes
"""
import xbmc
from . import kodiutils, nhk_api, url
from .episode import Episode

# At a glance menu item and list


def get_menu_item():
    """Returns the menu item for "At a glance"

    Returns:
         [Episode]: Menu item, or None if API call fails
    """

    menu_item = Episode()
    # Getting the first story
    api_result = url.get_json(nhk_api.rest_url["get_news_ataglance"])
    
    if api_result is None or "data" not in api_result or not api_result["data"]:
        xbmc.log("ataglance.get_menu_item: Failed to load at-a-glance data", xbmc.LOGERROR)
        kodiutils.show_notification("NHK World TV", "Unable to load At a Glance news.")
        return None
    
    featured_news = api_result["data"][0]
    thumbnails = featured_news.get("image", {})
    menu_item.thumb = thumbnails.get("list_pc", "")
    menu_item.fanart = thumbnails.get("main_pc", "")
    menu_item.title = kodiutils.get_string(30015)

    # Create the plot field
    menu_item.plot = kodiutils.get_string(30012).format(
        featured_news.get("title", ""), featured_news.get("description", "")
    )

    # Create the directory item

    menu_item.video_info = kodiutils.get_sd_video_info()
    return menu_item


def get_episodes(max_items):
    """Get the list of "At a glance" episodes

    Args:
        max_items ([int]): Maximum amount of episodes to display


    Returns:
        [list]: List of Episodes, empty list if API call fails
    """

    api_result_json = url.get_json(nhk_api.rest_url["get_news_ataglance"])
    
    if api_result_json is None or "data" not in api_result_json:
        xbmc.log("ataglance.get_episodes: Failed to load at-a-glance data", xbmc.LOGERROR)
        kodiutils.show_notification("NHK World TV", "Unable to load At a Glance episodes.")
        return []
    
    max_row_count = max_items
    result_row_count = len(api_result_json["data"])
    episodes = []

    # Only display MAX ROWS
    if result_row_count < max_row_count:
        max_row_count = result_row_count

    for row_count in range(0, max_row_count):
        row = api_result_json["data"][row_count]

        episode = Episode()
        title = row.get("title", "")
        thumbnails = row.get("image", {})
        if thumbnails.get("list_sp") is not None:
            episode.thumb = thumbnails.get("list_sp", "")
        else:
            episode.thumb = thumbnails.get("list_pc", "")
        episode.fanart = thumbnails.get("main_pc", "")

        episode.broadcast_start_date = row.get("posted_at")
        episode.title = title
        vod_id = row.get("id", "")
        episode.vod_id = vod_id
        
        video_info = row.get("video", {})
        episode.duration = video_info.get("duration", 0)
        episode.plot_include_time_difference = True
        episode.plot = row.get("description", "")

        episode.video_info = kodiutils.get_sd_video_info()
        episode.is_playable = True
        
        video_config = video_info.get("config", "")
        if video_config:
            episode.url = url.get_nhk_website_url(video_config)
        else:
            xbmc.log(f"ataglance.get_episodes: No video config for item {vod_id}", xbmc.LOGWARNING)
            continue
            
        episodes.append(episode)
    return episodes
