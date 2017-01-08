import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "broncos"
    _cdaweb_url = "http://www.denverbroncos.com/cda-web/"
    _categories = [
        "Broncos TV",
        "Cheerleaders",
        "Community",
        "Elway Exclusive",
        "Fantasy Football",
        "Highlights",
        "Historical Vault",
        "In The Zone",
        "Interviews",
        "Madden",
        "Mic'd Up",
        "NFL Network",
        "Postgame Locker Room",
        "Postgame Press Conferences",
        "Press Conferences",
        "Stadium Experiences",
        "Victory Speech",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
