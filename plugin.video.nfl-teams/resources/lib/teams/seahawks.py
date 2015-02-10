import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "seahawks"
    _cdaweb_url = "http://www.seahawks.com/cda-web/"
    _categories = [
        "12th MAN Flag",
        "Community",
        "Highlights",
        "Press Conferences",
        "Sea Gals",
        "Seahawks All-Access",
        "Seahawks Daily",
        "Seahawks Insider",
        "Seahawks on NFL.com",
        "Seahawks Saturday Night",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
