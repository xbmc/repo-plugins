import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "chiefs"
    _cdaweb_url = "http://www.kcchiefs.com/cda-web/"
    _categories = [
        "Video - ArrowVision",
        "Video - Cheerleaders",
        "Video - Chiefs Kingdom",
        "Video - Chiefs Live",
        "Video - Chiefs Today",
        "Video - Community",
        "Video - Draft",
        "Video - Highlights",
        "Video - History",
        "Video - Hy-Vee Chiefs Insider",
        "Video - Press Conferences",
        "Video - Red and Gold",
        "Video - Training Camp",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
