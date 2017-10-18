import xbmc,xbmcaddon
import json
import os,binascii

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

__addon_name__ = "NBA League Pass"
__addon_id__ = "plugin.video.nba"

# global variables
settings = xbmcaddon.Addon( id=__addon_id__)
scores = settings.getSetting( id="scores")
debug = settings.getSetting( id="debug")
use_local_timezone = settings.getSetting( id="local_timezone") == "0"
useragent = "iTunes-AppleTV/4.1"

# map the quality_id to a video height
# Ex: 720p
quality_id = settings.getSetting( id="quality_id")
video_heights_per_quality = [-1, 72060, 720, 540, 432, 360]
target_video_height = video_heights_per_quality[int(quality_id)]

cache = StorageServer.StorageServer("nbaleaguepass", 1)
cache.table_name = "nbaleaguepass"

# Delete the video urls cached if the video quality setting has changed
if cache.get("target_video_height") != str(target_video_height):
    cache.delete("video_%")
    cache.set("target_video_height", str(target_video_height))
    print "deleting video url cache"

cookies = ''
player_id = binascii.b2a_hex(os.urandom(16))
addon_dir = xbmc.translatePath( settings.getAddonInfo('path') ).decode('utf-8')

# the default fanart image
fanart_image = os.path.join(addon_dir, "fanart.jpg")
setting_fanart_image = settings.getSetting("fanart_image")
if setting_fanart_image != '':
    fanart_image = setting_fanart_image

try:
    config_path = os.path.join(addon_dir, "config", "config.json")
    config_json = open(config_path).read()
    config = json.loads(config_json)
except:
    root_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(root_path, "..", "config", "config.json")
    config_json = open(config_path).read()
    config = json.loads(config_json)
    pass

fav_team = None
