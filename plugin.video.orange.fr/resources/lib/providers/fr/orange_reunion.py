"""Orange Réunion."""

from lib.providers.abstract_orange_provider import AbstractOrangeProvider


class OrangeReunionProvider(AbstractOrangeProvider):
    """Orange Réunion provider."""

    def __init__(self):
        """Initialize Orange Réunion provider."""
        self.mco = "ORE"
        self.groups = {
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
            "Information internationale": [671, 53, 51, 410, 19, 525, 70239, 70240, 70241, 70242, 781, 830, 70246]
            + [70503],
        }
