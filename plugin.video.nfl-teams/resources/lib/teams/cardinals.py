import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "cardinals"
    _cdaweb_url = "http://www.azcardinals.com/cda-web/"
    _categories = [
        "All In",
        "Cardinals Chronicles",
        "Cardinals Daily Report",
        "Cards TV",
        "Cheerleaders",
        "Coming Soon",
        "Game Highlights",
        "In the Community",
        "Locker Room Speeches",
        "Press Pass",
        "Rosetta Stone",
        "Take 5",
        "Tenacious",
        "Training Camp",
        "Wired",
        "Xmo Xtra",
        "Zoom",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
