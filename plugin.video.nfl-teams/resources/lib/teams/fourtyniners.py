import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "fourtyniners"
    _cdaweb_url = "http://www.49ers.com/cda-web/"
    _categories = [
        "Video - 1on1",
        "Video - 49ers Press Pass",
        "Video - 49ers Studios",
        "Video - 49ers Total Access",
        "Video - Action Cam",
        "Video - Coming Soon",
        "Video - Community",
        "Video - Cover 2",
        "Video - Draft",
        "Video - Forty Niner Way",
        "Video - Game Highlights",
        "Video - Gold Rush",
        "Video - Levis Stadium",
        "Video - Locker Room Speech",
        "Video - Micd Up",
        "Video - NFL Network",
        "Video - Niner Talk",
        "Video - The Faithful",
        "Video - The Joe Show",
        "Video - The Remix",
        "Video - Top 10 Moments",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
