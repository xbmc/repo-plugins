import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "steelers"
    _cdaweb_url = "http://www.steelers.com/cda-web/"
    _categories = [
        # "#HereWeGo", - Empty (2017-01-08)
        "Agree to Disagree",
        "Around the Locker Room",
        # "Back to Work", - Empty (2017-01-08)
        "Chalk Talk",
        "Combine",
        "Community",
        "Draft",
        "Espanol",
        "Fashion",
        "Field Report",
        "Gameday",
        "Hall of Fame",
        "Highlights",
        "Holidays",
        "In a Minute",
        "Interviews",
        "Junior Reporter",
        "Keys to the Game",
        "Mike Tomlin Press Conference",
        "Mike Tomlin Show",
        "News Conferences",
        "NFL Network",
        # "Player Spotlight", - Empty (2017-01-08)
        "Sights and Sounds",
        "Steelers By Position",
        "Steelers History",
        "Steelers Late Night",
        "Steelers Legends",
        "Steelers LIVE",
        "Steelers Nation Unite",
        # "Steelers Saturday Night", - Empty (2017-01-08)
        "Steelers Time Machine",
        "Steelers.com Update",
        "Super Bowl",
        "Training Camp",
        "What It Is",
        "Youth Football Show",
        "Youth Football",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
