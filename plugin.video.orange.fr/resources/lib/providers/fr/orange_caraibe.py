"""Orange Caraïbe."""

from lib.providers.abstract_orange_provider import AbstractOrangeProvider


class OrangeCaraibeProvider(AbstractOrangeProvider):
    """Orange Caraïbe provider."""

    def __init__(self):
        """Initialize Orange Caraïbe provider."""
        self.mco = "OCA"
        self.groups = {}
