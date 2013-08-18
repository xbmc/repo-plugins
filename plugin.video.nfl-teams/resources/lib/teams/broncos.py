import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "broncos"
    _cdaweb_url = "http://www.denverbroncos.com/cda-web/"
    _categories = [
        "Broncos TV",
        "Cheerleaders",
        "Community",
        "Events",
        "Locker Room",
        "NFL Network",
        "Press Conferences",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
