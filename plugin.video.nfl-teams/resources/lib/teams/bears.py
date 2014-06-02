import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "bears"
    _cdaweb_url = "http://www.chicagobears.com/cda-web/"
    _categories = [
        "Bear Down of the Week",
        "Bear Trax",
        "Bears Buzz",
        "Draft Central 2014",
        "Features",
        "Game Preview",
        "Highlights",
        "Inside The Bears",
        "Keys to the Game",
        "NFL Network",
        "Offseason",
        "Press Conferences",
        "Sounds of the Game",
        "Thayer's Playbook",
        "Training Camp",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
