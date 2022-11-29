from resources.lib.globals import *

class Game:

    def __init__(self, game_json):
        self.game_id = game_json["id"]
        self.start_time = game_json["startTime"]
        self.home_team = game_json["homeCompetitor"]
        self.away_team = game_json["awayCompetitor"]
        self.content = game_json["content"]
        self.home_id = ""
        self.away_id = ""
        self.highlight_id = ""

    def create_listitem(self):
        content = self.content[0]
        title = str(content["editorial"]["translations"]["en"]["title"]).title()
        game_time = utc_to_local(string_to_date(self.start_time, "%Y-%m-%dT%H:%M:%S+00:00"))
        game_day = game_time.strftime("%Y-%m-%d")

        name = title
        if not content["status"]["isLive"]:
            if TIME_FORMAT == '0':
                game_time = game_time.strftime('%I:%M %p').lstrip('0')
            else:
                game_time = game_time.strftime('%H:%M')
            name = "%s %s" % (game_time, title)

        self.set_ids()

        icon = "%s%s" % (ICON_URL, content["editorial"]["image"]["path"])
        fanart = "%s%s" % (FANART_URL, content["editorial"]["image"]["path"])
        info = {'plot': "",
                'tvshowtitle': 'NHLTV',
                'title': title,
                'originaltitle': title,
                'aired': game_day,
                'genre': 'Sports'}

        # add_stream(name, '', title, self.home_id, self.away_id, icon, fanart, info, video_info, audio_info)

        add_stream(name, title, icon, fanart, info, home_id=self.home_id, away_id=self.away_id, highlight_id=self.highlight_id)

    def set_ids(self):
        for item in self.content:
            if str(item["contentType"]["name"]).upper() == "FULL GAME" and len(item["clientContentMetadata"]):
                broadcast = str(item["clientContentMetadata"][0]["name"]).upper()
                if broadcast == "HOME" or broadcast == "NATIONAL":
                    self.home_id = str(item["id"])
                elif broadcast == "AWAY":
                    self.away_id = str(item["id"])
            elif str(item["contentType"]["name"]).upper() == "HIGHLIGHTS":
                self.highlight_id = str(item["id"])