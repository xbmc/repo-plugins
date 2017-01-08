import resources.lib.nflc


class Team(resources.lib.nflc.NFLC):
    _short = "patriots"
    _website_url = "http://www.patriots.com"
    _categories = [
        (72441, "47 Second Player Interviews"),
        (2211, "All Access"),
        (2396, "All Video"),
        (60351, "Belichick Breakdown"),
        (2221, "Belichick Breakdowns"),
        (2386, "Belichick Breakdowns (exclusive)"),
        (2356, "Cheerleaders"),
        (2236, "Coffee with the Coach"),
        (2176, "Draft"),
        (2201, "General"),
        (2241, "Interviews"),
        (2196, "Live Event"),
        (73301, "Locker Room Celebrations"),
        (72416, "Magic Moments"),
        (2256, "NFL"),
        (2186, "NRG"),
        (58366, "Patriot Today: Locker Room Uncut"),
        (2341, "Patriots This Week"),
        (2266, "Patriots Today"),
        (2271, "Patriots Today: Locker Room Uncut"),
        (2281, "Patriots Today: Press Pass"),
        (2301, "PFW TV"),
        (70941, "Play by Pics"),
        (2316, "Press Conference"),
        (2401, "Press Conference Video"),
        (55906, "Press Pass"),
        (34926, "Sights and Sounds"),
        (2321, "Sounds of the Game"),
        (2371, "Special"),
        (2361, "Super Bowl"),
        (51511, "Syndication"),
        (9776, "Team"),
        (2331, "Totally Patriots"),
        (2296, "X-Box One: Postgame Locker Room"),
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
