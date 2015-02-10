import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "falcons"
    _cdaweb_url = "http://www.atlantafalcons.com/cda-web/"
    _categories = [
        "Video - Cheerleaders",
        "Video - Community",
        "Video - D-Block",
        "Video - Game Highlights",
        "Video - Game Week",
        "Video - Gameday",
        "Video - NFL Draft",
        "Video - NFL Network",
        "Video - Offseason",
        "Video - Player Shows",
        "Video - Playoffs",
        "Video - Quick Hits",
        "Video - Training Camp",
        "Video - Vantage Point",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
