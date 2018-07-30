from os import path

from resources.lib.menu import Menu


class Default(object):
    """Static object, which simply creates a list of teams."""

    _teams = [
        {"short": "cardinals", "long": "Arizona Cardinals"},
        {"short": "falcons", "long": "Atlanta Falcons"},
        {"short": "ravens", "long": "Baltimore Ravens"},
        {"short": "bills", "long": "Buffalo Bills"},
        {"short": "panthers", "long": "Carolina Panthers"},
        {"short": "bears", "long": "Chicago Bears"},
        {"short": "bengals", "long": "Cincinnati Bengals"},
        {"short": "browns", "long": "Cleveland Browns"},
        # {"short": "cowboys", "long": "Dallas Cowboys"},  # The website doesn't have video categories
        {"short": "broncos", "long": "Denver Broncos"},
        {"short": "lions", "long": "Detroit Lions"},
        {"short": "packers", "long": "Green Bay Packers"},
        {"short": "texans", "long": "Houston Texans"},
        {"short": "colts", "long": "Indianapolis Colts"},
        {"short": "jaguars", "long": "Jacksonville Jaguars"},
        {"short": "chiefs", "long": "Kansas City Chiefs"},
        {"short": "chargers", "long": "Los Angeles Chargers"},
        {"short": "rams", "long": "Los Angeles Rams"},
        {"short": "dolphins", "long": "Miami Dolphins"},
        {"short": "vikings", "long": "Minnesota Vikings"},
        # {"short": "patriots", "long": "New England Patriots"},  # The website doesn't have video categories
        {"short": "saints", "long": "New Orleans Saints"},
        {"short": "giants", "long": "New York Giants"},
        {"short": "jets", "long": "New York Jets"},
        {"short": "raiders", "long": "Oakland Raiders"},
        {"short": "eagles", "long": "Philadelphia Eagles"},
        {"short": "steelers", "long": "Pittsburgh Steelers"},
        {"short": "fourtyniners", "long": "San Francisco 49ers"},
        {"short": "seahawks", "long": "Seattle Seahawks"},
        {"short": "buccaneers", "long": "Tampa Bay Buccaneers"},
        {"short": "titans", "long": "Tennessee Titans"},
        {"short": "redskins", "long": "Washington Redskins"}
    ]

    def __init__(self):
        with Menu(["none"]) as menu:
            for team in self._teams:
                menu.add_item({
                    "url_params": {"team": team["short"]},
                    "name": team["long"],
                    "folder": True,
                    "thumbnail": path.join("resources", "images", "{0}.png".format(team["short"]))
                })
