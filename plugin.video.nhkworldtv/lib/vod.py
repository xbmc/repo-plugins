"""
Video-on-demand (VOD)
"""

import xbmc
import xbmcaddon

from . import kodiutils, nhk_api, url, utils
from .episode import Episode

ADDON = xbmcaddon.Addon()


def get_episode_list(api_method, episode_list_id, show_only_subtitle):
    """Video On Demand - Episode List

        Returns episode list based on the requested NHK API Method
        (e.g. Programs, Categories, etc.)

    Args:
        api_method ([str]): The NHK API method to use
        episode_list_id ([str]): ID to use (optional)
        show_only_subtitle ([int]): Only show subtitles (0 or 1)
    Returns:
        [list] -- List of episodes, empty list if API call fails
    """

    # Only format api_url when a non-0 value for id was provided
    # some APIs do not need an id
    if episode_list_id != "None":
        api_url = nhk_api.rest_url[api_method].format(episode_list_id)
    else:
        api_url = nhk_api.rest_url[api_method]

    # Get API result with null safety
    api_result = url.get_json(api_url)
    if api_result is None:
        xbmc.log("vod.get_episode_list: API call failed - no response", xbmc.LOGERROR)
        kodiutils.show_notification(
            "NHK World TV", "Unable to load episodes. Please try again later."
        )
        return []

    # API returns "items" array directly
    if "items" not in api_result:
        xbmc.log(
            "vod.get_episode_list: API response missing 'items'",
            xbmc.LOGERROR,
        )
        kodiutils.show_notification(
            "NHK World TV", "Unable to load episodes. Please try again later."
        )
        return []

    program_json = api_result["items"]

    episodes = []
    for row in program_json:
        episode = Episode()
        episode.is_playable = True
        title = row.get("title") or ""
        subtitle = row.get("subtitle") or ""

        # If episode has no title, try to use the parent program title
        if not title and not subtitle:
            video_program = row.get("video_program", {})
            program_title = video_program.get("title", "") if video_program else ""
            if program_title:
                title = program_title
                xbmc.log(
                    f"vod.get_episode_list: Using program title for episode id={row.get('id', 'unknown')}",
                    xbmc.LOGDEBUG,
                )
            else:
                # No title, subtitle, or program title - skip this episode
                xbmc.log(
                    f"vod.get_episode_list: Skipping episode with no title/subtitle/program, id={row.get('id', 'unknown')}",
                    xbmc.LOGWARNING,
                )
                continue

        # Convert show_only_subtitle to int safely
        try:
            show_subtitle_only = int(show_only_subtitle) == 1
        except (ValueError, TypeError):
            show_subtitle_only = False

        if show_subtitle_only:
            # Show only subtitle
            if len(subtitle) > 0:
                # There is a subtitle, use it
                episode_name = subtitle
            else:
                # Use the title instead of the subtitle
                episode_name = title
        else:
            # Show complete title
            if len(title) == 0:
                # Use the subtitle as the episode name
                # because there is no title
                episode_name = subtitle
            else:
                # Use the full episode name
                episode_name = utils.get_episode_name(title, subtitle)

        episode.title = episode_name
        episode.plot = row.get("description", "")

        # Get images from new API structure
        images_obj = row.get("images", {})
        if isinstance(images_obj, dict):
            images = images_obj.get("landscape", [])
            if images:
                episode.thumb = images[0].get("url", "")
                episode.fanart = (
                    images[-1].get("url", "") if len(images) > 1 else episode.thumb
                )
            else:
                episode.thumb = ""
                episode.fanart = ""
        elif isinstance(images_obj, list) and images_obj:
            # Some endpoints return images as array directly
            episode.thumb = images_obj[0].get("url", "") if images_obj[0] else ""
            episode.fanart = (
                images_obj[-1].get("url", "") if len(images_obj) > 1 else episode.thumb
            )
        else:
            episode.thumb = ""
            episode.fanart = ""

        episode.vod_id = row.get("id", "")
        episode.pgm_no = row.get("pgm_no", "")
        episode.duration = row.get("movie_duration", 0)

        # Check if we have an aired date
        broadcast_start_timestamp = row.get("onair")

        if broadcast_start_timestamp is not None:
            episode.broadcast_start_date = broadcast_start_timestamp
            episode.broadcast_end_date = row.get("vod_to")
            episode.plot_include_broadcast_detail = True

        episodes.append(episode)
    return episodes


