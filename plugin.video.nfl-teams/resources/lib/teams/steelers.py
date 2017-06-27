import resources.lib.nflcs


class Team(resources.lib.nflcs.NFLCS):
    _short = "steelers"
    _cdaweb_url = "http://www.steelers.com/cda-web/"
    _categories = [
        "Agree to Disagree",
        "Around the Locker Room",
        "Back to Work",
        "Chalk Talk",
        "Combine",
        "Community",
        "Draft",
        "Espanol",
        "Fashion",
        "Field Report",
        "Gameday",
        "Hall of Fame",
        "HereWeGo",
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
        "Owners Meetings",
        "Player Spotlight",
        "Sights and Sounds",
        "Steelers By Position",
        "Steelers History",
        "Steelers Late Night",
        "Steelers Legends",
        "Steelers LIVE",
        "Steelers Nation Unite",
        "Steelers Saturday Night",
        "Steelers Time Machine",
        "Steelers.com Update",
        "Super Bowl",
        "Training Camp",
        "What It Is",
        "Youth Football",
        "Youth Football Show",
    ]

    def __init__(self, parameters):
        self._parameters = parameters
        self.go()
