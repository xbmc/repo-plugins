import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "bears"
    _cdaweb_url = "http://www.chicagobears.com/cda-web/"
    _categories = [
        "Bears Talk",
        "Draft",
        "Features",
        "Football",
        "Highlights",
        "Inside The Bears",
        "NFL Network",
        "Press Conferences",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
