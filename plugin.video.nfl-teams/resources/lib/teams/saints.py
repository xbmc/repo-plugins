import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "saints"
    _cdaweb_url = "http://www.neworleanssaints.com/cda-web/"
    _categories = [
        "Gameday",
        "NFL Draft",
        "NFL Network",
        "Plays of the Game",
        "Press Conferences",
        "Saintsations",
        "Training Camp",
        "Youth Programs",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
