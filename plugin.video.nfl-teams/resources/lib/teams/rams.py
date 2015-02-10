import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "rams"
    _cdaweb_url = "http://www.stlouisrams.com/cda-web/"
    _categories = [
        "Video - Celebrities",
        "Video - Cheerleaders",
        "Video - Combine",
        "Video - Commercials",
        "Video - Community",
        "Video - Features",
        "Video - Fisher Up Front",
        "Video - Highlights",
        "Video - History",
        "Video - Inside the Game",
        "Video - Interviews",
        "Video - Kids Club",
        "Video - NFL Draft",
        "Video - NFL Network",
        "Video - Play 60",
        "Video - Press Conferences",
        "Video - Rams 360",
        "Video - Rams Nation",
        "Video - That's My Dog",
        "Video - Training Camp",
        "Video - Under the Lights",
        "Video - What 2 Watch",
        "Video - Wired",
        "Video - Youth Football",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
