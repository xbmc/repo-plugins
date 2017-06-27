import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "ravens"
    _cdaweb_url = "http://www.baltimoreravens.com/cda-web/"
    _categories = [
        "360 Replay",
        "Cheerleaders",
        "Community",
        "Draft",
        "Facebook Live",
        "Final Drive",
        "Gameday",
        "LIVE",
        "NFL Network",
        "Press Conferences",
        "Ravens Report",
        "Ravens Unscripted",
        "Ravens Wired",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
