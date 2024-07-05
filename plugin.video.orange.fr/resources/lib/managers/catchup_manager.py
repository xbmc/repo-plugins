"""Catchup TV Manager."""

import xbmc
import xbmcplugin

from lib.providers import get_provider
from lib.router import router
from lib.utils.gui import create_directory_items
from lib.utils.kodi import build_addon_url


class CatchupManager:
    """Navigate through catchup TV content."""

    def __init__(self):
        """Initialize Catchup Manager object."""
        self.provider = get_provider()

    def get_channels(self) -> list:
        """Return channels available for catchup TV."""
        channels = self.provider.get_catchup_channels()
        directory_items = create_directory_items(channels)

        succeeded = xbmcplugin.addDirectoryItems(router.handle, directory_items, len(directory_items))
        xbmcplugin.endOfDirectory(router.handle, succeeded)

    def get_categories(self, catchup_channel_id: str) -> list:
        """Return content categories for the required channel."""
        categories = self.provider.get_catchup_categories(catchup_channel_id)
        directory_items = create_directory_items(categories)

        succeeded = xbmcplugin.addDirectoryItems(router.handle, directory_items, len(directory_items))
        xbmcplugin.endOfDirectory(router.handle, succeeded)

    def get_articles(self, catchup_channel_id: str, category_id: str) -> list:
        """Return content (TV show, movie, etc) for the required channel and category."""
        articles = self.provider.get_catchup_articles(catchup_channel_id, category_id)
        directory_items = create_directory_items(articles)

        succeeded = xbmcplugin.addDirectoryItems(router.handle, directory_items, len(directory_items))
        xbmcplugin.endOfDirectory(router.handle, succeeded)

    def get_videos(self, catchup_channel_id: str, article_id: str) -> list:
        """Return the video list for the required show."""
        videos = self.provider.get_catchup_videos(catchup_channel_id, article_id)
        directory_items = create_directory_items(videos)

        succeeded = xbmcplugin.addDirectoryItems(router.handle, directory_items, len(directory_items))
        xbmcplugin.endOfDirectory(router.handle, succeeded)

    def play_video(self, video_id: str):
        """Play catchup video."""
        player = xbmc.Player()
        player.play(build_addon_url(f"/catchup-streams/{video_id}"))
