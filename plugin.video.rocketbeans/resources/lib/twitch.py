# -*- coding: utf-8 -*-
import time
from json import loads
from urllib.request import Request, urlopen
from resources.data.config import TWITCH_CLIENT_ID

from base64 import b64decode

class TwitchStream:
    def __init__(self, user_login):
        payload = loads(
            urlopen(
                Request(
                    "https://api.twitch.tv/helix/streams?user_login=%s" %user_login, 
                    headers = { "Client-ID": b64decode(TWITCH_CLIENT_ID).decode("utf-8") }
                )
            ).read()
        )["data"]
        
        if len(payload) > 0:
            self.url = "plugin://plugin.video.twitch/?mode=play&channel_id=%s" %payload[0]["user_id"]
            self.thumbnail = payload[0]["thumbnail_url"].format(
                height="270", width="480") + '#%s' % time.localtime()
            self.title = payload[0]["title"]
        else:
            raise Exception("Failed to fetch stream information from Twitch.")
