import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "seahawks"
    _cdaweb_url = "http://www.seahawks.com/cda-web/"
    _categories = [
        "12th MAN Flag",
        "Coach's Show",
        "Community",
        "Highlights",
        "NFL Network",
        "News Releases",
        "Press Conferences",
        "Sea Gals",
        "Seahawks 1-on-1",
        "Seahawks All-Access",
        "Seahawks Audible",
        "Seahawks Daily",
        "Seahawks Insider",
        "Seahawks Saturday Night",
        "Seahawks on NFL.com",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
