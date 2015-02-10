import urllib2
import json

def get_tv_stations():
    url = "http://www.rai.tv/dl/RaiTV/iphone/android/smartphone/advertising_config.html"
    response = json.load(urllib2.urlopen(url))
    channels = response["Channels"]
    
    for channel in channels:
        channel["icon"] = channel["icon"].replace(".png", "-big.png")
        
        # Force replay availability for Rai YoYo
        if channel["name"] == "Rai Yoyo":
            channel["hasReplay"] = "YES"
    
    return channels
    
def get_radio_station():
    url = "http://www.rai.tv/dl/RadioRai/config_json.html"
    response = json.load(urllib2.urlopen(url))
    return response["canali"]

