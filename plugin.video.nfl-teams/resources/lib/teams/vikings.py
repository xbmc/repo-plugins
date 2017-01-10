import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "vikings"
    _cdaweb_url = "http://www.vikings.com/cda-web/"
    _categories = [
        "Beyond The Gridiron",
        "Cheerleaders",
        "Community",
        "Draft 2011",
        "Game Day",
        "NFL Network",
        "Press Conferences",
        "Stadium",
        "Training Camp",
        "VEN Channel",
        "Vikings Connected",
        "Vikings GamePlan",
        "Vikings Wired",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
