import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "cowboys"
    _cdaweb_url = "http://www.dallascowboys.com/cda-web/"
    _categories = [
        "Videos - Cheerleaders",
        "Video - Coaches-Executives",
        "Videos - Exclusives",
        "Video - Game-Highlights",
        "Videos - History",
        "Video - NFL",
        "Video - Players",
        "Video - Reports",
        "Videos - Scouting Report",
        "Video - Shows - Cowboys Break",
        "Video - Shows - Talkin Cowboys",
        "Video - Shows - Draft Show",
        "Video - Shows - On Air",
        "Video - Quick Snap",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
