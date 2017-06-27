import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "titans"
    _cdaweb_url = "http://www.titansonline.com/cda-web/"
    _categories = [
        "2017 Draft",
        "Behind the Flame",
        "Cheerleaders",
        "Community",
        "Exclusives",
        "Game Highlights",
        "NFL Network Features",
        "One-on-One",
        "Player Interviews",
        "Press Conferences",
        "Titans All Access",
        "Titans in Two",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
