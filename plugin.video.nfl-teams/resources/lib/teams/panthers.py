import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "panthers"
    _cdaweb_url = "http://www.panthers.com/cda-web/"
    _categories = [
        "Coach Interviews",
        "Community",
        "Mailbag",
        "NFL Network",
        "Panthers Gameday",
        "Panthers Huddle",
        "Panthers Insider",
        "Panthers Pulse",
        "Panthers.com TV",
        "Player Interviews",
        "Sir Purr",
        "Stadium Tours",
        "TopCats",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
