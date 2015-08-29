import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "saints"
    _cdaweb_url = "http://www.neworleanssaints.com/cda-web/"
    _categories = [
        "Afternoon Wrap",
        "Coach Executive",
        "Fantasy",
        "Game Highlights",
        "Gameday",
        "Morning Report",
        "NFL Draft",
        "NFL Network",
        "Player",
        "Plays of the Game",
        "Practice",
        "Press Conferences",
        "Saintsations",
        "Training Camp",
        "Youth Programs",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
