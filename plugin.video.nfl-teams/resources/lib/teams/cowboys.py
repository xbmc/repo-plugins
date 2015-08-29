import resources.lib.nflc


class Team(resources.lib.nflc.NFLC):
    _short = "cowboys"
    _website_url = "http://www.dallascowboys.com"
    _categories = [
        (3516, "All Talk Shows"),
        (3586, "#ASKTHEBOYS"),
        (19586, "Audio Only"),  # Renamed from "Videos - Audio Only"
        (3571, "Best Of Talkin'"),
        (3566, "Best of The Break"),
        (3576, "Best of The Draft Show"),
        (2761, "Cheerleaders"),
        (2636, "Coaches & Executives"),
        (28431, "Community"),
        (2606, "Cowboys Break"),
        (21576, "Cowboys Daily in London"),
        (2686, "Cowboys Hour"),
        (19691, "Cowboys Insider"),
        (28886, "Cowboys TV"),
        (19701, "Cowboys Weekend"),
        (3241, "Draft"),
        (3181, "Draft Show"),
        (2926, "Exclusives"),
        (3486, "Fantasy Friday"),
        (3376, "First Take"),
        (19601, "FirstTake"),
        (2626, "Game Highlights"),
        (2696, "History"),
        (2921, "Injury Report"),
        (19596, "InjuryReport"),
        (28891, "Inside Training Camp"),  # Renamed from "Video - Inside Training Camp"
        (3466, "Know The Enemy"),
        (3346, "Live Reports"),
        (2676, "Lunch Break"),
        (2661, "NFL.com"),
        (3231, "On Air"),
        (2611, "Players"),
        (3136, "Quick Snap"),
        (2616, "Reports"),
        (28741, "Road Trip"),  # Renamed from "Video - Road Trip"
        (28561, "Roundtable"),  # Renamed from "Video - Roundtable"
        (2891, "Scouting Report"),
        (19213, "Special Edition"),
        (2596, "Talkin Cowboys"),
        (3581, "The Blitz"),
        (19696, "The Jason Garrett Show"),
        (3441, "The Legends Show"),
        (3471, "Upon Further Review"),
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
