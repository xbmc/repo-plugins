import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "steelers"
    _cdaweb_url = "http://www.steelers.com/cda-web/"
    _categories = [
        "Agree to Disagree",
        "Chalk Talk",
        "Combine",
        "Community",
        "Draft",
        "Espanol",
        "Features",
        "Gameday",
        "Highlights",
        "In a Minute",
        "Interviews",
        "Kid Zone",
        "News Conferences",
        "NFL Network",
        "Off the Field",
        "Steelers By Position",
        "Steelers.com LIVE",
        "Steelers.com Update",
        "SteelersTV",
        "Super Bowl",
        "Training Camp",
        "What It Is",
        "Youth Football",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
