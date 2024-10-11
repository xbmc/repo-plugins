"""Abstract TV Provider."""

from abc import ABC, abstractmethod
from typing import List


class AbstractProvider(ABC):
    """Provide methods to be implemented by each ISP."""

    @abstractmethod
    def get_live_stream_info(self, stream_id: str) -> dict:
        """Get live stream information (MPD address, Widewine key) for the specified id. Returned keys: path, mime_type, manifest_type, drm, license_type, license_key."""  # noqa: E501
        pass

    @abstractmethod
    def get_catchup_stream_info(self, stream_id: str) -> dict:
        """Get catchup stream information (MPD address, Widewine key) for the specified id. Returned keys: path, mime_type, manifest_type, drm, license_type, license_key."""  # noqa: E501
        pass

    @abstractmethod
    def get_streams(self) -> list:
        """Retrieve all the available channels and the the associated information (name, logo, preset, etc.) following JSON-STREAMS format."""  # noqa: E501
        pass

    @abstractmethod
    def get_epg(self) -> dict:
        """Return EPG data for the specified period following JSON-EPG format."""
        pass

    @abstractmethod
    def get_catchup_items(self, levels: List[str]) -> list:
        """Return a list of directory items for the specified levels."""
        pass
