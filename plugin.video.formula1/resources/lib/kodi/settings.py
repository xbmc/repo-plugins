class Settings:

    VIDEO_FORMAT = {
        "HLS (Adaptive)": "m3u8",
        "1080p": "mp4:1080",
        "720p": "mp4:720",
        "360p": "mp4:360",
    }

    def __init__(self, addon):
        self.addon = addon

    def get(self, id):
        return self.addon.getSetting(id)

    def set(self, id, value):
        return self.addon.setSetting(id, value)
