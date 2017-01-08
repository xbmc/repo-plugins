import resources.lib.nflc


class Team(resources.lib.nflc.NFLC):
    _short = "seahawks"
    _website_url = "http://www.seahawks.com"
    _categories = [
        (1651, "12 Flag"),
        (1636, "Community"),
        (30186, "Conference Call"),
        (32061, "DO NOT USE Home"),
        (10836, "Eye of the Hawk"),
        (48371, "Fantasy"),
        (25786, "From NFL Network"),
        (1606, "Highlights"),
        (48136, "In The City"),
        (48396, "In The City Sea Fair"),
        (10826, "Locker Room Sound"),
        (48386, "Off Day"),
        (1631, "Press Conferences"),
        (1661, "Promotional Video"),
        (51286, "Raible Call of the Game"),
        (1641, "Sea Gals"),
        (1611, "Seahawks All-Access"),
        (1596, "Seahawks Daily"),
        (9151, "Seahawks Insider"),
        (1626, "Seahawks on NFL Network"),
        (25791, "Seahawks on NFL.com"),
        (10446, "Seahawks Press Pass"),
        (1616, "Seahawks Saturday Night"),
        (10831, "Seahawks.com Exclusive"),
        (11196, "The Huddle"),
        (1646, "Training Camp"),
        (1656, "USAA Salute to Service"),
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
