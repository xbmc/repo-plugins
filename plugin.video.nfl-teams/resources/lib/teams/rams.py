import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "rams"
    _cdaweb_url = "http://www.therams.com/cda-web/"
    _categories = [
        "Video - Cheerleaders",
        "Video - Community",
        "Video - Features",
        "Video - Highlights",
        "Video - Interviews",
        "Video - NFL Combine",
        "Video - NFL Network",
        "Video - One-on-One",
        "Video - Press Conferences",
        "Video - Rams Top Chef",
        "Video - The Staff",
        "Video - Under the Lights",
        "Video - Wired",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
