import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "titans"
    _cdaweb_url = "http://www.titansonline.com/cda-web/"
    _categories = [
        "Cheerleaders",
        "Community",
        "Game Highlights",
        "NFL Network Features",
        "Player Interviews",
        "Press Conferences",
        "T-RAC",
        "Titans All Access",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
