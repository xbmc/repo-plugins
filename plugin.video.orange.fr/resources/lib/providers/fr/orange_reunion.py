"""Orange Réunion."""

from lib.providers.provider_interface import ProviderInterface
from lib.utils.orange import get_epg, get_stream_info, get_streams


class OrangeReunionProvider(ProviderInterface):
    """Orange Réunion provider."""

    groups = {
        "Généralistes": [20245, 21079, 1080, 70005, 192, 4, 80, 47, 20118, 78],
        "Divertissement": [30195, 1996, 531, 70216, 57, 70397, 70398, 70399],
        "Jeunesse": [30482],
        "Découverte": [111, 30445],
        "Jeunes": [30444, 20119, 21404, 21403, 563],
        "Musique": [20458, 21399, 70150, 605],
        "Sport": [64, 2837],
        "Jeux": [1061],
        "Société": [1072],
        "Information française": [234, 481, 226, 112, 2111, 529, 1073],
        "Information internationale": [671, 53, 51, 410, 19, 525, 70239, 70240, 70241, 70242, 781, 830, 70246, 70503],
    }

    def get_stream_info(self, channel_id: str) -> dict:
        """Get stream information (MPD address, Widewine key) for the specified id. Required keys: path, mime_type, manifest_type, drm, license_type, license_key."""  # noqa: E501
        return get_stream_info(channel_id, "ORE")

    def get_streams(self) -> list:
        """Retrieve all the available channels and the the associated information (name, logo, preset, etc.) following JSON-STREAMS format."""  # noqa: E501
        return get_streams(self.groups, "ORE")

    def get_epg(self) -> dict:
        """Return EPG data for the specified period following JSON-EPG format."""
        return get_epg(2, "ORE")
