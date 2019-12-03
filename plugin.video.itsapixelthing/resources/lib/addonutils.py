# -*- coding: utf-8 -*-
import re
from resources.lib.kodiutils import kodi_json_request

def return_duration_as_seconds(string):
    try:
        totalseconds = 0
        hours = re.findall(r'(\d+)H',string)
        minutes = re.findall(r'(\d+)M',string)
        seconds = re.findall(r'(\d+)S',string)
        if hours:
            totalseconds += 3600*int(hours[0])
        if minutes:
            totalseconds += 60*int(minutes[0])
        if seconds:
            totalseconds += int(seconds[0])
        return str(totalseconds)
    except IndexError:
        return '0'

def is_youtube_addon_installed():
    result = kodi_json_request(
        {
            "jsonrpc": "2.0",
            "method": "Addons.GetAddonDetails",
            "params": {
                "addonid": "plugin.video.youtube",
                "properties": ["installed"]
            },
            "id": 11
        }
    )
    return bool(result and result["addon"]["installed"])
