import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "bills"
    _cdaweb_url = "http://www.buffalobills.com/cda-web/"
    _categories = [
        "Beyond Blue and Red",
        "Bills Focus",
        "Bills History",
        "Bills Roundup",
        "Camp Highlights",
        "Coffee with the Coach",
        "Combine",
        "Draft",
        "Game Highlights",
        "Inside the Locker Room",
        "NFL Network",
        "Off the Field",
        "Press Conferences",
        "Senior Bowl",
        "Unfiltered",
        "Wired for Sound",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
