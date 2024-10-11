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

    def build_directory(self, levels: str = None) -> None:
        """Build catchup TV directory."""
        levels = levels.split("/") if levels else []
        items = self.provider.get_catchup_items(levels)

        for item in items:
            is_folder = item.get("is_folder")
            xbmcplugin.addDirectoryItem(router.handle, item["path"], create_list_item(item, is_folder), is_folder)

        xbmcplugin.endOfDirectory(router.handle)
