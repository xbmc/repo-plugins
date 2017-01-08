import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "ravens"
    _cdaweb_url = "http://www.baltimoreravens.com/cda-web/"
    _categories = [
        "360 Replay",
        "Cheerleaders",
        "Community",
        "Draft",
        "Final Drive",
        "Gameday",
        # "LIVE", - Empty (2017-01-08)
        "NFL Network",
        "Press Conferences",
        "Ravens Report",
        "Ravens Unscripted",
        "Ravens Wired",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
