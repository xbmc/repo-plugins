import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "bills"
    _cdaweb_url = "http://www.buffalobills.com/cda-web/"
    _categories = [
        "Bills All Access",
        "Bills Focus",
        "Bills History",
        "Bills Roundup",
        "Game Highlights",
        "Jills Cheerleaders",
        "NFL Draft",
        "NFL Network",
        "Off the Field",
        "Press Conferences",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
