import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "ravens"
    _cdaweb_url = "http://www.baltimoreravens.com/cda-web/"
    _categories = [
        "2 Minute Drill",
        "Cheerleaders",
        "Community",
        "CSN",
        "Gameday",
        "LIVE",
        "NFL Network",
        "Poe",
        "Press Conferences",
        "Ravens Productions - Ravens Report",
        "Ravens Productions - Unscripted",
        "Ravens Productions - Wired",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
