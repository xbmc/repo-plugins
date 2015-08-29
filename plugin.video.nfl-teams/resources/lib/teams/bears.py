import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "bears"
    _cdaweb_url = "http://www.chicagobears.com/cda-web/"
    _categories = [
        "Bear Down of the Week",
        "Bears Buzz",
        "Bears InSight",
        "Bears Roundtable",
        "Draft",
        "Features",
        "Game Preview",
        "Highlights",
        "Inside The Bears",
        "Keys to the Game",
        "NFL Network",
        "Press Conferences",
        "Sideline Soundtrack",
        "Sounds of the Game",
        "Thayer's Playbook",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
