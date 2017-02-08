import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "jets"
    _cdaweb_url = "http://www.newyorkjets.com/cda-web/"
    _categories = [
        "All Access",
        "Coordinators Press Conferences",
        "Flight Crew",
        "Gameday Highlights",
        "JetLife",
        "Jets in 90",
        "Jets Nation",
        "Jets Spotlight",
        "Jets Talk Live",
        "Legends",
        "Locker Room Sound",
        "National Perspective",
        "NFL Network",
        "On the Road",
        "Practice Highlights",
        "Press Conferences",
        "Sights and Sounds",
        "Team Report",
        "This Is Our House",
        "TV Shows - SNY",
        "TV Shows - WCBS",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
