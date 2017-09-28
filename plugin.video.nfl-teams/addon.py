import json
import sys
from urllib import unquote

__plugin__ = "NFL Teams"
__author__ = "Jeppe Toustrup"
__url__ = "https://github.com/Tenzer/plugin.video.nfl-teams"
__version__ = "1.3.4"

if sys.argv[2]:
    parameters = json.loads(unquote(sys.argv[2].lstrip("?")))

    if parameters["team"] == "bears":
        from resources.lib.teams.bears import Team
    elif parameters["team"] == "bengals":
        from resources.lib.teams.bengals import Team
    elif parameters["team"] == "bills":
        from resources.lib.teams.bills import Team
    elif parameters["team"] == "broncos":
        from resources.lib.teams.broncos import Team
    elif parameters["team"] == "browns":
        from resources.lib.teams.browns import Team
    elif parameters["team"] == "buccaneers":
        from resources.lib.teams.buccaneers import Team
    elif parameters["team"] == "cardinals":
        from resources.lib.teams.cardinals import Team
    elif parameters["team"] == "chargers":
        from resources.lib.teams.chargers import Team
    elif parameters["team"] == "chiefs":
        from resources.lib.teams.chiefs import Team
    elif parameters["team"] == "colts":
        from resources.lib.teams.colts import Team
    elif parameters["team"] == "cowboys":
        from resources.lib.teams.cowboys import Team
    elif parameters["team"] == "dolphins":
        from resources.lib.teams.dolphins import Team
    elif parameters["team"] == "eagles":
        from resources.lib.teams.eagles import Team
    elif parameters["team"] == "falcons":
        from resources.lib.teams.falcons import Team
    elif parameters["team"] == "fourtyniners":
        from resources.lib.teams.fourtyniners import Team
    elif parameters["team"] == "giants":
        from resources.lib.teams.giants import Team
    elif parameters["team"] == "jaguars":
        from resources.lib.teams.jaguars import Team
    elif parameters["team"] == "jets":
        from resources.lib.teams.jets import Team
    elif parameters["team"] == "lions":
        from resources.lib.teams.lions import Team
    elif parameters["team"] == "packers":
        from resources.lib.teams.packers import Team
    elif parameters["team"] == "panthers":
        from resources.lib.teams.panthers import Team
    elif parameters["team"] == "patriots":
        from resources.lib.teams.patriots import Team
    elif parameters["team"] == "raiders":
        from resources.lib.teams.raiders import Team
    elif parameters["team"] == "rams":
        from resources.lib.teams.rams import Team
    elif parameters["team"] == "ravens":
        from resources.lib.teams.ravens import Team
    elif parameters["team"] == "redskins":
        from resources.lib.teams.redskins import Team
    elif parameters["team"] == "saints":
        from resources.lib.teams.saints import Team
    elif parameters["team"] == "seahawks":
        from resources.lib.teams.seahawks import Team
    elif parameters["team"] == "steelers":
        from resources.lib.teams.steelers import Team
    elif parameters["team"] == "texans":
        from resources.lib.teams.texans import Team
    elif parameters["team"] == "titans":
        from resources.lib.teams.titans import Team
    elif parameters["team"] == "vikings":
        from resources.lib.teams.vikings import Team

    Team(parameters)
else:
    from resources.lib.default import Default
    Default()
