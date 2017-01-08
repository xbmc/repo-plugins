import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "falcons"
    _cdaweb_url = "http://www.atlantafalcons.com/cda-web/"
    _categories = [
        "Video - Cheerleaders",
        "Video - Coach's Corner",
        "Video - Community",
        # "Video - D-Block", - Empty (2017-01-08)
        # "Video - Draft", - Empty (2017-01-08)
        "Video - FalconCast",
        # "Video - FalconsLIVE", - Empty (2017-01-08)
        "Video - Features",
        "Video - Gameday",
        "Video - Highlights",
        # "Video - History", - Empty (2017-01-08)
        "Video - Interviews & Press Conferences",
        # "Video - New Stadium", - Empty (2017-01-08)
        "Video - NFL Network",
        "Video - Playoffs",
        "Video - Quick Hits",
        "Video - Training Camp",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
