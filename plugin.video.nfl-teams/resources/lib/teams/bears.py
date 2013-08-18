import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "bears"
    _cdaweb_url = "http://www.chicagobears.com/cda-web/"
    _categories = [
        "Bear Down of the Week",
        "Bear Trax",
        "Draft",
        "Features",
        "Final Horn",
        "Game Preview",
        "Healthy with the Bears",
        "Highlights",
        "Keys to the Game",
        "NFL Network",
        "Offseason",
        "Press Conferences",
        "Sounds of the Game",
        "Tradition",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
