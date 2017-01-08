import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "packers"
    _cdaweb_url = "http://www.packers.com/cda-web/"
    _categories = [
        "After Further Review",
        "Alumni Spotlight",
        "Community",
        "Exclusives",
        "Game Highlights",
        "Game Preview",
        "Locker Room Interviews",
        "Mike McCarthy Show",
        "NFL Network",
        "Press Conference",
        "Prospect Primer",
        # "Sights & Sounds", - Empty (2017-01-08)
        "Tailgate Tour",
        "The McCarren Report",
        "Training Camp",
        "Under The Cap",
        "Video Ask Vic",
        "What You Mightve Missed",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
