import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "buccaneers"
    _cdaweb_url = "http://www.buccaneers.com/cda-web/"
    _categories = [
        "Buccaneers Insider",
        "Cheerleaders",
        "Community",
        "Gameday",
        "Injury Report",
        "NFL Network",
        "Open Locker Room",
        "Press Conference",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
