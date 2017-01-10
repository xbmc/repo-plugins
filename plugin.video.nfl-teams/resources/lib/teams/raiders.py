import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "raiders"
    _cdaweb_url = "http://www.raiders.com/cda-web/"
    _categories = [
        "Behind the Shield",
        "Game Highlights",
        "Historical Highlights",
        "NFL Network",
        "Press Conferences",
        "Raiderettes",
        "Raiders Report",
        # "Silver and Black", - Empty (2017-01-08)
        "Viva",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
