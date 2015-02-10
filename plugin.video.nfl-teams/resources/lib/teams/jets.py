import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "jets"
    _cdaweb_url = "http://www.newyorkjets.com/cda-web/"
    _categories = [
        "Draft/Combine",
        "Exclusives",
        "Flight Crew",
        "Gameday Highlights",
        "In-Stadium Videos",
        "Jets Replay",
        "Jets Talk Live",
        "Locker Room Sound",
        "MetLife Stadium",
        "On the Inside with EA",
        "Point After",
        "Press Conferences",
        "The Jets Minute",
        "TV Shows - SNY",
        "TV Shows - WCBS",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
