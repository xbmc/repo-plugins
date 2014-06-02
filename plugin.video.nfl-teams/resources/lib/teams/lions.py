import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "lions"
    _cdaweb_url = "http://www.detroitlions.com/cda-web/"
    _categories = [
        "Alumni Roundtable",
        "Archive",
        "Coach's View",
        "Game Highlights",
        "Herman One-on-One",
        "Media Sessions",
        "Monday Presser",
        "Postgame Video",
        "Tim and Mike",
        "Wired for Sound",
        "Youth Football",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
