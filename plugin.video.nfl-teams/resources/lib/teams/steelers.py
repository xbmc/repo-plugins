import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "steelers"
    _cdaweb_url = "http://www.steelers.com/cda-web/"
    _categories = [
        "1st and 10",
        "Chalk Talk",
        "Community",
        "Draft",
        "Espanol",
        "Features",
        "Gameday",
        "Interviews",
        "Kid Zone",
        "News Conferences",
        "Off the Field",
        "SteelersTV",
        "Super Bowl",
        "Training Camp",
        "Youth Football",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
