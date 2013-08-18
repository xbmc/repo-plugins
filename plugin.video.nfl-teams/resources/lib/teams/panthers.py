import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "panthers"
    _cdaweb_url = "http://www.panthers.com/cda-web/"
    _categories = [
        "Community",
        "NFL Network",
        "Panthers Gameday",
        "Panthers Huddle",
        "Panthers.com TV",
        "Sir Purr",
        "Stadium Tours",
        "TopCats",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
