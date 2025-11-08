"""
Top stories menu item and list
"""
import xbmc
from . import kodiutils, nhk_api, url
from .episode import Episode


def get_menu_item():
    """Returns the menu item for "Top stories"

    Returns:
        [Episode]: Menu item, or None if API call fails
    """

    # Getting top story
    api_result = url.get_json(nhk_api.rest_url["homepage_news"], False)
    
    if api_result is None or "data" not in api_result or not api_result["data"]:
        xbmc.log("topstories.get_menu_item: Failed to load top stories data", xbmc.LOGERROR)
        kodiutils.show_notification("NHK World TV", "Unable to load Top Stories news.")
        return None
    
    featured_news = api_result["data"][0]

    menu_item = Episode()

    if featured_news.get("thumbnails") is not None:
        thumbnails = featured_news["thumbnails"]
        menu_item.thumb = thumbnails.get("small", "")
        menu_item.fanart = thumbnails.get("middle", "")

    menu_item.title = kodiutils.get_string(30010)

    # Create the plot field
    menu_item.plot = kodiutils.get_string(30012).format(
        featured_news.get("title", ""), featured_news.get("description", "")
    )

    # Create the directory item
    menu_item.video_info = kodiutils.get_sd_video_info()

    return menu_item


def get_episodes(max_items, icon, fanart):
    """Get the list of "Top stories" episodes

    Args:
        max_items ([int]): Maximum amount of episodes to display
        icon (str): Default icon
        fanart (str): Default fanart

    Returns:
        [list]: List of Episodes, empty list if API call fails
    """

    api_result_json = url.get_json(nhk_api.rest_url["homepage_news"], False)
    
    if api_result_json is None or "data" not in api_result_json:
        xbmc.log("topstories.get_episodes: Failed to load top stories data", xbmc.LOGERROR)
        kodiutils.show_notification("NHK World TV", "Unable to load Top Stories episodes.")
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
        news_id = row.get("id", "")

        thumbnails = row.get("thumbnails")
        if thumbnails is None:
            # Featured news does not have a thumbnail
            episode.thumb = icon
            episode.fanart = fanart
        else:
            episode.thumb = thumbnails.get("small", "")
            episode.fanart = thumbnails.get("middle", "")
        episode.broadcast_start_date = row.get("updated_at")

        if row.get("videos") is not None:
            video = row["videos"]
            # Top stories that have a video attached to them
            episode.title = kodiutils.get_string(30063).format(title)
            episode.vod_id = news_id
            episode.duration = video.get("duration", 0)
            episode.plot_include_time_difference = True
            episode.plot = row.get("description", "")
            episode.video_info = kodiutils.get_sd_video_info()
            episode.is_playable = True
            
            video_config = video.get("config", "")
            if video_config:
                episode.url = url.get_nhk_website_url(video_config)
            else:
                xbmc.log(f"topstories.get_episodes: No video config for {news_id}", xbmc.LOGWARNING)
                continue
        else:
            # No video attached to it
            episode.title = title
            # Get detailed news information
            api_url = nhk_api.rest_url["news_detail"].format(news_id)
            news_detail_result = url.get_json(api_url)
            
            if news_detail_result is None or "data" not in news_detail_result:
                xbmc.log(f"topstories.get_episodes: Failed to get detail for news {news_id}", xbmc.LOGWARNING)
                # Still add the episode with basic info
                episode.plot = row.get("description", "")
                episode.is_playable = False
            else:
                news_detail_json = news_detail_result["data"]
                detail = news_detail_json.get("detail", "")
                detail = detail.replace("<br />", "\n")
                detail = detail.replace("\n\n", "\n")
                episode.plot_include_time_difference = True
                episode.plot = detail
                thumbnails = news_detail_json.get("thumbnails")
                if thumbnails is not None:
                    episode.thumb = thumbnails.get("small", "")
                    episode.fanart = thumbnails.get("middle", "")
                episode.is_playable = False
        episodes.append(episode)
    return episodes
