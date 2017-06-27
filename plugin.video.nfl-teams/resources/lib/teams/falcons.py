import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "falcons"
    _cdaweb_url = "http://www.atlantafalcons.com/cda-web/"
    _categories = [
        "Video - Cheerleaders",
        "Video - Coach's Corner",
        "Video - Community",
        "Video - D-Block",
        "Video - Draft",
        "Video - FalconCast",
        "Video - FalconsLIVE",
        "Video - Features",
        "Video - Gameday",
        "Video - Highlights",
        "Video - History",
        "Video - Interviews & Press Conferences",
        "Video - New Stadium",
        "Video - NFL Network",
        "Video - Playoffs",
        "Video - Quick Hits",
        "Video - Training Camp",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
