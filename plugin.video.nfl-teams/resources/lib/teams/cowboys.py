import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "cowboys"
    _cdaweb_url = "http://www.dallascowboys.com/cda-web/"
    _categories = [
        "Video - AskTheBoys",
        "Videos - Cheerleaders",
        "Video - Coaches-Executives",
        "Videos - Draft",
        "Videos - Exclusives",
        "FirstTake",
        "Video - Game-Highlights",
        "Videos - History",
        "Videos - Know The Enemy",
        "Video - Live Reports",
        "Video - NFL",
        "Video - Players",
        "Video - Quick Snap",
        "Video - Reports",
        "Videos - Scouting Report",
        "Video - Shows - Best Of The Break",
        "Video - Shows - Best Of The Draft Show",
        "Video - Shows - Cowboys Break",
        "Video - Shows - Cowboys Hour",
        "Video - Shows - Draft Show",
        "Video - Shows - On Air",
        "Video - Shows - Talkin Cowboys",
        "Video - Shows - The Legends Show",
        "Video - The Blitz",
        "Videos - Upon Further Review",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
