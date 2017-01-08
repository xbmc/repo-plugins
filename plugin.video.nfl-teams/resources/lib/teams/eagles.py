import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "eagles"
    _cdaweb_url = "http://www.philadelphiaeagles.com/cda-web/"
    _categories = [
        "Cheerleaders",
        "Community",
        "Eagle Eye In The Sky",
        "Eagles 360",
        "Eagles Game Plan",
        "Eagles Insider",
        "Eagles Live",
        "Features",
        "Football Analysis",
        "Football News",
        "Gameday Coverage",
        "Highlights",
        "Inside The Eagles",
        "Journey To The Draft",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
