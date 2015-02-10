import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "cardinals"
    _cdaweb_url = "http://www.azcardinals.com/cda-web/"
    _categories = [
        "All In",
        "Cardinals Daily Report",
        "Cards TV",
        "Cheerleaders",
        "Game Highlights",
        "In the Community",
        "Press Pass",
        "Wired",
        "Zoom",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
