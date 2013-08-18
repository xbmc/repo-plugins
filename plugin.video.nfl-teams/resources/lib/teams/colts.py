import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "colts"
    _cdaweb_url = "http://www.colts.com/cda-web/"
    _categories = [
        "Blue",
        "Cheerleaders",
        "Colts UpClose",
        "Community",
        "Facebook Friday",
        "Game Highlights",
        "Instant Access",
        "Locker Talk",
        "My Indiana Football",
        "NFL Draft",
        "NFL Videos",
        "One on One",
        "Player Focus",
        "Postgame Locker Room",
        "Postgame Speech",
        "Pregame Report",
        "Press Conferences",
        "Sounds of the Game",
        "Three Things to Watch For",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
