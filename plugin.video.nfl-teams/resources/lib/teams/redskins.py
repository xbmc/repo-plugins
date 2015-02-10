import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "redskins"
    _cdaweb_url = "http://www.redskins.com/cda-web/"
    _categories = [
        "Channel 10",
        "Cheerleaders",
        "Comcast SportsNet",
        "Community",
        "Game Day",
        "NFL Films",
        "Press Conferences",
        "Redskins News",
        "Redskins Pride",
        "TV Shows",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
