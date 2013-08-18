import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "jaguars"
    _cdaweb_url = "http://www.jaguars.com/cda-web/"
    _categories = [
        "Videos - All Access",
        "Videos - Cheerleaders",
        "Videos - Community",
        "Videos - Film Room",
        "Videos - Gameday",
        "Video - Inside the Jaguars",
        "Videos - Interviews",
        "Videos - NFL Network",
        "Videos - O-Zone",
        "Videos - Special Features",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
