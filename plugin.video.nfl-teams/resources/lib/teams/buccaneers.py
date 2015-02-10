import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "buccaneers"
    _cdaweb_url = "http://www.buccaneers.com/cda-web/"
    _categories = [
        "@1Buc",
        "Buccaneers Insider",
        "Bucs Rewind",
        "Cheerleaders",
        "Community",
        "Draft",
        "Events",
        "GameDay",
        "Gameday Preview",
        "Open Locker Room",
        "Post Game",
        "Practice: OTA",
        "Press Conference",
        "Sound FX",
        "Training Camp",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
