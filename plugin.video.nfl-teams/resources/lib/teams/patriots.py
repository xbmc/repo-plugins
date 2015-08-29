import resources.lib.nflc


class Team(resources.lib.nflc.NFLC):
    _short = "patriots"
    _website_url = "http://www.patriots.com"
    _categories = [
        (2211, "All Access"),
        (2221, "Belichick Breakdowns"),
        (2356, "Cheerleaders"),
        (2236, "Coffee with the Coach"),
        (2176, "Draft"),
        (2256, "Game Highlights"),
        (2201, "General"),
        (2241, "Interviews"),
        (2196, "Live Event"),
        (2271, "Locker Room Uncut"),
        (2186, "NRG"),
        (2341, "Patriots This Week"),
        (2266, "Patriots Today"),
        (2301, "PFW TV"),
        (2316, "Press Conference"),
        (2281, "Press Pass"),
        (34926, "Sights and Sounds"),
        (2321, "Sounds of the Game"),
        (2371, "Special"),
        (2361, "Super Bowl"),
        (2331, "Totally Patriots"),
        (2296, "X-Box One: Locker Room"),
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
