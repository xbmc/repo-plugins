import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "jets"
    _cdaweb_url = "http://www.newyorkjets.com/cda-web/"
    _categories = [
        "Draft/Combine",
        "Flight Crew",
        "Game Preview & Review",
        "Gameday Highlights",
        "Green & White Report",
        "Jets Replay",
        "Jets Takeoff",
        "Jets Talk Live",
        "Locker Room Sound",
        "MetLife Stadium",
        "On the Inside with EA",
        "Press Conferences",
        "TV Shows",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
