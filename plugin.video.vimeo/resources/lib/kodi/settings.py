class Settings:

    VIDEO_FORMAT = {
        "HLS (Adaptive)": "hls:default",
        "2160p": "progressive:2160p",
        "1080p": "progressive:1080p",
        "720p": "progressive:720p",
        "540p": "progressive:540p",
        "360p": "progressive:360p",
        "240p": "progressive:240p"
    }

    VIDEO_CODEC = {
        "AV1": "AV1",
        "H.264": "H264",
    }

    def __init__(self, addon):
        self.addon = addon

    def get(self, id):
        return self.addon.getSetting(id)

    def set(self, id, value):
        return self.addon.setSetting(id, value)