def resolve_vod_episode(vod_id):
    """Resolve a VOD episode directly from NHK

    Args:
        vod_id ([str]): The VOD Id

    Returns:
        [Episode]: The resolved Episode with playback URL, or None if failed
    """

    # Handle empty vod_id
    if not vod_id or vod_id == "":
        xbmc.log("vod.resolve_vod_episode: Empty vod_id provided", xbmc.LOGERROR)
        return None

    xbmc.log(
        f"vod.resolve_vod_episode: Getting episode information for vod_id: {vod_id}"
    )

    # Get episode detail with null safety
    episode_result = url.get_json(nhk_api.rest_url["get_episode_detail"].format(vod_id))

    if episode_result is None:
        xbmc.log(
            f"vod.resolve_vod_episode: Failed to get episode details for {vod_id}",
            xbmc.LOGERROR,
        )
        kodiutils.show_notification(
            "NHK World TV", "Unable to load episode. Please try again."
        )
        return None

    # Validate API response has episode data
    if "id" not in episode_result:
        xbmc.log(
            f"vod.resolve_vod_episode: Invalid episode response for {vod_id}",
            xbmc.LOGERROR,
        )
        kodiutils.show_notification(
            "NHK World TV", "Unable to load episode. Please try again."
        )
        return None

    episode_detail = episode_result

    # Fill the episode details
    episode = Episode()
    episode.vod_id = vod_id
    episode.title = episode_detail.get("title", "Unknown Title")

    # Handle broadcast date (ISO 8601 string format)
    onair = episode_detail.get("onair")
    if onair and isinstance(onair, str):
        # ISO string date from new API
        episode.broadcast_start_date = onair

    episode.plot = episode_detail.get("description", "")
    episode.pgm_no = episode_detail.get("pgm_no", "")

    # Get images from episode detail
    images_obj = episode_detail.get("images", {})
    if isinstance(images_obj, dict):
        images = images_obj.get("landscape", [])
        if images:
            episode.thumb = images[0].get("url", "")
            episode.fanart = (
                images[-1].get("url", "") if len(images) > 1 else episode.thumb
            )
        else:
            episode.thumb = ""
            episode.fanart = ""
    elif isinstance(images_obj, list) and images_obj:
        # Some endpoints return images as array directly
        episode.thumb = images_obj[0].get("url", "") if images_obj[0] else ""
        episode.fanart = (
            images_obj[-1].get("url", "") if len(images_obj) > 1 else episode.thumb
        )
    else:
        episode.thumb = ""
        episode.fanart = ""

    # Get duration from video info or movie_duration field
    video_info = episode_detail.get("video", {})
    episode.duration = episode_detail.get("movie_duration") or video_info.get(
        "duration", 0
    )

    # Get video URL from API response
    if video_info and "url" in video_info:
        video_url = video_info.get("url")
        if video_url:
            # Try to upgrade to 1080p if available
            video_url_1080p = url.upgrade_to_1080p(video_url)
            episode.url = video_url_1080p
            xbmc.log(
                f"vod.resolve_vod_episode: Got video URL for {vod_id}: {video_url_1080p}"
            )
            episode.video_info = kodiutils.get_video_info(video_url_1080p)
            episode.is_playable = True
            return episode
        else:
            xbmc.log(
                f"vod.resolve_vod_episode: Empty video URL for {vod_id}",
                xbmc.LOGERROR,
            )
            kodiutils.show_notification("NHK World TV", "Video is not available.")
            return None
    else:
        xbmc.log(
            f"vod.resolve_vod_episode: No video URL in response for {vod_id}",
            xbmc.LOGERROR,
        )
        kodiutils.show_notification("NHK World TV", "Video is not available.")
        return None
