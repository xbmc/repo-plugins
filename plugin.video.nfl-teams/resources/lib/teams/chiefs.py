import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "chiefs"
    _cdaweb_url = "http://www.kcchiefs.com/cda-web/"
    _categories = [
        "Video - Arrowhead Update",
        "Video - Cheerleaders",
        "Video - Chiefs Kingdom",
        "Video - Chiefs Live",
        "Video - Chiefs Today",
        "Video - Community",
        "Video - Highlights",
        "Video - History",
        "Video - Hy-Vee Chiefs Insider",
        "Video - Play Breakdown",
        "Video - Press Conferences",
        # "Video - Red and Gold", - Empty (2017-01-08)
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
