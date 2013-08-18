import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "vikings"
    _cdaweb_url = "http://www.vikings.com/cda-web/"
    _categories = [
        "Beyond The Gridiron",
        "Cheerleaders",
        "Community",
        "Draft 2011", # TODO: Make a way to rename to "Draft", as that's what it's called on Vikings.com
        "Game Day",
        "NFL Network",
        "Press Conferences",
        "Stadium",
        "Training Camp",
        "VEN Channel",
        "Vikings GamePlan",
        "Vikings Wired",
        "Viktor the Viking",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
