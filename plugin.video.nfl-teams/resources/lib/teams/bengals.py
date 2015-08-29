import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "bengals"
    _cdaweb_url = "http://www.bengals.com/cda-web/"
    _categories = [
        "Audio Conference Calls",
        "Bengals Breakdown",
        "Bengals Weekly",
        "Bengals.com Features",
        "Game Highlights",
        "Game Previews",
        "In the Locker Room",
        "Minicamp/OTAs",
        "NFL Draft",
        "NFL Network",
        "NFL Scouting Combine",
        "Press Conferences",
        "Rookie Minicamp",
        "Training Camp",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
