import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "rams"
    _cdaweb_url = "http://www.therams.com/cda-web/"
    _categories = [
        "Video - Cheerleaders",
        "Video - Community",
        "Video - Features",
        "Video - Hard Knocks",
        "Video - Highlights",
        "Video - Interviews",
        "Video - NFL Combine",
        "Video - NFL Draft",
        "Video - NFL Network",
        "Video - One-on-One",
        "Video - Play 60",
        "Video - Press Conferences",
        "Video - Rams 360",
        "Video - Rams Nation",
        "Video - The Search",
        "Video - Training Camp",
        "Video - Under the Lights",
        "Video - Wired",
        "Video - Youth Football",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
