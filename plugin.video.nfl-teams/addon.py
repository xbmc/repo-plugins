import sys
from urlparse import parse_qs


__plugin__ = "NFL Teams"
__author__ = "Jeppe Toustrup"
__url__ = "https://github.com/Tenzer/plugin.video.nfl-teams"
__version__ = "1.1.2"

if sys.argv[2]:
    parameters = parse_qs(sys.argv[2].lstrip("?"))

    if "team" in parameters:
        team = parameters["team"][0]
        del parameters["team"]

        if team == "bears":
            from resources.lib.teams.bears import Team
        elif team == "bengals":
            from resources.lib.teams.bengals import Team
        elif team == "bills":
            from resources.lib.teams.bills import Team
        elif team == "broncos":
            from resources.lib.teams.broncos import Team
        elif team == "browns":
            from resources.lib.teams.browns import Team
        elif team == "buccaneers":
            from resources.lib.teams.buccaneers import Team
        elif team == "cardinals":
            from resources.lib.teams.cardinals import Team
        elif team == "chargers":
            from resources.lib.teams.chargers import Team
        elif team == "chiefs":
            from resources.lib.teams.chiefs import Team
        elif team == "colts":
            from resources.lib.teams.colts import Team
        elif team == "cowboys":
            from resources.lib.teams.cowboys import Team
        elif team == "dolphins":
            from resources.lib.teams.dolphins import Team
        elif team == "eagles":
            from resources.lib.teams.eagles import Team
        elif team == "falcons":
            from resources.lib.teams.falcons import Team
        elif team == "fourtyniners":
            from resources.lib.teams.fourtyniners import Team
        elif team == "giants":
            from resources.lib.teams.giants import Team
        elif team == "jaguars":
            from resources.lib.teams.jaguars import Team
        elif team == "jets":
            from resources.lib.teams.jets import Team
        elif team == "lions":
            from resources.lib.teams.lions import Team
        elif team == "packers":
            from resources.lib.teams.packers import Team
        elif team == "panthers":
            from resources.lib.teams.panthers import Team
        elif team == "patriots":
            from resources.lib.teams.patriots import Team
        elif team == "raiders":
            from resources.lib.teams.raiders import Team
        elif team == "rams":
            from resources.lib.teams.rams import Team
        elif team == "ravens":
            from resources.lib.teams.ravens import Team
        elif team == "redskins":
            from resources.lib.teams.redskins import Team
        elif team == "saints":
            from resources.lib.teams.saints import Team
        elif team == "seahawks":
            from resources.lib.teams.seahawks import Team
        elif team == "steelers":
            from resources.lib.teams.steelers import Team
        elif team == "texans":
            from resources.lib.teams.texans import Team
        elif team == "titans":
            from resources.lib.teams.titans import Team
        elif team == "vikings":
            from resources.lib.teams.vikings import Team

        Team(parameters)
else:
    import resources.lib.default

    resources.lib.default.Default()
