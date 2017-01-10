import resources.lib.nflc


class Team(resources.lib.nflc.NFLC):
    _short = "chargers"
    _website_url = "http://www.chargers.com"
    _categories = [
        (5906, "Are You Ready?"),
        (1571, "Behind the Bolt"),
        (1636, "Bolts Breakdown"),
        (4591, "BoltsCast"),
        (1671, "BoltsCast - Podcasts (Video)"),
        (32381, "Call of the Game"),
        (4541, "Catch of the Week"),
        (1631, "Charger Girls"),
        (1576, "Chargers Insider"),
        (1591, "Chargers Report"),
        (1616, "Community"),
        (1621, "Features"),
        (1601, "Fitness"),
        (1656, "Game Day"),
        (1626, "Game Highlights"),
        (1661, "Game Time"),
        (4576, "Gameday Show"),
        (5911, "Holiday Card"),
        (4561, "Junior Seau"),
        (22626, "LaDainian Tomlinson"),
        (19391, "Meet The Chargers"),
        (32406, "Micd Up"),
        (1606, "Military"),
        (1611, "News Conferences"),
        (15506, "NFL Draft"),
        (1651, "NFL Network"),
        (32251, "Practice Snapshot"),
        (1561, "Team"),
        (1641, "USA Football"),
        (1666, "Xs and Os"),
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
