"""TV Provider interface."""


class ProviderInterface:
    """Provide methods to be implemented by each ISP."""

    def get_stream_info(self, channel_id: str) -> dict:
        """Get stream information (MPD address, Widewine key) for the specified id. Required keys: path, mime_type, manifest_type, drm, license_type, license_key."""  # noqa: E501

    def get_streams(self) -> list:
        """Retrieve all the available channels and the the associated information (name, logo, preset, etc.) following JSON-STREAMS format."""  # noqa: E501

    def get_epg(self) -> dict:
        """Return EPG data for the specified period following JSON-EPG format."""
