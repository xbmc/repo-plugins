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
        # "Sights & Sounds",  # Does not return any videos, neither in Kodi or on the website
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
