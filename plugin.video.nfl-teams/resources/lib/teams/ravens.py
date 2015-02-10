import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "ravens"
    _cdaweb_url = "http://www.baltimoreravens.com/cda-web/"
    _categories = [
        "2 Minute Drill",
        "Cheerleaders",
        "Community",
        "CSN",
        "Gameday",
        "Mailbag",
        "NFL Network",
        "Press Conferences",
        "Pump-Up Takeovers",
        "Rave TV - 1 Winning Drive",
        "Rave TV - Ravens One-on-One",
        "Rave TV - Ravens Report",
        "Ray Lewis",
        "Super Bowl XLVII",
        "Training Camp",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
