import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "fourtyniners"
    _cdaweb_url = "http://www.49ers.com/cda-web/"
    _categories = [
        "Video - 49ers Press Pass",
        "Video - 49ers Studios",
        "Video - 49ers Total Access",
        "Video - Coming Soon",
        "Video - Community",
        "Video - Cover 2",
        "Video - Game Highlights",
        "Video - Gold Rush",
        "Video - Locker Room Speech",
        "Video - Micd Up",
        "Video - NFL Network",
        "Video - Niner Talk",
        "Video - The Joe Show",
        "Video - The Remix",
        "Video - Top 10 Moments",
        "Video - Weekly Conversation",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
