import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "jaguars"
    _cdaweb_url = "http://www.jaguars.com/cda-web/"
    _categories = [
        "Videos - All Access",
        "Videos - Cheerleaders",
        "Videos - Combine",
        "Videos - Community",
        "Videos - Draft",
        "Videos - Film Room",
        "Videos - Gameday",
        "Video - Inside the Jaguars",
        "Videos - Interviews",
        "Videos - Jags Wired",
        "Videos - Jaguars.com LIVE",
        "Videos - Kickin It With Scobee",
        "Videos - O-Zone",
        "Videos - ROAR Calendar",
        "Videos - Senior Bowl",
        "Videos - Special Features",
        "Videos - Top 10",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
