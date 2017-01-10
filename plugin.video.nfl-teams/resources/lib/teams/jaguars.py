import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "jaguars"
    _cdaweb_url = "http://www.jaguars.com/cda-web/"
    _categories = [
        "Videos - All Access",
        "Videos - Cheerleaders",
        "Videos - Classic Jags",
        "Videos - Community",
        "Videos - Film Room",
        "Videos - Gameday Grub",
        "Videos - Gameday",
        "Video - Inside the Jaguars",
        "Videos - Interviews",
        "Videos - Jags Wired",
        "Videos - Jaguars.com Features",
        "Videos - Jaguars.com LIVE",
        "Videos - O-Zone",
        "Videos - ROAR Calendar",
        "Videos - Union Jax",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
