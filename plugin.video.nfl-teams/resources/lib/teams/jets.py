import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "jets"
    _cdaweb_url = "http://www.newyorkjets.com/cda-web/"
    _categories = [
        "Coach's Corner",
        "Coordinators Press Conferences",
        "Exclusives",
        "Flight Crew",
        "Gameday Highlights",
        "Interview",
        "Jets Talk Live",
        "Locker Room Sound",
        "MetLife Stadium",
        "On the Inside with EA",
        "On the Road",
        "Press Conferences",
        "Season Ticket Holders",
        "Sights and Sounds",
        "Team Report",
        "The Jets Minute",
        "This Is Our House",
        "TV Shows - SNY",
        "TV Shows - WCBS",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
