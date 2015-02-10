import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "giants"
    _cdaweb_url = "http://www.giants.com/cda-web/"
    _categories = [
        "Draft",
        "Features",
        "Gameday",
        "Giants Online",
        "Interviews",
        "Sights and Sounds",
        "Superbowl 46",
        "TV Shows",
        "Web Shows",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
