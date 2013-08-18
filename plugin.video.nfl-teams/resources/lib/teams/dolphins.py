import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "dolphins"
    _cdaweb_url = "http://www.miamidolphins.com/cda-web/"
    _categories = [
        "Camp Dolphins",
        "Community",
        "En Espanol",
        "FinsidersTV",
        "Game Day",
        "NFL Network",
        "Official Shows",
        "Players",
        "Postgame Press Conference",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
