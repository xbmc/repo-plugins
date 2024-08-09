"""Catchup TV Manager."""

import xbmcplugin

from lib.providers import get_provider
from lib.router import router
from lib.utils.gui import create_list_item


class CatchupManager:
    """Navigate through catchup TV content."""

    def __init__(self):
        """Initialize Catchup Manager object."""
        self.provider = get_provider()

    def get_channels(self) -> list:
        """Return channels available for catchup TV."""
        channels = self.provider.get_catchup_channels()

        for channel in channels:
            xbmcplugin.addDirectoryItem(router.handle, channel["path"], create_list_item(channel, True), True)

        xbmcplugin.endOfDirectory(router.handle)

    def get_categories(self, catchup_channel_id: str) -> list:
        """Return content categories for the required channel."""
        categories = self.provider.get_catchup_categories(catchup_channel_id)

        for category in categories:
            xbmcplugin.addDirectoryItem(router.handle, category["path"], create_list_item(category, True), True)

        xbmcplugin.endOfDirectory(router.handle)

    def get_articles(self, catchup_channel_id: str, category_id: str) -> list:
        """Return content (TV show, movie, etc) for the required channel and category."""
        articles = self.provider.get_catchup_articles(catchup_channel_id, category_id)

        for article in articles:
            xbmcplugin.addDirectoryItem(router.handle, article["path"], create_list_item(article, True), True)

        xbmcplugin.endOfDirectory(router.handle)

    def get_videos(self, catchup_channel_id: str, article_id: str) -> list:
        """Return the video list for the required show."""
        videos = self.provider.get_catchup_videos(catchup_channel_id, article_id)

        for video in videos:
            xbmcplugin.addDirectoryItem(router.handle, video["path"], create_list_item(video))

        xbmcplugin.endOfDirectory(router.handle)
