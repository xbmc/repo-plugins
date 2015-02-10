import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "chargers"
    _cdaweb_url = "http://www.chargers.com/cda-web/"
    _categories = [
        "Charger Girls",
        "Chargers Report",
        "Community",
        "Features",
        "Game Highlights",
        "Game Time",
        "NFL Network",
        "USA Football",
        "Xs and Os",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
