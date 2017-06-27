import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "fourtyniners"
    _cdaweb_url = "http://www.49ers.com/cda-web/"
    _categories = [
        "Video - 1on1",
        "Video - 49ers Live",
        "Video - 49ers Press Pass",
        "Video - 49ers Studios",
        "Video - Action Cam",
        "Video - Community",
        "Video - Draft",
        "Video - Forty Niner Way",
        "Video - Game Highlights",
        "Video - Gold Rush",
        "Video - Micd Up",
        "Video - NFL Network",
        "Video - Niner Talk",
        "Video - The Faithful",
        "Video - Top 10 Moments",
        "Video - Training Camp",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
