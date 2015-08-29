import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "colts"
    _cdaweb_url = "http://www.colts.com/cda-web/"
    _categories = [
        "Cheerleaders",
        "Colts TV",
        "Gameday",
        "Postgame Speech",
        "Press Conferences",
        "Sounds of the Game",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
