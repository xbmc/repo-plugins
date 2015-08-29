import resources.lib.nflc


class Team(resources.lib.nflc.NFLC):
    _short = "chargers"
    _website_url = "http://www.chargers.com"
    _categories = [
        (1571, "Behind the Bolt"),
        (1636, "Bolts Breakdown"),
        (4591, "BoltsCast"),
        (1631, "Charger Girls"),
        (1576, "Chargers Insider"),
        (1616, "Community"),
        (1621, "Features"),
        (1626, "Game Highlights"),
        (1661, "Game Time"),
        (5911, "Holiday Card"),
        (1611, "News Conferences"),
        (15506, "NFL Draft"),
        (1651, "NFL Network"),
        (1666, "Xs and Os"),
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
